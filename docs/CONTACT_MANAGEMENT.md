# Contact Management System

## Overview

The Contact Management System is part of Milestone 6 of Pew Mail, enabling organizations to manage contacts, organize recipients into groups, import CSV files, and send personalized HTML emails through the existing approved delivery workflow.

## Features

### 1. Contact Management

Organizations can manage contacts with the following attributes:
- First name
- Last name
- Full name (computed)
- Email address
- Organization/company
- Job title
- Phone number (optional)
- Custom fields
- Tags
- Notes
- Created date
- Updated date

#### Operations
- Create contact
- Edit contact
- Delete contact
- Archive contact
- Search contacts
- Filter contacts
- View contact details
- Detect duplicate email addresses (normalized for comparison)

#### Security
- Contacts are scoped to organizations
- No cross-organization contact exposure without explicit permissions

### 2. Contact Import

Organizations can import contacts from CSV files:

#### Process
1. Upload a CSV file
2. Preview the contents
3. Map CSV columns to Pew Mail fields
4. Inspect invalid records
5. Identify duplicates
6. Choose whether to skip or update existing contacts
7. Confirm the import
8. View an import summary

#### Supported Data
- Custom fields where practical
- Invalid email addresses detection
- Duplicate records detection
- Missing required fields validation
- Empty values handling
- Malformed CSV files handling
- Large imports safety

#### Import Report
- Successful records count
- Skipped records count
- Updated records count
- Failed records count
- Error details for failed records

### 3. Contact Groups

Recipients can be organized into groups:

#### Examples
- Hackathon Participants
- Sponsors
- Mentors
- Speakers
- College Students
- Newsletter Subscribers

#### Operations
- Create groups
- Rename groups
- Delete groups
- Add contacts to groups
- Remove contacts from groups
- Search groups
- View group membership
- Select groups as email recipients

#### Technical Implementation
- Many-to-many database relationship
- A contact can belong to multiple groups

### 4. Tags and Segmentation

Basic contact tagging system:

#### Examples
- Participant
- Speaker
- Sponsor
- Volunteer
- Alumni

#### Filtering Capabilities
- Tags
- Organization
- Group membership
- Custom fields
- Contact creation date

### 5. Email Personalization Engine

Safe template-variable substitution for email personalization:

#### Standard Variables
- `{{first_name}}`
- `{{last_name}}`
- `{{full_name}}`
- `{{organization}}`
- `{{job_title}}`

#### Custom Variables
- Support for custom field variables
- Example: `{{department}}`

#### Safety Features
- HTML escaping to prevent XSS
- Only approved text variables are replaced
- No executable HTML or script injection
- Explicitly supported trusted HTML content only with strict validation
- Default value support: `{{first_name | default: "there"}}`

### 6. Personalization Preview

Email Studio feature for previewing personalized emails:

#### Functionality
- Select a contact for preview
- Preview email with substituted variables
- Support for multiple sample contacts
- Clear identification of missing variables
- Configuration of fallback values

### 7. Recipient Selection

Integration with existing email workflow:

#### Selection Options
- Individual contacts
- Contact groups
- CSV-imported recipients
- Manually entered email addresses

#### Display Information
- Total recipients count
- Duplicate count
- Invalid recipients list
- Missing personalization fields
- Recipient source breakdown

#### Safety Measures
- Prevent accidental exposure of recipient email addresses
- Prefer individual messages or appropriate batch mechanisms
- No large recipient list exposure in CC

### 8. Send Preparation and Safety

Integration with existing staging, approval, and delivery workflow:

#### Pre-Delivery Steps
1. Resolve recipients
2. Validate addresses
3. Resolve personalization variables
4. Validate required fields
5. Generate recipient-specific HTML
6. Verify the output
7. Apply delivery limits
8. Require production confirmation

#### Relationship Maintenance
- Original email
- Approved version
- Recipient
- Personalized output
- Delivery record

#### Safety Features
- Content changes after approval require new version
- No bypassing of existing approval process

### 9. Contact Consent and Unsubscribe

Privacy-conscious contact management:

#### Supported Features
- Contact source tracking
- Consent status (consented, unsubscribed)
- Consent timestamp
- Consent source
- Unsubscribe status
- Suppression status

#### Compliance Features
- Unsubscribe mechanism for promotional emails
- Suppression list maintenance
- Exclusion of unsubscribed recipients
- Prevention of accidental re-addition to marketing groups
- Transactional vs promotional email distinction
- Anti-spam and privacy compliance documentation

### 10. Contact Import History

Tracking of all contact import activities:

#### Stored Information
- Import ID
- Organization
- File name
- Timestamp
- User
- Number of records
- Successful records
- Updated records
- Skipped records
- Failed records

#### Retention Policy
- Import metadata retained
- Source files not unnecessarily retained after processing
- Error report download option

## Database Schema

### Core Models

#### Contact
```python
class Contact(BaseModel):
    first_name: str
    last_name: str
    email: str  # Indexed, normalized
    organization: Optional[str]
    job_title: Optional[str]
    phone_number: Optional[str]
    organization_id: UUID  # Foreign key, indexed
    custom_fields: JSON  # Flexible storage
    tags: JSON  # Array of tags
    notes: Optional[str]
    is_archived: bool
    consent_status: Optional[str]
    consent_timestamp: Optional[DateTime]
    consent_source: Optional[str]
    unsubscribe_timestamp: Optional[DateTime]
    is_suppressed: bool
    source: Optional[str]
    import_id: Optional[UUID]  # Foreign key
```

#### ContactGroup
```python
class ContactGroup(BaseModel):
    name: str
    description: Optional[str]
    organization_id: UUID  # Foreign key, indexed
```

#### ContactGroupMembership
```python
class ContactGroupMembership(BaseModel):
    contact_id: UUID  # Foreign key
    group_id: UUID  # Foreign key
```

#### ContactImport
```python
class ContactImport(BaseModel):
    organization_id: UUID  # Foreign key
    user_id: UUID  # Foreign key
    file_name: str
    total_records: int
    successful_records: int
    updated_records: int
    skipped_records: int
    failed_records: int
    column_mapping: JSON
    error_report_path: Optional[str]
```

### Personalization Models

#### PersonalizationSchema
```python
class PersonalizationSchema(BaseModel):
    organization_id: UUID  # Foreign key
    name: str
    description: Optional[str]
    variables: JSON  # Variable definitions
```

#### RecipientSnapshot
```python
class RecipientSnapshot(BaseModel):
    staging_snapshot_id: UUID  # Foreign key
    recipient_data: JSON  # Serialized contact data
    personalization_variables: JSON  # Resolved variables
    personalized_html: Optional[str]
    personalized_plain_text: Optional[str]
```

#### PersonalizedEmail
```python
class PersonalizedEmail(BaseModel):
    recipient_snapshot_id: UUID  # Foreign key
    staging_snapshot_id: UUID  # Foreign key
    google_send_history_id: Optional[UUID]  # Foreign key
    recipient_email: str
    recipient_name: Optional[str]
    subject: str
    html_content: str
    plain_text_content: Optional[str]
    delivery_status: str  # pending, sent, failed
    delivery_error: Optional[str]
    sent_at: Optional[DateTime]
```

## API Endpoints

### Contact Management
- `POST /contacts/` - Create contact
- `GET /contacts/{contact_id}` - Get contact
- `PUT /contacts/{contact_id}` - Update contact
- `DELETE /contacts/{contact_id}` - Delete contact
- `POST /contacts/{contact_id}/archive` - Archive contact
- `POST /contacts/search` - Search contacts

### Group Management
- `POST /contacts/groups` - Create group
- `GET /contacts/groups` - List groups
- `PUT /contacts/groups/{group_id}` - Update group
- `DELETE /contacts/groups/{group_id}` - Delete group
- `POST /contacts/groups/{group_id}/members/{contact_id}` - Add contact to group
- `DELETE /contacts/groups/{group_id}/members/{contact_id}` - Remove contact from group
- `GET /contacts/groups/{group_id}/members` - Get group members

### CSV Import
- `POST /contacts/import/csv` - Import contacts from CSV
- `GET /contacts/import/history` - Get import history

### Personalization
- `POST /contacts/personalization/preview` - Preview personalization
- `POST /contacts/personalization/recipient-summary` - Get recipient summary

## Security Considerations

1. **Data Isolation**: All contact data is scoped to organizations
2. **Token Protection**: OAuth tokens are encrypted at rest
3. **Input Validation**: Strict validation of all inputs
4. **HTML Escaping**: Prevention of XSS in personalization
5. **Consent Tracking**: Comprehensive consent and unsubscribe handling
6. **Access Control**: Integration with existing user/organization permissions

## Privacy Compliance

The system includes features to help with privacy compliance:
- Consent status tracking
- Unsubscribe mechanisms
- Suppression lists
- Source tracking
- Audit trails
- Data minimization principles
- Documentation of compliance approaches

## Testing

### Backend Tests
- Contact CRUD operations
- Duplicate detection
- CSV parsing and validation
- Column mapping
- Group membership management
- Tag filtering
- Personalization substitution
- HTML escaping
- Missing variable handling
- Unsubscribe suppression
- Organization isolation

### Frontend Tests
- Contact management UI
- CSV import workflow
- Group management
- Recipient selection
- Personalization preview
- Validation warnings

### End-to-End Tests
1. Create an organization
2. Create a contact group
3. Import a CSV with 20 sample contacts
4. Map the columns
5. Resolve duplicates
6. Confirm import
7. Select the group in an email
8. Personalize the email using first name
9. Preview several contacts
10. Validate recipient data
11. Create a recipient snapshot
12. Verify that unsubscribed contacts are excluded
13. Send only through the existing test-delivery workflow

## Definition of Done

Milestone 6 is complete when:
1. Contact CRUD operations work
2. CSV imports work
3. Groups work
4. Tags work
5. Personalization works
6. Missing variables are handled safely
7. Recipient selection works
8. Suppression and consent controls work
9. Integration with staging and approval works
10. Tests pass
11. Documentation is updated