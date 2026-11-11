# Pew Mail Templates Documentation

## Overview
Pew Mail templates provide reusable email designs that can be applied to create new emails quickly. Templates support categorization, versioning, and flexible sharing across organization scopes.

## Template Categories
Templates can be categorized into the following types:
- Event invitation
- Event announcement
- Newsletter
- Hackathon announcement
- Sponsorship outreach
- Partnership outreach
- Product announcement
- Welcome email
- Thank-you email
- Follow-up email
- Professional communication
- Custom

## Template Scopes
Templates support four ownership scopes:

1. **System templates** - Provided by Pew Mail, available to all organizations
2. **Organization templates** - Shared across an organization
3. **Project templates** - Available to a specific project
4. **Personal templates** - Visible only to their creator

Permissions are strictly enforced to prevent cross-organization access.

## Template Operations

### Creating Templates
Templates can be created in two ways:
- From an existing email document
- From scratch using the template editor

### Applying Templates
When applying a template to create a new email, users can choose:
- Structure and layout only
- Structure, layout, and styling
- Full template including subject and preheader

Brand compatibility is automatically checked when applying templates.

### Template Versioning
Templates support full version history with immutable snapshots. Each version stores:
- Structured document
- Metadata (name, description, category, tags)
- Subject and preheader
- Design tokens
- Author information
- Timestamp
- Change description

Restoring a previous version creates a new version rather than overwriting history.

## Template Fields
- `name` - Template name
- `description` - Template description
- `category` - One of the predefined categories
- `tags` - Array of tags for filtering
- `thumbnail_url` - Preview image URL
- `subject` - Default subject line
- `preheader` - Default preheader text
- `document` - Structured email document
- `mjml_content` - Generated MJML
- `html_content` - Compiled HTML
- `scope` - Template ownership scope
- `project_id` - Associated project (if project-scoped)
- `created_by_id` - Template creator
- `design_tokens` - Design tokens used in the template
- `is_archived` - Archive status
- `current_version_id` - Pointer to current version
- `is_starter` - Flag for starter templates

## Security Considerations
- Templates are isolated by organization
- System templates are protected from unauthorized modification
- Template operations require appropriate permissions based on scope