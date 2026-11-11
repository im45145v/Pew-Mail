# Pew Mail - Environment Variables

This document describes all environment variables used by the Pew Mail application across different environments.

## Environment Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ENVIRONMENT` | Application environment | `development` | Yes |
| | Valid values: `development`, `staging`, `production` | | |

## Database Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `POSTGRES_DB` | PostgreSQL database name | `pewmail` | Yes |
| `POSTGRES_USER` | PostgreSQL username | `pewmail` | Yes |
| `POSTGRES_PASSWORD` | PostgreSQL password | `pewmail_dev_password` | Yes |
| `POSTGRES_PORT` | PostgreSQL port | `5432` | Yes |
| `DATABASE_URL` | Full database connection URL | `postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:${POSTGRES_PORT}/${POSTGRES_DB}` | Yes |

## Security Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | Secret key for JWT tokens and encryption | `your_secret_key_here_change_in_production` | Yes |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiration time | `30` | No |

## AI Provider Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AI_PROVIDER_URL` | AI provider API endpoint | `https://api.openai.com/v1` | Yes |
| `AI_API_KEY` | AI provider API key | - | Yes |

## Google OAuth Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | - | Yes (for Google integration) |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | - | Yes (for Google integration) |

## Application URLs

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `FRONTEND_URL` | Frontend application URL | `http://localhost:5173` | Yes |
| `BACKEND_API_URL` | Backend API URL | `http://localhost:8000` | Yes |
| `FRONTEND_API_URL` | Frontend API proxy URL | `http://localhost:5173` | Yes |

## Port Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `BACKEND_PORT` | Backend application port | `8000` | No |
| `FRONTEND_PORT` | Frontend application port | `5173` | No |
| `POSTGRES_PORT` | PostgreSQL port | `5432` | No |
| `MAILPIT_SMTP_PORT` | Mailpit SMTP port (dev only) | `1025` | No |
| `MAILPIT_HTTP_PORT` | Mailpit HTTP port (dev only) | `8025` | No |

## Logging Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LOG_LEVEL` | Application log level | `INFO` | No |
| `LOG_FORMAT` | Log format | `json` | No |
| | Valid values: `json`, `text` | | |

## Storage Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `STORAGE_TYPE` | Storage type | `local` | Yes |
| | Valid values: `local`, `s3` | | |
| `STORAGE_LOCAL_PATH` | Local storage path | `./uploads` | No |
| `AWS_ACCESS_KEY_ID` | AWS access key ID | - | Yes (for S3) |
| `AWS_SECRET_ACCESS_KEY` | AWS secret access key | - | Yes (for S3) |
| `AWS_S3_BUCKET_NAME` | S3 bucket name | - | Yes (for S3) |
| `AWS_S3_REGION` | S3 region | - | Yes (for S3) |

## Redis Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` | No |

## Billing Provider Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `BILLING_PROVIDER` | Billing provider | `mock` | Yes |
| | Valid values: `mock`, `stripe`, `razorpay` | | |
| `STRIPE_SECRET_KEY` | Stripe secret key | - | Yes (for Stripe) |
| `RAZORPAY_KEY_ID` | Razorpay key ID | - | Yes (for Razorpay) |
| `RAZORPAY_KEY_SECRET` | Razorpay key secret | - | Yes (for Razorpay) |

## AI Usage Limits

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AI_QUOTA_LIMIT` | Monthly AI quota limit (tokens) | `10000` | No |
| `AI_DAILY_RATE_LIMIT` | Daily AI request rate limit | `1000` | No |

## Organization Limits

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MAX_PROJECTS_PER_ORGANIZATION` | Max projects per organization | `10` | No |
| `MAX_TEMPLATES_PER_ORGANIZATION` | Max templates per organization | `100` | No |
| `MAX_CONTACTS_PER_ORGANIZATION` | Max contacts per organization | `10000` | No |
| `MAX_EMAIL_CAMPAIGNS_PER_ORGANIZATION` | Max email campaigns per organization | `100` | No |

## Email Sending Limits

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MAX_TEST_SENDS_PER_DAY` | Max test sends per day | `50` | No |
| `MAX_PRODUCTION_SENDS_PER_DAY` | Max production sends per day | `1000` | No |

## File Upload Limits

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MAX_FILE_SIZE_MB` | Maximum file size (MB) | `10` | No |
| `ALLOWED_FILE_TYPES` | Allowed file types (comma separated) | `.jpg,.jpeg,.png,.gif,.svg` | No |

## Background Jobs Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `WORKER_CONCURRENCY` | Worker concurrency | `4` | No |
| `WORKER_MAX_TASKS_PER_CHILD` | Max tasks per worker child | `1000` | No |

## Environment-Specific Requirements

### Development
- Database configuration with local PostgreSQL
- Mailpit for email testing
- Development secrets (can be less secure)

### Staging
- Separate database from production
- Realistic configuration close to production
- Proper secrets management

### Production
- Managed database service
- SSL/TLS configuration
- Proper secrets management
- Security-hardened configuration
- Monitoring and alerting configuration

## Security Best Practices

1. Never commit actual secrets to version control
2. Use strong, randomly generated secrets in production
3. Rotate secrets regularly
4. Use different secrets for each environment
5. Restrict access to environment files
6. Use secure permissions on environment files (600)
7. Validate all environment variables at startup
8. Fail fast on missing critical configuration