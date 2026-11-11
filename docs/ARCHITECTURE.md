# Pew Mail — Architecture Documentation

## Application Structure

Monorepo organization:
```
pew-mail/
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── features/
│   │   │   ├── dashboard/
│   │   │   ├── projects/
│   │   │   ├── editor/
│   │   │   ├── brand/
│   │   │   ├── testing/
│   │   │   ├── contacts/
│   │   │   └── settings/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── types/
│   │   └── utils/
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── auth/
│   │   ├── users/
│   │   ├── organizations/
│   │   ├── projects/
│   │   ├── brands/
│   │   ├── emails/
│   │   ├── ai/
│   │   ├── email_engine/
│   │   ├── rendering/
│   │   ├── validation/
│   │   ├── staging/
│   │   ├── delivery/
│   │   ├── contacts/
│   │   ├── versioning/
│   │   ├── integrations/
│   │   │   └── google/
│   │   ├── database/
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   └── requirements.txt
│
├── email_templates/
├── ai_skills/
├── docs/
├── scripts/
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## Technology Stack

### Frontend Architecture
- **Framework**: React with TypeScript for type safety
- **Build Tool**: Vite for fast development and building
- **Styling**: Tailwind CSS for utility-first styling
- **Components**: shadcn/ui library built on Radix UI primitives
- **Icons**: Lucide icons for consistent iconography
- **Routing**: React Router for client-side routing
- **State Management**: TanStack Query for server state management
- **Component Architecture**: Modular, reusable components organized by feature

### Backend Architecture
- **Framework**: FastAPI for high-performance Python web framework
- **Data Validation**: Pydantic for request/response validation and serialization
- **Database ORM**: SQLAlchemy for database abstraction
- **Migrations**: Alembic for database schema versioning
- **Database**: PostgreSQL for reliable data persistence
- **Architecture Layers**:
  - API Routes: HTTP endpoint definitions
  - Services: Business logic implementation
  - Repositories: Data access layer
  - Models: Database schema definitions
  - Core: Shared utilities and configuration

### Email Engine Architecture
- **Markup Language**: MJML for responsive email design
- **Document Model**: Structured email representation that compiles to MJML/HTML
- **Validation**: HTML sanitization and email client compatibility checking
- **Components**: Reusable email building blocks (headers, text, images, buttons, etc.)

### Database Design Principles
- **Identifier Strategy**: UUIDs for all entity identifiers
- **Relationships**: Properly normalized relationships with foreign keys
- **Access Control**: Organization-level data isolation
- **Versioning**: Built-in revision history for email documents
- **Extensibility**: Modular model design supporting future enhancements
- **Audit Trail**: Comprehensive activity logging for collaboration features
- **Auditing**: Comprehensive audit logging for security and compliance

## Core Components

### Authentication System
- Multi-organization membership
- Role-based access control (Owner, Admin, Editor, Reviewer, Viewer)
- Secure session management
- Future OAuth integration (Google, etc.)

### Email Document Model
Structured representation supporting:
- Headers and footers
- Text sections with rich formatting
- Images with alt text and optimization
- Interactive buttons with customizable styles
- Layout elements (dividers, columns, background sections)
- Social media links
- Custom components for extensibility

### AI Integration Framework
- Provider-agnostic design supporting any OpenAI-compatible API
- Modular skill system for specialized capabilities
- Context-aware generation using brand guidelines and project history
- Conversation management for iterative editing

### Testing Pipeline
- Automated validation checks before staging
- Snapshot-based staging for consistent test environments
- Approval workflow with immutable versions
- Idempotency protection against duplicate sends

### Delivery System
- Provider abstraction supporting multiple email services
- Secure credential management
- Sending history and tracking
- Error handling and retry mechanisms

## Security Architecture

### Data Protection
- Input validation at API boundaries
- SQL injection prevention through ORM
- XSS prevention through HTML sanitization
- CSRF protection for state-changing operations

### Authentication & Authorization
- JWT-based session tokens
- Role-based access control enforced server-side
- Organization data isolation
- Secure password handling

### Infrastructure Security
- Environment variable configuration
- Secure credential storage
- Rate limiting for abuse prevention
- Audit logging for compliance

## Deployment Architecture

### Development Environment
- Docker Compose for consistent local setup
- PostgreSQL database container
- Environment-specific configuration
- Hot reloading for frontend development

### Future Production Considerations
- Containerized deployment (Docker/Kubernetes)
- Load balancing and horizontal scaling
- CDN for asset delivery
- Database replication and backups
- Monitoring and alerting system

## Extensibility Points

### Plugin Architecture
- AI skills as modular, version-controlled components
- Email components with standardized interfaces
- Delivery providers with pluggable interfaces
- Import/export adapters for various formats

### API Design
- RESTful endpoints with consistent naming
- Versioned APIs for backward compatibility
- Comprehensive error handling with descriptive messages
- Pagination and filtering for large datasets

## Performance Considerations

### Frontend Optimization
- Code splitting by route and feature
- Asset compression and caching
- Lazy loading for non-critical components
- Efficient state management to minimize re-renders

### Backend Optimization
- Database indexing for common query patterns
- Connection pooling for database efficiency
- Caching strategies for expensive operations
- Asynchronous processing for non-blocking operations

### Email Processing
- Compiled email caching
- Parallel processing for batch operations
- Efficient MJML-to-HTML compilation
- Image optimization and CDN integration