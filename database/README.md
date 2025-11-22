# Database Files

This folder contains database-related files including backups, dumps, and schema updates.

## 📁 Folder Structure

### `/backups`
Database backup and dump files
- `backup_before_migration.sql` - Backup before schema migrations
- `kooptimizer_db2_complete_dump.sql` - Complete database dump (34.79 MB)

### `/updates`
Database schema updates and migration scripts
- SQL migration scripts
- Python migration utilities
- Stored procedure definitions

## 🔒 Security Note

**Important:** Database dump files contain sensitive data and should NOT be committed to git.

The `.gitignore` file is configured to exclude:
- `*.sql` files
- Database dumps
- Sensitive backups

## 📦 Backup Best Practices

1. **Before Major Changes**: Always create a backup
   ```bash
   pg_dump -U postgres -d kooptimizer_db2 > database/backups/backup_YYYYMMDD.sql
   ```

2. **Regular Backups**: Schedule automated backups for production

3. **Secure Storage**: Store backups in secure, encrypted locations

4. **Test Restores**: Periodically test backup restoration

## 🔄 Restoring from Backup

To restore a database from backup:

```bash
# Create new database
createdb -U postgres kooptimizer_db2

# Restore from backup
psql -U postgres -d kooptimizer_db2 -f database/backups/kooptimizer_db2_complete_dump.sql
```

See [Database Setup Instructions](../docs/setup/DATABASE_SETUP_INSTRUCTIONS.md) for detailed steps.

## 📝 Schema Updates

The `/updates` folder contains:
- Migration scripts in chronological order
- Stored procedure definitions
- Enum type definitions
- Table schema modifications

Run updates in order to maintain database integrity.

---
*Last updated: November 22, 2025*
