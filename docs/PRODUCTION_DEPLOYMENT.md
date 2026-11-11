# Pew Mail - Production Deployment Guide

This guide provides instructions for deploying Pew Mail in a production environment.

## Overview

Pew Mail can be deployed in various cloud environments including AWS, Google Cloud, Azure, and on-premises infrastructure. The application consists of:

1. Frontend (React/Vite application)
2. Backend (FastAPI application)
3. PostgreSQL database
4. Optional Redis for background jobs
5. Object storage (S3-compatible or local)

## Deployment Architecture Options

### Option 1: Containerized Deployment (Recommended)

Deploy using Docker Compose or Kubernetes with the provided Dockerfiles.

#### Components:
- Frontend container (Nginx)
- Backend container (FastAPI)
- PostgreSQL container (or managed service)
- Redis container (optional, for background jobs)

### Option 2: Traditional Deployment

Deploy each service separately on VMs or bare metal servers.

### Option 3: Cloud-Native Deployment

Deploy on managed services:
- Frontend: AWS S3 + CloudFront, Google Cloud Storage, Vercel, Netlify
- Backend: AWS ECS/EKS, Google Cloud Run, Azure Container Instances
- Database: AWS RDS, Google Cloud SQL, Azure Database
- Background jobs: AWS Lambda, Google Cloud Functions, Azure Functions

## Prerequisites

1. Domain name for the application
2. SSL certificate (recommended)
3. Cloud provider account (if deploying to cloud)
4. DNS management access
5. CI/CD pipeline (recommended)

## Environment Preparation

### 1. Configure Environment Variables

Create a `.env.production` file with production values:

```bash
# Critical: Generate a secure secret key
openssl rand -hex 32

# Set environment variables
ENVIRONMENT=production
SECRET_KEY=your_generated_secure_key
DATABASE_URL=postgresql://user:password@host:port/database
AI_API_KEY=your_ai_provider_key
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
FRONTEND_URL=https://yourdomain.com
STORAGE_TYPE=s3
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_S3_BUCKET_NAME=your_bucket_name
AWS_S3_REGION=your_region
```

### 2. Set Up Database

#### Option A: Managed Database Service (Recommended)
- AWS RDS PostgreSQL
- Google Cloud SQL PostgreSQL
- Azure Database for PostgreSQL

#### Option B: Self-Hosted PostgreSQL
Ensure:
- Proper backups enabled
- Performance tuning
- Security hardening
- Monitoring and alerting

### 3. Configure Storage

#### Local Storage
For local storage, ensure:
- Sufficient disk space
- Regular backups
- Proper permissions

#### S3-Compatible Storage
Configure:
- Bucket with appropriate permissions
- CORS configuration for frontend access
- Lifecycle policies for cost optimization

### 4. Set Up SSL/TLS

Obtain SSL certificates through:
- Let's Encrypt (free)
- Commercial CA
- Cloud provider certificate management

## Deployment Steps

### 1. Build Docker Images

```bash
# Build backend
cd backend
docker build -t pewmail-backend:latest .

# Build frontend
cd ../frontend
docker build -t pewmail-frontend:latest .
```

### 2. Configure Docker Compose for Production

Use `docker-compose.prod.yml` as a template and customize for your environment.

### 3. Deploy Services

```bash
# Deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Or deploy with Kubernetes
kubectl apply -f kubernetes/
```

### 4. Run Database Migrations

```bash
# Run migrations
docker exec -it pewmail-backend alembic upgrade head
```

### 5. Configure Load Balancer/Reverse Proxy

Set up NGINX, Traefik, or cloud load balancer with:
- SSL termination
- Rate limiting
- Request buffering
- Health checks

### 6. Set Up Monitoring

Configure:
- Application logs collection
- Performance monitoring
- Uptime monitoring
- Error tracking (Sentry, etc.)
- Database monitoring

## Security Considerations

### Network Security
- Use private networks where possible
- Restrict database access to backend only
- Implement firewall rules
- Enable DDoS protection

### Application Security
- Use secure headers
- Implement CSP (Content Security Policy)
- Protect against common web vulnerabilities
- Regular security scanning

### Data Security
- Encrypt data at rest
- Use TLS for data in transit
- Regular security audits
- Compliance with relevant regulations

## Backup and Recovery

### Database Backups
- Automated daily backups
- Point-in-time recovery
- Cross-region replication
- Regular restore testing

### File Backups
- Regular snapshots of storage
- Versioning for critical files
- Off-site backup storage

### Disaster Recovery Plan
- Documented recovery procedures
- Regular DR testing
- Backup integrity verification
- Recovery time objectives (RTO)
- Recovery point objectives (RPO)

## Scaling Considerations

### Horizontal Scaling
- Multiple backend instances behind load balancer
- Read replicas for database
- CDN for static assets
- Auto-scaling groups

### Vertical Scaling
- Increase instance sizes
- Database scaling
- Memory and CPU optimization

### Performance Optimization
- Database indexing
- Caching strategies
- Query optimization
- Asset optimization

## Monitoring and Observability

### Metrics to Monitor
- Application response times
- Error rates
- Database performance
- Resource utilization
- AI usage quotas
- Email delivery metrics

### Alerting
- Critical alerts (high priority)
- Warning alerts (medium priority)
- Info alerts (low priority)
- Escalation procedures

## Maintenance Procedures

### Regular Maintenance Tasks
- Log rotation
- Database vacuum/analyze
- Security patching
- Certificate renewal
- Backup verification

### Version Updates
- Blue-green deployment strategy
- Rollback procedures
- Compatibility testing
- Zero-downtime deployments

## Troubleshooting Common Issues

### Deployment Failures
- Check container logs
- Verify environment variables
- Confirm network connectivity
- Validate resource limits

### Performance Issues
- Profile application performance
- Check database queries
- Monitor resource usage
- Analyze slow requests

### Security Incidents
- Isolate affected systems
- Preserve evidence
- Notify stakeholders
- Apply security patches

## CI/CD Integration

### Continuous Integration
- Automated testing
- Security scanning
- Code quality checks
- Dependency scanning

### Continuous Deployment
- Automated deployments
- Canary deployments
- Rollback mechanisms
- Environment promotion

## Cost Optimization

### Infrastructure Costs
- Right-size instances
- Use spot/preemptible instances where appropriate
- Optimize storage usage
- Implement auto-scaling

### Operational Costs
- Automate routine tasks
- Minimize manual interventions
- Optimize monitoring costs
- Efficient resource utilization

## Support and Maintenance

### Documentation
- Keep documentation updated
- Maintain runbooks
- Document customizations
- Track configuration changes

### Training
- Train operations team
- Document procedures
- Regular knowledge refresh
- Incident response training

## Conclusion

This deployment guide provides a comprehensive approach to deploying Pew Mail in production. Follow security best practices, implement proper monitoring, and regularly review and update your deployment procedures.

Remember to:
1. Test thoroughly in staging before production
2. Implement proper backup and recovery procedures
3. Monitor application performance and security
4. Plan for scaling as your user base grows
5. Keep all components updated with security patches