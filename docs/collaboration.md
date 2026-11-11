# Pew Mail Collaboration Documentation

## Overview
Pew Mail supports team collaboration through organization invitations, email comments, activity tracking, and conflict prevention.

## Organization Invitations

### Inviting Members
Organization owners and admins can invite new members by email address:
- Assign organization roles (Owner, Admin, Editor, Reviewer, Viewer)
- Generate secure, time-limited invitation tokens
- Track invitation status (Pending, Accepted, Expired, Revoked)

### Accepting Invitations
Users can accept invitations through email links or directly in the application.

### Managing Invitations
Inviters can:
- Revoke pending invitations
- Resend invitations
- View invitation status

## Email Collaboration

### Collaborator Information
Each email displays:
- Creator information
- Last edited by and timestamp
- Current collaborators

### Activity Tracking
Meaningful activity events are recorded for:
- Email creation
- Edits and updates
- Comments and replies
- Status changes
- Review actions

An activity panel displays recent events for each email.

## Comments and Review Threads

### Comment Types
Two types of comments are supported:
- **General email comments** - Apply to the entire email
- **Section-specific comments** - Attached to specific email sections using stable IDs

### Threaded Replies
Comments support threaded discussions with:
- Nested replies
- Author and timestamp tracking
- Resolution status (Active, Resolved, Deleted)

### Comment Management
Users can:
- Add and reply to comments
- Edit their own comments
- Resolve and reopen threads
- Delete comments where permitted

Deleted sections preserve comment history with appropriate indicators.

## Conflict Prevention

### Optimistic Concurrency Control
Pew Mail implements optimistic concurrency control to prevent:
- Silent overwrites of newer changes
- Loss of user work

When a user attempts to save an outdated version:
- A clear conflict response is returned
- Sufficient information is provided for frontend handling
- User's unsaved content is preserved where possible

The existing email versioning system supports this functionality.

## Notifications

### Notification Types
The system generates notifications for:
- Organization invitations
- Comments and replies
- Review requests
- Approval or rejection
- Other collaboration events

### Notification Management
Notifications support:
- Read/unread status tracking
- Manual archiving
- Filtering by type

Email notifications are minimized to reduce noise.

## Permissions and Security

### Role-Based Access
Collaboration features respect the existing organization role system:
- Owners and Admins have broad access
- Editors can contribute content
- Reviewers can approve content
- Viewers have read-only access

### Data Protection
- Comment access is restricted by organization membership
- Private user information is not unnecessarily exposed
- All collaboration operations are logged for audit purposes

## Implementation Details

### Data Models
Key collaboration models include:
- `OrganizationInvitation` - Manages invitation lifecycle
- `EmailComment` - Top-level email comments
- `EmailCommentReply` - Comment replies
- `ActivityEvent` - Records meaningful actions
- `Notification` - User notifications

### APIs
Collaboration features are exposed through:
- Organization invitation endpoints
- Email comment endpoints
- Activity event endpoints
- Notification endpoints

All APIs enforce tenant isolation and appropriate permissions.