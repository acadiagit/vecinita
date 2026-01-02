# Vecinita Documentation Index

Quick reference guide to all documentation in this project.

## \ud83d\ude80 Getting Started

| Document | Description | Audience |
|----------|-------------|----------|
| [../QUICKSTART.md](../QUICKSTART.md) | Complete setup guide with Docker and local dev | Developers (new) |
| [../README.md](../README.md) | Project overview and quick reference | Everyone |
| [../backend/README.md](../backend/README.md) | Backend API and tools details | Backend developers |
| [../frontend/README.md](../frontend/README.md) | Frontend components and testing | Frontend developers |

## \ud83d\udcca Project Status

| Document | Description | Last Updated |
|----------|-------------|--------------|
| [FINAL_STATUS_REPORT.md](FINAL_STATUS_REPORT.md) | Complete project status (108 tests passing) | Production Ready |
| [TEST_COVERAGE_SUMMARY.md](TEST_COVERAGE_SUMMARY.md) | Testing strategy and results | 108/108 tests passing |

## \ud83c\udfd7\ufe0f Architecture & Design

| Document | Description | Category |
|----------|-------------|----------|
| [LANGGRAPH_REFACTOR_SUMMARY.md](LANGGRAPH_REFACTOR_SUMMARY.md) | LangGraph agent architecture and implementation | Core Architecture |
| [architecture/NEW_CODE_STRUCTURE.md](architecture/NEW_CODE_STRUCTURE.md) | Overall project structure | Code Organization |
| [architecture/SCRAPER_ORGANIZATION.md](architecture/SCRAPER_ORGANIZATION.md) | Web scraper backend design | Scraper Architecture |

## \u2728 Features & Capabilities

| Document | Description | Category |
|----------|-------------|----------|
| [STREAMING_UX_SUMMARY.md](STREAMING_UX_SUMMARY.md) | Enhanced streaming with planning agent | User Experience |
| [SOURCE_TITLE_CLEANUP.md](SOURCE_TITLE_CLEANUP.md) | Source attribution improvements | Data Quality |
| [features/STREAMING_MODE.md](features/STREAMING_MODE.md) | Memory-efficient data processing | Performance |
| [features/HTML_CLEANER_README.md](features/HTML_CLEANER_README.md) | Content extraction and cleanup | Data Processing |
| [features/CHUNKING_UPLOAD_PIPELINE.md](features/CHUNKING_UPLOAD_PIPELINE.md) | Data ingestion pipeline | Data Pipeline |

## \ud83d\udee0\ufe0f Tools & Utilities

| Document | Description | Category |
|----------|-------------|----------|
| [tools/DB_CLI_USAGE.md](tools/DB_CLI_USAGE.md) | Database CLI tool guide | Database Management |
| [tools/DB_CLI_SUMMARY.md](tools/DB_CLI_SUMMARY.md) | DB CLI quick reference | Database Management |
| [DB_SEARCH_DIAGNOSTIC_GUIDE.md](DB_SEARCH_DIAGNOSTIC_GUIDE.md) | Database search troubleshooting | Debugging |

## \ud83d\udcd6 Guides & How-Tos

| Document | Description | Category |
|----------|-------------|----------|
| [guides/BEFORE_AFTER_GUIDE.md](guides/BEFORE_AFTER_GUIDE.md) | Comparison documentation | Development |
| [guides/ENHANCED_LOGGING.md](guides/ENHANCED_LOGGING.md) | Logging configuration and best practices | Debugging |
| [guides/LOGGING_QUICK_REFERENCE.md](guides/LOGGING_QUICK_REFERENCE.md) | Quick logging reference | Debugging |

## \ud83d\udcdd Documentation by Use Case

### I want to...

**...get started quickly**
- Start here: [../QUICKSTART.md](../QUICKSTART.md)
- Backend setup: [../backend/README.md](../backend/README.md)
- Frontend setup: [../frontend/README.md](../frontend/README.md)

**...understand the architecture**
- Agent design: [LANGGRAPH_REFACTOR_SUMMARY.md](LANGGRAPH_REFACTOR_SUMMARY.md)
- Code structure: [architecture/NEW_CODE_STRUCTURE.md](architecture/NEW_CODE_STRUCTURE.md)
- Scraper design: [architecture/SCRAPER_ORGANIZATION.md](architecture/SCRAPER_ORGANIZATION.md)

**...implement new features**
- See streaming implementation: [STREAMING_UX_SUMMARY.md](STREAMING_UX_SUMMARY.md)
- Check test coverage: [TEST_COVERAGE_SUMMARY.md](TEST_COVERAGE_SUMMARY.md)
- Review code structure: [architecture/NEW_CODE_STRUCTURE.md](architecture/NEW_CODE_STRUCTURE.md)

**...troubleshoot issues**
- Database search: [DB_SEARCH_DIAGNOSTIC_GUIDE.md](DB_SEARCH_DIAGNOSTIC_GUIDE.md)
- Logging guide: [guides/ENHANCED_LOGGING.md](guides/ENHANCED_LOGGING.md)
- Source attribution: [SOURCE_TITLE_CLEANUP.md](SOURCE_TITLE_CLEANUP.md)

**...run tests**
- Test coverage: [TEST_COVERAGE_SUMMARY.md](TEST_COVERAGE_SUMMARY.md)
- Backend tests: `cd backend && uv run pytest`
- Frontend tests: `cd frontend && npm run test`

**...deploy to production**
- Docker setup: [../QUICKSTART.md](../QUICKSTART.md#docker-compose)
- Render deployment: [../render.yaml](../render.yaml)
- Environment setup: [../QUICKSTART.md](../QUICKSTART.md#configuration)

## \ud83d\udccc Quick Links

- **Project Repository**: [GitHub - acadiagit/vecinita](https://github.com/acadiagit/vecinita)
- **Issue Tracker**: [GitHub Issues](https://github.com/acadiagit/vecinita/issues)
- **CI/CD Status**: ![Tests](https://github.com/acadiagit/vecinita/actions/workflows/test.yml/badge.svg)

---

**Last Updated**: January 2026  
**Status**: Production Ready (108/108 tests passing)
