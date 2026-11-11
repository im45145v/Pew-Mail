# Pew Mail — Development Guide

## Getting Started

### Prerequisites
- Python 3.15+
- Node.js 26+
- Docker and Docker Compose
- Git

### Initial Setup
1. Clone the repository
2. Install frontend dependencies:
   ```
   cd frontend
   npm install
   ```
3. Install backend dependencies:
   ```
   cd backend
   pip install -r requirements.txt
   ```
4. Start Docker services:
   ```
   docker-compose up -d
   ```
5. Run database migrations:
   ```
   cd backend
   alembic upgrade head
   ```

### Running the Application
1. Start the backend:
   ```
   cd backend
   uvicorn app.main:app --reload
   ```
2. Start the frontend:
   ```
   cd frontend
   npm run dev
   ```
3. Access the application at `http://localhost:5173`

## Development Workflow

### Branch Strategy
- `main` - Production-ready code
- `develop` - Integration branch for ongoing work
- Feature branches - Individual feature development (`feature/[feature-name]`)
- Release branches - Preparation for releases (`release/[version]`)
- Hotfix branches - Urgent production fixes (`hotfix/[issue]`)

### Commit Guidelines
- Use conventional commits format
- Keep commits focused and atomic
- Reference issue numbers when applicable
- Example: `feat(auth): add organization switcher (#123)`

### Code Review Process
1. Create a pull request from feature branch to `develop`
2. Ensure all tests pass
3. Request review from at least one team member
4. Address feedback before merging
5. Squash merge to maintain clean history

## Project Structure

### Monorepo Organization
```
pew-mail/
├── frontend/          # React application
├── backend/           # FastAPI application
├── email_templates/   # Shared email templates
├── ai_skills/         # AI skill modules
├── docs/              # Documentation
├── scripts/           # Utility scripts
├── docker-compose.yml # Development infrastructure
└── .env.example       # Environment configuration template
```

## Backend Development

### Directory Structure
```
backend/
├── app/
│   ├── api/           # API route definitions
│   ├── core/          # Core configuration and utilities
│   ├── auth/          # Authentication system
│   ├── users/         # User management
│   ├── organizations/ # Organization management
│   ├── projects/      # Project management
│   ├── brands/        # Brand management
│   ├── emails/        # Email document management
│   ├── ai/            # AI integration
│   ├── email_engine/  # Email processing
│   ├── rendering/     # Template rendering
│   ├── validation/    # Validation services
│   ├── staging/       # Staging management
│   ├── delivery/      # Email delivery
│   ├── contacts/      # Contact management
│   ├── versioning/    # Version control
│   ├── integrations/  # Third-party integrations
│   └── database/      # Database models and connections
├── alembic/           # Database migrations
├── tests/             # Test suite
└── requirements.txt   # Python dependencies
```

### API Development
1. Define Pydantic models for requests/responses
2. Implement service layer business logic
3. Create API routes in appropriate modules
4. Add authentication/authorization as needed
5. Write unit tests for new functionality

### Database Changes
1. Create new migration:
   ```
   alembic revision -m "description of change"
   ```
2. Edit generated migration file to define changes
3. Apply migration locally:
   ```
   alembic upgrade head
   ```
4. Test migration with clean database

### New Models in Milestone 7
Milestone 7 introduces several new model categories:
- **Template Models**: Enhanced email templates with versioning and scopes
- **Component Models**: Reusable email components and design tokens
- **Collaboration Models**: Comments, activity events, and notifications
- **Campaign Models**: Campaign organization and email grouping
- **Analytics Models**: Provider event tracking and email analytics

When working with these models, ensure:
- Proper foreign key relationships
- Organization-level data isolation
- Appropriate indexing for performance
- Consistent naming conventions

## Frontend Development

### Directory Structure
```
frontend/
├── src/
│   ├── app/           # Main application component
│   ├── components/    # Shared UI components
│   ├── layouts/       # Page layouts
│   ├── pages/         # Top-level page components
│   ├── features/      # Feature-specific modules
│   ├── hooks/         # Custom React hooks
│   ├── services/      # API service clients
│   ├── types/         # TypeScript type definitions
│   └── utils/         # Utility functions
├── public/            # Static assets
└── package.json       # Dependencies and scripts
```

### Component Development
1. Create new components in appropriate feature directories
2. Use TypeScript for type safety
3. Follow existing styling patterns with Tailwind CSS
4. Implement proper error handling
5. Write unit tests for complex components

### State Management
1. Use TanStack Query for server state
2. Use React context for global client state
3. Keep state as localized as possible
4. Prefer derived state over duplicated state

## Testing

### Backend Testing
```
cd backend
pytest                      # Run all tests
pytest tests/test_auth.py   # Run specific test file
pytest -v                   # Verbose output
pytest --cov                # Coverage report
```

Test types:
- Unit tests for services and utilities
- Integration tests for API endpoints
- Database tests for model operations
- End-to-end tests for critical workflows

### Frontend Testing
```
cd frontend
npm run test            # Run all tests
npm run test:watch      # Watch mode
npm run test:coverage   # Coverage report
```

Test types:
- Unit tests for components and utilities
- Integration tests for complex features
- End-to-end tests with Playwright

### Test Data Management
- Use factories for consistent test data
- Clean up database between tests
- Mock external services in unit tests
- Use realistic test scenarios

## AI Development

### Skill Creation
1. Define skill interface in `ai_skills/`
2. Implement provider-agnostic logic
3. Add tests with mocked AI responses
4. Document usage and parameters
5. Version control skill definitions

### Prompt Engineering
1. Externalize prompts to separate files
2. Use template variables for dynamic content
3. Document prompt iteration history
4. Test with diverse inputs
5. Monitor output quality and biases

## Docker Development

### Services
- `postgres`: Database (port 5432)
- `mailpit`: Email testing (ports 1025, 8025)

### Commands
```bash
docker-compose up -d        # Start services
docker-compose down         # Stop services
docker-compose logs postgres # View database logs
```

## Environment Configuration

### Required Variables
Copy `.env.example` to `.env` and configure:
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Cryptographic secret for sessions
- `AI_PROVIDER_URL`: AI service endpoint
- `AI_API_KEY`: AI service authentication

### Environment Separation
- Development: `.env` file
- Testing: Hardcoded test values
- Production: Environment variables

## Debugging

### Backend Debugging
1. Use logging.debug() for detailed information
2. Enable SQL query logging in development
3. Use debugger breakpoints in IDE
4. Check Docker logs for infrastructure issues

### Frontend Debugging
1. Use browser developer tools
2. Enable React DevTools
3. Check network tab for API issues
4. Use console.log() sparingly

### Common Issues
1. Database connection failures: Check Docker and credentials
2. CORS errors: Verify API configuration
3. Missing environment variables: Check .env file
4. Port conflicts: Change ports in docker-compose.yml

## Deployment

### Build Process
1. Backend: Package with dependencies
2. Frontend: Build static assets
3. Database: Apply migrations
4. Configuration: Set production environment variables

### CI/CD Pipeline
1. Pull requests: Run tests and linting
2. Main branch: Build and deploy to staging
3. Releases: Deploy to production
4. Rollbacks: Use Docker image tags

## Code Quality

### Linting
- Backend: pylint, black, isort
- Frontend: ESLint, Prettier
- Run before committing changes

### Security
- Dependency scanning regularly
- Code review for security issues
- Penetration testing periodically
- Security headers in API responses

### Performance
- Profile slow operations
- Optimize database queries
- Cache expensive computations
- Monitor resource usage

## Contributing

### Adding New Features
1. Create feature branch from `develop`
2. Implement functionality with tests
3. Update documentation as needed
4. Create pull request to `develop`

### Reporting Issues
1. Check existing issues first
2. Include reproduction steps
3. Provide environment information
4. Add screenshots/logs when relevant

### Code Standards
1. Follow existing code style
2. Write self-documenting code
3. Add comments for complex logic
4. Keep functions focused and small