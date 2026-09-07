# IM link access request

## Goal

Let a person who starts from an IM bot link complete registration, request access to
the bot's workspace, and use the bot once a workspace administrator approves them.

## Context

An IM `/link <email>` URL carries the IM sender, bot account, workspace, and claimed
email in a signed token. Confirmation already verifies that the logged-in email matches
the claimed email and that the user belongs to the target workspace. A user without that
membership receives `not_member` with no next step. Registration and email verification
also route users with no workspace to ordinary onboarding, which creates a new workspace
instead of returning to the bot link.

The platform email-match check remains the security boundary for forwarded links. A
forwarded URL can only be confirmed by a session for the email in its signed claims.

## Approaches considered

1. Tell users to ask an administrator for an organization invite. This needs no new data
   model, but leaves the IM link unfinished and makes administrators match users to bots
   manually.
2. Let a valid company email join automatically. This is smooth but changes access policy
   for every workspace and cannot be safe without a configured domain policy.
3. Create an IM-link access request for the target workspace and let its administrators
   approve it. This preserves the existing membership gate, gives the user one action,
   and lets approval resume the IM link. This is the chosen approach.

## Design

### Link confirmation

The IM link page continues to submit the signed link token after authentication. A member
is linked immediately. A non-member sees one action: `申请加入`.

The registration and OTP routes preserve `/im-link?token=...` as their safe return URL.
They do not redirect this flow to onboarding merely because the new user has no workspace.
The registration form pre-fills the email in the token and prevents changing it, so a
registration cannot complete with an email that the link confirmation would reject.

### Access requests

`POST /api/v1/im/link/access-requests` accepts a valid signed IM link token from an
authenticated user. It repeats the existing email-match and account checks, and creates
or reuses one pending request for `(workspace, user, account, IM sender)`. It does not
grant any access itself.

An access-request row records the target organization and workspace, the requesting user,
the IM account and sender, the originating chat when available, and its `pending`,
`approved`, or `rejected` state. It stores the platform claim needed to finish the link
after approval. Duplicate submissions return the existing pending state.

The signed link lifetime is extended to 24 hours so registration and email verification
can finish without a user needing to issue `/link` again. The email-match check is kept.

### Administrator approval

Workspace administrators see pending requests in the existing workspace Members settings
tab. Approving a request grants the requester organization role `member` if needed, then
workspace role `member`, marks the request approved, and upserts the IM identity link.
The approval path is workspace-scoped; it remains separate from organization-admin routes.

Rejecting a request records that result without changing membership or identity links.
The requester can submit a new request after rejection.

### Feedback

The browser shows only three outcomes: request access, waiting for approval, or linked.
When approval completes the user can send the next IM message as the linked CubePlex user.
The existing Feishu success reply is reused when the original link has a Feishu chat ID;
other connectors keep their current behavior.

## Out of scope

- Domain-based automatic workspace admission.
- Changing automatic platform-email identity resolution.
- A general-purpose organization or workspace self-service request system outside IM link.
- Adding new notifications for IM connectors that do not already support link-success
  feedback.

## Success criteria

- A new user can register and verify the email from an IM link, then return to that link.
- A matching user without workspace access can submit exactly one pending request.
- A workspace administrator can approve or reject the request from Members settings.
- Approval grants the correct organization and workspace memberships and creates the IM
  identity link.
- A different logged-in email cannot submit or confirm the link.
