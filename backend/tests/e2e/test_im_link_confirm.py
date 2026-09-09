"""Concurrent browser confirmations must persist one link and both succeed."""

import asyncio
import secrets

import httpx
import pytest
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from cubeplex.im.link import get_jwt_secret, sign_link_token
from cubeplex.models import Membership, OrganizationMembership
from cubeplex.models.im_connector import IMIdentityLink, IMLinkAccessRequest
from tests.e2e.conftest import DEFAULT_ORG_ID, DEFAULT_TEST_EMAIL, DEFAULT_WS_ID
from tests.e2e.im_fixtures import im_cleanup, im_seed_account, im_seed_stub_credential


@pytest.mark.asyncio
async def test_concurrent_confirmations_and_reopen_succeed(
    async_client: httpx.AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    user_id = (await async_client.get("/api/v1/auth/me")).json()["id"]
    suffix = secrets.token_hex(5)
    account_id = f"imac-{suffix}"
    credential_id = f"cred-{suffix}"
    async with session_factory() as session:
        await im_seed_stub_credential(session, credential_id=credential_id, org_id=DEFAULT_ORG_ID)
        await im_seed_account(
            session,
            account_id=account_id,
            org_id=DEFAULT_ORG_ID,
            ws_id=DEFAULT_WS_ID,
            user_id=user_id,
            credential_id=credential_id,
            external_account_id=suffix,
            platform="wecom",
        )
        await session.commit()

    token = sign_link_token(
        im_user_id="wecom-sender",
        email=DEFAULT_TEST_EMAIL,
        account_id=account_id,
        workspace_id=DEFAULT_WS_ID,
        platform="wecom",
        secret=get_jwt_secret(),
    )
    try:
        async with asyncio.timeout(15), session_factory() as blocker:
            # Let both requests read the empty mapping before either can insert.
            await blocker.execute(text("LOCK TABLE im_identity_links IN SHARE MODE"))
            async with asyncio.TaskGroup() as group:
                requests = [
                    group.create_task(
                        async_client.post("/api/v1/im/link/confirm", json={"token": token})
                    )
                    for _ in range(2)
                ]
                try:
                    async with session_factory() as observer:
                        while True:
                            waiting = await observer.scalar(
                                text(
                                    "SELECT count(*) FROM pg_stat_activity "
                                    "WHERE datname = current_database() "
                                    "AND wait_event_type = 'Lock' "
                                    "AND query ILIKE 'INSERT INTO im_identity_links%'"
                                )
                            )
                            if waiting == 2:
                                break
                            await observer.rollback()
                            await asyncio.sleep(0.01)
                finally:
                    await blocker.rollback()
            responses = [task.result() for task in requests]
        assert [r.status_code for r in responses] == [200, 200], [r.text for r in responses]
        reopened = await async_client.post("/api/v1/im/link/confirm", json={"token": token})
        assert reopened.status_code == 200, reopened.text
        assert reopened.json()["ok"] is True
        async with session_factory() as session:
            links = (
                await session.scalars(
                    select(IMIdentityLink).where(
                        IMIdentityLink.account_id == account_id,  # type: ignore[arg-type]
                    )
                )
            ).all()
            assert len(links) == 1
            assert links[0].user_id == user_id
    finally:
        async with session_factory() as session:
            await im_cleanup(session, account_ids=[account_id], credential_ids=[credential_id])
            await session.commit()


@pytest.mark.asyncio
async def test_access_request_approval_grants_membership_and_links_identity(
    async_client: httpx.AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    user_id = (await async_client.get("/api/v1/auth/me")).json()["id"]
    suffix = secrets.token_hex(5)
    account_id = f"imac-{suffix}"
    credential_id = f"cred-{suffix}"
    async with session_factory() as session:
        await im_seed_stub_credential(session, credential_id=credential_id, org_id=DEFAULT_ORG_ID)
        await im_seed_account(
            session,
            account_id=account_id,
            org_id=DEFAULT_ORG_ID,
            ws_id=DEFAULT_WS_ID,
            user_id=user_id,
            credential_id=credential_id,
            external_account_id=suffix,
            platform="wecom",
        )
        await session.execute(delete(Membership).where(Membership.user_id == user_id))
        await session.execute(
            delete(OrganizationMembership).where(OrganizationMembership.user_id == user_id)
        )
        await session.commit()
    token = sign_link_token(
        im_user_id="wecom-sender",
        email=DEFAULT_TEST_EMAIL,
        account_id=account_id,
        workspace_id=DEFAULT_WS_ID,
        platform="wecom",
        secret=get_jwt_secret(),
    )
    try:
        requested = await async_client.post(
            "/api/v1/im/link/access-requests", json={"token": token}
        )
        assert requested.status_code == 200, requested.text
        assert requested.json()["status"] == "pending"
        repeated = await async_client.post("/api/v1/im/link/access-requests", json={"token": token})
        assert repeated.status_code == 200, repeated.text
        assert repeated.json()["status"] == "pending"
        async with session_factory() as session:
            request = (
                await session.scalars(
                    select(IMLinkAccessRequest).where(IMLinkAccessRequest.account_id == account_id)
                )
            ).one()
            session.add(
                OrganizationMembership(user_id=user_id, org_id=DEFAULT_ORG_ID, role="admin")
            )
            session.add(Membership(user_id=user_id, workspace_id=DEFAULT_WS_ID, role="admin"))
            await session.commit()
        listed = await async_client.get(f"/api/v1/ws/{DEFAULT_WS_ID}/members/access-requests")
        assert listed.status_code == 200, listed.text
        assert [item["id"] for item in listed.json()["requests"]] == [request.id]
        approved = await async_client.post(
            f"/api/v1/ws/{DEFAULT_WS_ID}/members/access-requests/{request.id}/approve"
        )
        assert approved.status_code == 204, approved.text
        async with session_factory() as session:
            link = (
                await session.scalars(
                    select(IMIdentityLink).where(IMIdentityLink.account_id == account_id)
                )
            ).one()
            assert link.user_id == user_id
    finally:
        async with session_factory() as session:
            await im_cleanup(session, account_ids=[account_id], credential_ids=[credential_id])
            await session.commit()
