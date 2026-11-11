# Pew Mail — Product Specification

## Product Overview

### Product Name
Pew Mail

### Product Category
AI-powered HTML Email Design, Management and Delivery Studio

### Product Tagline
Create. Launch. Connect.

### Core Concept
Pew Mail allows individuals, student organizations, committees, communities and small businesses to create beautiful, professional HTML emails without knowing HTML, CSS or email development.

Users can describe what they want in natural language. An AI agent called **PewPew** assists with understanding the purpose of the email, generating email content, creating attractive email layouts, applying brand guidelines, following design rules and editing existing emails through conversational instructions.

The application provides a complete workflow:
Create → Design → Edit → Validate → Stage → Test → Approve → Send → Archive

The user should never be required to interact with Python, HTML, MJML, Google Apps Script or APIs directly to perform normal operations. Advanced users may optionally access the underlying source code.

### Product Philosophy
1. AI-first, but user-controlled
2. Design quality matters as much as functionality
3. Every organization should have reusable brand memory
4. Every email should have a revision history
5. No email should accidentally reach production recipients
6. Testing must happen before production delivery
7. The system should support multiple organizations and connected accounts
8. Keep the architecture modular and extensible

## Target Users
Initially optimize for:
- College committees
- Student organizations
- Hackathon organizers
- Developer communities
- Event organizers
- Small businesses
- Individuals who frequently send professional emails

Typical use cases:
- Hackathon announcements
- Event invitations
- Registration confirmations
- Sponsorship outreach
- Newsletters
- Speaker invitations
- Community updates
- Student announcements
- Promotional emails

Avoid turning this into a complicated enterprise marketing automation platform in the first release.

## Core Application Modules

### A. Authentication and Accounts
Implement an account architecture that supports multiple organizations where a user can belong to multiple organizations.

Each organization should have:
- Members
- Projects
- Brand guidelines
- Email templates
- Connected email accounts
- Contacts
- Email history

Roles to implement:
- Owner
- Admin
- Editor
- Reviewer
- Viewer

Permissions must be enforced in the backend, not just in the frontend.

### B. Dashboard
Dashboard features:
- Recent projects
- Recent emails
- Draft emails
- Emails awaiting approval
- Recently sent emails
- Connected Google accounts
- Quick create action

Creating an email should be the primary action.

### C. Projects
Users can create separate projects like:
- Annual Tech Fest 2027
- Hackathon announcements
- Monthly newsletter
- Sponsor outreach
- Community updates

Each project should have:
- Description
- Brand configuration
- Instructions
- Email collection
- Reusable components
- AI context
- Memory of previous work

### D. Brand Studio
Organizations should be able to save brand identity information including:
- Brand name
- Logo
- Primary color
- Secondary color
- Accent color
- Background color
- Typography preferences
- Writing tone
- Preferred email layout
- Design guidelines
- Footer information
- Social links
- Uploaded assets

AI should use active project's brand guidelines when generating or editing emails.

### E. AI Agent — PewPew
PewPew can:
1. Understand natural-language email briefs
2. Generate email structures
3. Generate content
4. Choose appropriate layouts
5. Apply brand guidelines
6. Modify individual sections
7. Rewrite text
8. Suggest improvements
9. Generate MJML through structured document representations
10. Explain design decisions
11. Preserve existing content unless instructed otherwise

AI architecture principles:
- Separate responsibilities for intent understanding, content generation, design planning, brand application, document generation, compilation, validation, and revision descriptions
- Modular skill architecture with reusable, version-controlled and documented skills

### F. Email Editor
Three modes:
1. AI Chat - Conversational interface with PewPew
2. Visual Editor - Select and modify email sections with text editing, images, buttons, colors, spacing, section ordering, backgrounds, layout options
3. Source View - Inspect generated MJML and HTML with warnings about source edits affecting structured editing

### G. Email Versioning
Every meaningful saved change creates a revision storing:
- Version ID
- Parent version
- Structured email document
- Generated MJML
- Compiled HTML snapshot
- Author
- Timestamp
- Change description
- Testing status
- Approval status

Users can view previous versions, compare versions, restore versions, duplicate versions, and identify approved versions. Approved versions must be immutable.

### H. Email Testing Lab and Staging
Workflow stages:
DRAFT → GENERATED → EDITING → VALIDATION → STAGING → TEST SEND → REVIEW → APPROVED → PRODUCTION SEND → ARCHIVED

Validation checks:
- HTML validity
- MJML compilation
- Broken links
- Missing image sources
- Missing alt text
- Missing subject line
- Empty buttons
- Unresolved template placeholders
- Responsive layout issues
- Unsafe or unsupported markup

Features:
- Staged email snapshots
- Test recipient management
- Test sending with clear identification
- Final approval screen
- Duplicate-send protection with idempotency keys

### I. Google Gmail Integration
Using Gmail API with:
- OAuth 2.0 authorization
- Secure token storage and refresh
- Gmail draft creation
- HTML email sending
- Sending history
- Error handling
- Account disconnection
- Delivery provider interface for future providers (Amazon SES, Postmark, Mailgun, SendGrid)

Security requirements:
- No Google passwords
- No OAuth tokens in frontend
- Encrypted refresh tokens
- Minimum OAuth scopes
- Revoked token handling
- No sending without approval

### J. Contact Management
Support:
- Manual contact entry
- CSV imports
- Contact groups
- Recipient selection
- Email address validation
- Duplicate detection
- Personalization fields ({{first_name}}, {{organization}}, {{event_name}})

Safe template-variable substitution without complex CRM features.

### K. Advanced Templates
Template library with:
- Categorized templates (Event invitation, Newsletter, Welcome email, etc.)
- Template ownership scopes (System, Organization, Project, Personal)
- Template versioning with immutable snapshots
- Rich metadata (tags, thumbnails, subject, preheader)
- Design token integration
- Template application with selective inheritance

### L. Reusable Design Components
Component library with:
- Pre-built email sections (headers, footers, CTAs, etc.)
- Component versioning
- Scope-based sharing
- Easy insertion into emails
- Independent modification after insertion

### M. Team Collaboration
Enhanced collaboration features:
- Organization invitations with role assignment
- Email comments and threaded replies
- Section-specific commenting
- Activity tracking and audit logs
- Notification system
- Conflict prevention through optimistic concurrency control

### N. Campaign Organization
Campaign management:
- Group related emails
- Campaign status tracking
- Campaign analytics
- Email association management

### O. Analytics and Reporting
Data-driven insights:
- Delivery pipeline tracking (Requested, Accepted, Delivered, etc.)
- Provider event ingestion architecture
- Campaign and email-level metrics
- Privacy-respecting tracking options
- Extensible provider integration

## Technology Stack

### Frontend
- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui component library
- Lucide icons
- React Router
- TanStack Query

### Backend
- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic migrations
- PostgreSQL

Clear separation between API routes, services, repositories, database models and business logic.

### Email Engine
- MJML for responsive email markup
- HTML compilation
- Structured email document representation
- HTML sanitization and validation
- Reusable email components

Structured representation supports headers, text sections, images, buttons, dividers, columns, background sections, footers, social links, and custom components.

### Database
PostgreSQL with migrations and properly designed relationships.

### Storage
Storage abstraction for uploaded images, logos and generated assets with local filesystem storage during development and S3-compatible option later.

### AI Integration
Provider-independent AI architecture with OpenAI-compatible provider interface, environment variables for configuration, and separate services and skills.

### Local Development
Docker Compose for PostgreSQL and infrastructure with documented commands for running the entire application locally.