# Database CLI Utility

A Python-based database management CLI for Vecinita that provides direct PostgreSQL access without requiring `psql` to be installed.

## Features

✅ **No psql required** - Uses `psycopg2` for direct database connections
✅ **Environment-aware** - Reads from `.env` or environment variables
✅ **Safe operations** - Confirmation prompts for destructive actions
✅ **Comprehensive commands** - Test, truncate, stats, vacuum, list tables
✅ **Verbose mode** - Debug logging available

## Available Commands

### 1. Test Connection
Test database connectivity and show PostgreSQL version.

```bash
python -m src.utils.db_cli test-connection
```

Output:
```
INFO | Testing database connection...
INFO | ✓ Connection successful
INFO | PostgreSQL version: PostgreSQL 15.1
```

### 2. Truncate Tables
Delete all data from main tables (requires confirmation).

```bash
# Interactive (prompts for confirmation)
python -m src.utils.db_cli truncate

# Skip confirmation (dangerous!)
python -m src.utils.db_cli truncate --no-confirm

# Truncate specific tables
python -m src.utils.db_cli truncate --tables public.document_chunks
```

Output:
```
INFO | Truncating tables: public.document_chunks, public.search_queries, public.processing_queue
WARNING | This will DELETE ALL DATA from these tables!
Are you sure you want to continue? (y/n): y
INFO | ✓ Tables truncated successfully
```

### 3. Table Statistics
Show row counts and sizes for all main tables.

```bash
python -m src.utils.db_cli stats
```

Output:
```
INFO | Fetching table statistics...
INFO | 
INFO | ============================================================
INFO | TABLE STATISTICS
INFO | ============================================================
INFO | document_chunks           |     12,345 rows |     45 MB
INFO | search_queries            |        234 rows |    128 kB
INFO | processing_queue          |          0 rows |      8 kB
INFO | ============================================================
INFO | Total database size: 52 MB
```

### 4. Vacuum Analyze
Optimize database performance by reclaiming space and updating statistics.

```bash
python -m src.utils.db_cli vacuum
```

Output:
```
INFO | Running VACUUM ANALYZE...
INFO | ✓ VACUUM ANALYZE completed
```

### 5. List Tables
Show all tables in the public schema.

```bash
python -m src.utils.db_cli list-tables
```

Output:
```
INFO | Listing tables in public schema...
INFO | 
INFO | ============================================================
INFO | TABLES IN PUBLIC SCHEMA
INFO | ============================================================
INFO |  1. document_chunks
INFO |  2. processing_queue
INFO |  3. search_queries
INFO | ============================================================
INFO | Total: 3 tables
```

## Configuration

The CLI reads database configuration from environment variables or `.env` file:

### Option 1: DATABASE_URL (Recommended)
```bash
DATABASE_URL=postgresql://user:pass@host:port/dbname
```

### Option 2: Individual Parameters
```bash
DB_HOST=db.dosbzlhijkeircyainwz.supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your-password
DB_SSLMODE=require
```

## Verbose Mode

Add `-v` or `--verbose` to any command for detailed debug output:

```bash
python -m src.utils.db_cli stats -v
```

Output includes:
- SQL queries being executed
- Connection parameters (sanitized)
- Detailed error traces

## Integration with Pipeline

The database CLI is now integrated into the data scraping pipeline (`scripts/data_scrape_load.py`):

```bash
# Pipeline automatically uses db_cli instead of psql
python scripts/data_scrape_load.py --clean
```

The pipeline will:
1. Use `src.utils.db_cli truncate` instead of `psql`
2. Handle errors gracefully
3. Log all operations

## Error Handling

The CLI provides clear error messages:

```
ERROR | ✗ Connection failed: FATAL: password authentication failed
ERROR | ✗ Truncate failed: relation "public.nonexistent" does not exist
ERROR | ✗ Unexpected error: [detailed error message]
```

## Exit Codes

- `0` - Success
- `1` - Error
- `130` - User cancelled (Ctrl+C)

## Dependencies

Required (already in `pyproject.toml`):
- `psycopg2-binary` - PostgreSQL adapter
- `python-dotenv` - Environment variable loading (optional)

## Security Notes

⚠️ **Database Password**: 
- Store in `.env` file (not committed to git)
- Never hardcode in scripts
- Use environment variables in production

⚠️ **Truncate Operations**:
- Always prompts for confirmation (unless `--no-confirm`)
- Logs all operations for audit trail
- Cannot be undone - be careful!

## Advantages Over psql

| Feature | psql | db_cli |
|---------|------|--------|
| Installation | Separate PostgreSQL client | Python only |
| Dependencies | System package | pip package |
| Cross-platform | Varies by OS | Works everywhere |
| Integration | Shell commands | Native Python |
| Error handling | Exit codes only | Detailed exceptions |
| Logging | Limited | Comprehensive |

## Troubleshooting

### Connection Failed
```bash
# Test connection first
python -m src.utils.db_cli test-connection -v

# Check environment variables
python -c "import os; print(os.getenv('DB_HOST'))"
```

### Module Not Found
```bash
# Ensure you're in the project root
cd /path/to/vecinita

# Run with -m flag
python -m src.utils.db_cli test-connection
```

### psycopg2 Not Installed
```bash
# Install dependencies
uv sync
# or
pip install psycopg2-binary
```

## Examples

```bash
# Quick health check
python -m src.utils.db_cli test-connection

# Check table sizes before cleanup
python -m src.utils.db_cli stats

# Clean database for fresh start
python -m src.utils.db_cli truncate

# Optimize after large operations
python -m src.utils.db_cli vacuum

# Debug connection issues
python -m src.utils.db_cli test-connection -v
```

## See Also

- `scripts/data_scrape_load.py` - Main pipeline using db_cli
- `src/utils/vector_loader.py` - Data loading utilities
- `README.md` - Project documentation
