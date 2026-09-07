# IM link access request

**Goal:** Resume an IM identity link through registration and a workspace access request.

**Architecture:** A workspace-scoped access-request record keeps the IM identity context
after a matching authenticated user asks to join. IM-link endpoints create that record;
the existing workspace Members surface lets an administrator approve it. Approval grants
the memberships and writes the identity link in one transaction.

**Tech stack:** FastAPI, SQLModel/Alembic, Next.js, React, `@cubeplex/core` API client.

## 1. Persist and expose IM-link access requests

**Files:** Add an access-request model and public-ID prefix; export it from model exports.
Add a generated Alembic migration. Extend the IM-link route and core IM API client.

**Interfaces:**

- `POST /api/v1/im/link/access-requests { token }` returns `pending` or `approved` state.
- The request holds target org/workspace, requester, IM account/sender, platform/chat data,
  and a status.

**Core logic:** Validate the signed token, current email, and account as confirmation does.
Reuse an existing pending request for the same user and IM sender; otherwise create one.
The user cannot choose the workspace or another IM identity.

**Tests:** E2E tests prove a matching non-member can create one request and a mismatched
email cannot create it.

## 2. Approve or reject in workspace Members settings

**Files:** Extend the workspace-member route and schemas; add core members API functions;
add a small pending-request section to `MembersPanel` and translations.

**Interfaces:** Workspace-admin-only list, approve, and reject endpoints under
`/api/v1/ws/{workspace_id}/members/access-requests`.

**Core logic:** Approval first ensures organization membership as `member`, then grants
workspace membership as `member`, upserts the request's IM identity link, and records the
approved state. Rejection only changes status. Both assert the request belongs to the URL
workspace.

**Tests:** E2E tests cover approval's membership/link invariant, rejection, and cross-
workspace isolation.

## 3. Resume authentication and display the minimal user flow

**Files:** Update `ImLinkPage`, registration and OTP routing, auth forms/pages as needed,
and IM-link translations and component tests.

**Interfaces:** `ImLinkPage` consumes the new request endpoint and renders the request,
waiting, or success state.

**Core logic:** Keep an IM-link `next` URL through login, registration, and OTP. Identify
that path centrally so no-workspace users return to it instead of onboarding. Bind the
registration email to the link's claimed email before creating the account.

**Tests:** Component tests cover non-member request and pending states; E2E covers the
new-user registration return path and direct member confirmation.

## 4. Verify and hand off

**Files:** Update the existing IM user documentation page if it describes manual linking.

**Tests:** Run focused backend E2E, core/frontend tests, and the relevant build/type checks.
Run the normal pre-push hook on code push.
