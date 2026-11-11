# Pew Mail - Backup and Recovery

This document outlines the backup and recovery procedures for Pew Mail to ensure business continuity and data protection.

## Overview

Pew Mail requires a comprehensive backup strategy that protects both application data and configuration. This document covers backup procedures for all components of the application stack.

## Backup Strategy

### Recovery Point Objective (RPO)

- **Database**: 24 hours (daily backups) with point-in-time recovery
- **File Storage**: 24 hours (daily backups)
- **Configuration**: Immediate (version controlled)

### Recovery Time Objective (RTO)

- **Full Recovery**: 4 hours
- **Partial Recovery**: 1 hour
- **Critical Data Recovery**: 30 minutes

## Database Backup

### PostgreSQL Backup Methods

#### Physical Backups (Base Backups)
- **Frequency**: Daily at 2:00 AM UTC
- **Retention**: 30 days
- **Storage**: Encrypted object storage
- **Method**: `pg_basebackup` or filesystem-level snapshots

#### Logical Backups
- **Frequency**: Daily at 1:00 AM UTC
- **Retention**: 90 days
- **Storage**: Encrypted object storage
- **Method**: `pg_dump` with custom format

#### Write-Ahead Log (WAL) Archiving
- **Frequency**: Continuous archiving
- **Retention**: 7 days
- **Storage**: Encrypted object storage
- **Purpose**: Point-in-time recovery

### Backup Implementation

#### Automated Backup Script

Create a backup script at `/opt/pewmail/scripts/backup.sh`:

```bash
#!/bin/bash
# Pew Mail Backup Script

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/pewmail"
DB_NAME="pewmail"
DB_USER="pewmail"

# Create backup directory
mkdir -p ${BACKUP_DIR}/${DATE}

# Database logical backup
pg_dump -U ${DB_USER} -d ${DB_NAME} -Fc > ${BACKUP_DIR}/${DATE}/pewmail_${DATE}.dump

# Database base backup (for PITR)
pg_basebackup -D ${BACKUP_DIR}/${DATE}/base_backup -U ${DB_USER} -F tar

# Archive WAL files
pg_archivecleanup ${BACKUP_DIR}/wal ${OLDEST_BASE_BACKUP}

# Compress and encrypt backups
tar -czf ${BACKUP_DIR}/${DATE}.tar.gz ${BACKUP_DIR}/${DATE}
gpg --encrypt --recipient admin@company.com ${BACKUP_DIR}/${DATE}.tar.gz

# Upload to cloud storage
aws s3 cp ${BACKUP_DIR}/${DATE}.tar.gz.enc s3://pewmail-backups/${DATE}.tar.gz.enc

# Cleanup local backups older than 7 days
find ${BACKUP_DIR} -name "*.tar.gz*" -mtime +7 -delete
```

#### Cron Schedule

Add to crontab:
```bash
# Daily database backup at 1:00 AM
0 1 * * * /opt/pewmail/scripts/backup.sh >> /var/log/pewmail_backup.log 2>&1
```

### Database Recovery Procedures

#### Full Database Restore

1. **Stop Application Services**:
   ```bash
   systemctl stop pewmail-frontend
   systemctl stop pewmail-backend
   ```

2. **Restore Base Backup**:
   ```bash
   # Stop PostgreSQL
   systemctl stop postgresql
   
   # Remove existing data directory
   rm -rf /var/lib/postgresql/data/*
   
   # Extract base backup
   tar -xf /backup/pewmail/20261111_010000/base_backup.tar -C /var/lib/postgresql/data/
   
   # Set permissions
   chown -R postgres:postgres /var/lib/postgresql/data/
   ```

3. **Recover to Point-in-Time**:
   ```bash
   # Create recovery.conf (PostgreSQL 11 and earlier) or recovery.signal (12+)
   echo "restore_command = 'cp /backup/wal/%f %p'" > /var/lib/postgresql/data/recovery.signal
   echo "recovery_target_time = '2026-11-11 00:00:00'" >> /var/lib/postgresql/data/postgresql.auto.conf
   
   # Start PostgreSQL
   systemctl start postgresql
   
   # Wait for recovery to complete
   # PostgreSQL will automatically remove recovery.signal when complete
   ```

4. **Restore Logical Backup** (Alternative method):
   ```bash
   # Create new database
   createdb -U postgres pewmail_restore
   
   # Restore from dump
   pg_restore -U postgres -d pewmail_restore /backup/pewmail/20261111_010000/pewmail_20261111_010000.dump
   
   # Rename databases
   psql -U postgres -c "ALTER DATABASE pewmail RENAME TO pewmail_old;"
   psql -U postgres -c "ALTER DATABASE pewmail_restore RENAME TO pewmail;"
   ```

5. **Restart Application Services**:
   ```bash
   systemctl start pewmail-backend
   systemctl start pewmail-frontend
   ```

## File Storage Backup

### Local Storage Backup

For applications using local file storage:

1. **Daily rsync Backups**:
   ```bash
   #!/bin/bash
   DATE=$(date +%Y%m%d)
   rsync -av --delete /var/www/pewmail/uploads/ /backup/pewmail/files_${DATE}/
   tar -czf /backup/pewmail/files_${DATE}.tar.gz /backup/pewmail/files_${DATE}/
   gpg --encrypt --recipient admin@company.com /backup/pewmail/files_${DATE}.tar.gz
   aws s3 cp /backup/pewmail/files_${DATE}.tar.gz.enc s3://pewmail-backups/files_${DATE}.tar.gz.enc
   ```

### S3-Compatible Storage Backup

For S3-compatible storage:

1. **Enable Versioning**:
   - Enable versioning on the bucket to protect against accidental deletion
   - Enable MFA delete for additional protection

2. **Cross-Region Replication**:
   - Configure replication to a bucket in a different region
   - Enable encryption for replicated objects

3. **Lifecycle Policies**:
   ```json
   {
     "Rules": [
       {
         "ID": "TransitionToIA",
         "Status": "Enabled",
         "Filter": {"Prefix": "backups/"},
         "Transitions": [
           {
             "Days": 30,
             "StorageClass": "STANDARD_IA"
           }
         ],
         "NoncurrentVersionTransitions": [
           {
             "NoncurrentDays": 30,
             "StorageClass": "STANDARD_IA"
           }
         ],
         "Expiration": {
           "Days": 365
         },
         "NoncurrentVersionExpiration": {
           "NoncurrentDays": 365
         }
       }
     ]
   }
   ```

## Configuration Backup

### Application Configuration

1. **Environment Variables**:
   - Store in version control (without secrets)
   - Use separate files for each environment
   - Encrypt secret values

2. **Docker Compose Files**:
   - Store in version control
   - Use templates with environment variable substitution

3. **Database Schema**:
   - Use Alembic migrations
   - Store migration files in version control
   - Tag releases with migration versions

### Infrastructure as Code

1. **Terraform State**:
   - Store state files in encrypted remote backend
   - Enable state locking
   - Use version control for configuration

2. **Kubernetes Manifests**:
   - Store in version control
   - Use Helm charts for templating
   - Implement GitOps workflow

## Disaster Recovery Plan

### Recovery Scenarios

#### Scenario 1: Database Corruption
**Impact**: Complete loss of application data
**RTO**: 4 hours
**Steps**:
1. Assess corruption extent
2. Identify latest clean backup
3. Restore database from backup
4. Replay WAL logs to desired point
5. Validate data integrity
6. Restart application services

#### Scenario 2: File Storage Loss
**Impact**: Lost email templates, assets, and uploads
**RTO**: 2 hours
**Steps**:
1. Identify affected files
2. Restore from latest backup
3. Validate file integrity
4. Update database references if needed
5. Restart application services

#### Scenario 3: Complete Infrastructure Failure
**Impact**: Total loss of application infrastructure
**RTO**: 8 hours
**Steps**:
1. Provision new infrastructure
2. Restore database from backup
3. Restore file storage from backup
4. Deploy application code
5. Configure application with restored data
6. Validate application functionality
7. Update DNS records

### Recovery Team

1. **Primary Contact**: System administrator with database privileges
2. **Secondary Contact**: Application developer with deployment knowledge
3. **Management Contact**: IT manager or CTO for escalation

### Communication Plan

1. **Internal Notification**: Email/pager system for team members
2. **Customer Notification**: Status page and email updates
3. **Stakeholder Notification**: Executive briefings
4. **External Notification**: Public status page updates

## Backup Validation

### Regular Testing

1. **Monthly Restore Tests**:
   - Test restore of database backup to separate environment
   - Verify data integrity and application functionality
   - Document results and issues

2. **Quarterly Disaster Recovery Drills**:
   - Execute full disaster recovery procedure
   - Measure actual RTO and RPO
   - Update procedures based on findings

3. **Annual Penetration Testing**:
   - Test backup security measures
   - Verify encryption effectiveness
   - Assess access controls

### Monitoring and Alerts

1. **Backup Success Monitoring**:
   ```bash
   # Add to backup script
   if [ $? -eq 0 ]; then
     curl -X POST https://alerts.company.com/backups/pewmail/success
   else
     curl -X POST https://alerts.company.com/backups/pewmail/failure
   fi
   ```

2. **Backup Age Monitoring**:
   - Alert if no successful backup in 24 hours
   - Alert if backup file size varies significantly

3. **Storage Space Monitoring**:
   - Alert if backup storage exceeds 80% capacity
   - Alert if insufficient space for next backup

## Security Considerations

### Backup Encryption

1. **At-Rest Encryption**:
   - Use AES-256 encryption for backup files
   - Store encryption keys separately from backups
   - Use hardware security modules (HSM) when possible

2. **In-Transit Encryption**:
   - Use TLS for backup transfers
   - Verify SSL certificates
   - Use secure protocols (SFTP, SCP, HTTPS)

### Access Control

1. **Backup File Permissions**:
   ```bash
   chmod 600 /backup/pewmail/*.tar.gz
   chown backup:backup /backup/pewmail/*.tar.gz
   ```

2. **System Access**:
   - Restrict SSH access to backup servers
   - Use bastion hosts for access
   - Implement two-factor authentication

3. **Cloud Storage Permissions**:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:PutObject",
           "s3:GetObject",
           "s3:DeleteObject"
         ],
         "Resource": "arn:aws:s3:::pewmail-backups/*"
       },
       {
         "Effect": "Allow",
         "Action": "s3:ListBucket",
         "Resource": "arn:aws:s3:::pewmail-backups"
       }
     ]
   }
   ```

## Compliance and Auditing

### Regulatory Requirements

1. **GDPR**:
   - Ensure backups contain only necessary personal data
   - Implement right to erasure for backup data
   - Document data processing activities

2. **SOX**:
   - Maintain audit trails of financial data
   - Implement segregation of duties
   - Document controls and procedures

3. **HIPAA** (if applicable):
   - Implement administrative, physical, and technical safeguards
   - Encrypt protected health information
   - Document security incident responses

### Audit Trail

1. **Backup Logs**:
   - Timestamp of all backup operations
   - Status (success/failure) of operations
   - File sizes and checksums
   - User or system that initiated operation

2. **Access Logs**:
   - Timestamp of all backup access
   - User or system that accessed backup
   - Operations performed on backup
   - IP addresses of access attempts

## Cost Optimization

### Storage Tiering

1. **Hot Storage**: Recent backups (last 7 days)
2. **Warm Storage**: Monthly backups (last 90 days)
3. **Cold Storage**: Annual backups (archive)

### Compression Strategies

1. **Database Dumps**: Use custom format with compression
2. **File Archives**: Use tar.gz or tar.bz2 compression
3. **Incremental Backups**: Use rsync for incremental file sync

### Retention Policies

```python
# Sample retention policy configuration
BACKUP_RETENTION = {
    'hourly': 24,      # Keep 24 hourly backups
    'daily': 30,       # Keep 30 daily backups
    'weekly': 12,      # Keep 12 weekly backups
    'monthly': 12,     # Keep 12 monthly backups
    'yearly': 7        # Keep 7 yearly backups
}
```

## Conclusion

This backup and recovery strategy ensures that Pew Mail can recover from various failure scenarios while meeting business requirements for data protection and availability. Regular testing and updates to these procedures are essential to maintain their effectiveness.

Key success factors:
1. Automated backups with monitoring
2. Regular testing of restore procedures
3. Secure storage of backup data
4. Clear documentation of recovery procedures
5. Regular updates to reflect infrastructure changes