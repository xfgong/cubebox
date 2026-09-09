"""Concurrent browser confirmations must persist one link and both succeed."""

import asyncio
import secrets

import httpx
import pytest
from fastapi import HTTPException
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from cubeplex.api.routes.v1.im_link import _ConfirmBody, create_access_request
from cubeplex.api.routes.v1.ws_members import _resolve_access_request, list_access_requests
from cubeplex.auth.context import RequestContext
from cubeplex.im.link import get_jwt_secret, sign_link_token
from cubeplex.models import Membership, OrganizationMembership, Role, User
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
        async with session_factory() as session:
            user = await session.get(User, user_id)
            assert user is not None
            requested_directly = await create_access_request(
                _ConfirmBody(token=token), user, session
            )
            assert requested_directly.status == "pending"
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
        async with session_factory() as session:
            user = await session.get(User, user_id)
            assert user is not None
            ctx = RequestContext(user, DEFAULT_ORG_ID, DEFAULT_WS_ID, Role.ADMIN)
            listed = await list_access_requests(ctx, session)
            assert [item.id for item in listed.requests] == [request.id]
            await _resolve_access_request(
                request_id=request.id, approved=True, ctx=ctx, session=session
            )
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


@pytest.mark.asyncio
async def test_access_request_rejects_bad_claims_and_allows_rejection(
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
    valid = sign_link_token(
        im_user_id="sender",
        email=DEFAULT_TEST_EMAIL,
        account_id=account_id,
        workspace_id=DEFAULT_WS_ID,
        platform="wecom",
        secret=get_jwt_secret(),
    )
    wrong_email = sign_link_token(
        im_user_id="sender",
        email="other@example.com",
        account_id=account_id,
        workspace_id=DEFAULT_WS_ID,
        platform="wecom",
        secret=get_jwt_secret(),
    )
    unknown_account = sign_link_token(
        im_user_id="sender",
        email=DEFAULT_TEST_EMAIL,
        account_id=f"imac-missing-{suffix}",
        workspace_id=DEFAULT_WS_ID,
        platform="wecom",
        secret=get_jwt_secret(),
    )
    try:
        async with session_factory() as session:
            user = await session.get(User, user_id)
            assert user is not None
            with pytest.raises(HTTPException, match="invalid_token"):
                await create_access_request(_ConfirmBody(token="bad"), user, session)
            with pytest.raises(HTTPException, match="email_mismatch"):
                await create_access_request(_ConfirmBody(token=wrong_email), user, session)
            with pytest.raises(HTTPException, match="account_not_found"):
                await create_access_request(_ConfirmBody(token=unknown_account), user, session)
            member = await create_access_request(_ConfirmBody(token=valid), user, session)
            assert member.status == "approved"
        async with session_factory() as session:
            await session.execute(delete(Membership).where(Membership.user_id == user_id))
            await session.commit()
        async with session_factory() as session:
            user = await session.get(User, user_id)
            assert user is not None
            requested = await create_access_request(_ConfirmBody(token=valid), user, session)
            assert requested.status == "pending"
            repeated = await create_access_request(_ConfirmBody(token=valid), user, session)
            assert repeated.status == "pending"
            request = (
                await session.scalars(
                    select(IMLinkAccessRequest).where(IMLinkAccessRequest.account_id == account_id)
                )
            ).one()
            session.add(Membership(user_id=user_id, workspace_id=DEFAULT_WS_ID, role="admin"))
            await session.commit()
        async with session_factory() as session:
            user = await session.get(User, user_id)
            assert user is not None
            ctx = RequestContext(user, DEFAULT_ORG_ID, DEFAULT_WS_ID, Role.ADMIN)
            await _resolve_access_request(
                request_id=request.id, approved=False, ctx=ctx, session=session
            )
        async with session_factory() as session:
            assert (
                await session.scalar(
                    select(IMLinkAccessRequest.status).where(IMLinkAccessRequest.id == request.id)
                )
                == "rejected"
            )
    finally:
        async with session_factory() as session:
            await im_cleanup(session, account_ids=[account_id], credential_ids=[credential_id])
            await session.commit()


@pytest.mark.asyncio
async def test_approval_adds_requester_to_org_and_workspace(
    async_client: httpx.AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Approving a request grants access when the requester has no memberships yet."""
    admin_id = (await async_client.get("/api/v1/auth/me")).json()["id"]
    suffix = secrets.token_hex(5)
    account_id = f"imac-{suffix}"
    credential_id = f"cred-{suffix}"
    requester = User(
        email=f"im-requester-{suffix}@example.com",
        hashed_password="not-used-by-this-test",
    )
    request_id = ""
    try:
        async with session_factory() as session:
            session.add(requester)
            await session.flush()
            await im_seed_stub_credential(
                session, credential_id=credential_id, org_id=DEFAULT_ORG_ID
            )
            await im_seed_account(
                session,
                account_id=account_id,
                org_id=DEFAULT_ORG_ID,
                ws_id=DEFAULT_WS_ID,
                user_id=admin_id,
                credential_id=credential_id,
                external_account_id=suffix,
                platform="wecom",
            )
            request = IMLinkAccessRequest(
                org_id=DEFAULT_ORG_ID,
                workspace_id=DEFAULT_WS_ID,
                account_id=account_id,
                im_user_id="requester",
                user_id=requester.id,
                platform="wecom",
            )
            session.add(request)
            await session.commit()
            request_id = request.id

        async with session_factory() as session:
            admin = await session.get(User, admin_id)
            assert admin is not None
            ctx = RequestContext(admin, DEFAULT_ORG_ID, DEFAULT_WS_ID, Role.ADMIN)
            await _resolve_access_request(
                request_id=request_id, approved=True, ctx=ctx, session=session
            )
        async with session_factory() as session:
            org_membership = await session.scalar(
                select(OrganizationMembership).where(
                    OrganizationMembership.user_id == requester.id,
                    OrganizationMembership.org_id == DEFAULT_ORG_ID,
                )
            )
            assert org_membership is not None
            assert org_membership.role == "member"
            membership = await session.scalar(
                select(Membership).where(
                    Membership.user_id == requester.id,
                    Membership.workspace_id == DEFAULT_WS_ID,
                )
            )
            assert membership is not None
            assert membership.role == "member"
            assert (
                await session.scalar(
                    select(IMIdentityLink.user_id).where(IMIdentityLink.account_id == account_id)
                )
                == requester.id
            )
    finally:
        async with session_factory() as session:
            await im_cleanup(session, account_ids=[account_id], credential_ids=[credential_id])
            await session.execute(delete(Membership).where(Membership.user_id == requester.id))
            await session.execute(
                delete(OrganizationMembership).where(OrganizationMembership.user_id == requester.id)
            )
            await session.execute(delete(User).where(User.id == requester.id))
            await session.commit()


@pytest.mark.asyncio
async def test_approval_of_unknown_access_request_returns_not_found(
    async_client: httpx.AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    user_id = (await async_client.get("/api/v1/auth/me")).json()["id"]
    async with session_factory() as session:
        user = await session.get(User, user_id)
        assert user is not None
        ctx = RequestContext(user, DEFAULT_ORG_ID, DEFAULT_WS_ID, Role.ADMIN)
        with pytest.raises(HTTPException, match="access_request_not_found"):
            await _resolve_access_request(
                request_id="ilar-missing", approved=True, ctx=ctx, session=session
            )
