<!-- code-review-graph MCP tools -->
## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes` or `query_graph` instead of Grep
- **Understanding impact**: `get_impact_radius` instead of manually tracing imports
- **Code review**: `detect_changes` + `get_review_context` instead of reading entire files
- **Finding relationships**: `query_graph` pattern="tests_for" to check coverage
- **Architecture questions**: `get_architecture_overview` + `list_communities`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools

| Tool | Use when |
|------|----------|
| `detect_changes` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context` | Need source snippets for review — token-efficient |
| `get_impact_radius` | Understanding blast radius of a change |
| `get_affected_flows` | Finding which execution paths are impacted |
| `query_graph` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes` | Finding functions/classes by name or keyword |
| `get_architecture_overview` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

### Workflow

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes` for code review.
3. Use `get_affected_flows` to understand impact.
4. Use `query_graph` pattern="tests_for" to check coverage.

## Project Summary for Claude

This repository contains a Streamlit-based news recommendation system with both PostgreSQL-backed and SQLite-backed authentication components.

### Overall architecture

- **Frontend**: Streamlit UI built in `Home.py`, `app.py`, and page modules under `pages/`.
- **Backend**: Uses RSS aggregation, database persistence, authentication, logging, and analytics.
- **Auth path 1**: `app.py` + `api/auth.py` uses PostgreSQL, bcrypt, JWT tokens, and Streamlit session state.
- **Auth path 2**: `Home.py` + `auth_new.py` uses SQLite, session tokens, local preferences, bookmarks, and reading activity.

### Most important files and responsibilities

- `Home.py`: Primary Streamlit entrypoint for the SQLite-based implementation.
  - restores session from query params via `restore_session_from_query()`.
  - builds sidebar for source/category preferences, search, bookmarks, and exports.
  - defines `fetch_rss(url)` with caching and error handling.
  - defines `get_news()` to normalize and display feed items.

- `app.py`: Alternate Streamlit entrypoint for the Postgres-based implementation.
  - presents login/signup UI through `show_landing_page()`.
  - renders dashboard, news feed, bookmarks, activity, and profile in `show_dashboard()`.
  - handles news fetching, bookmark state, preferences, and user profile actions.

- `api/auth.py`: PostgreSQL-backed authentication manager.
  - `AuthManager.hash_password(password)` — bcrypt hash.
  - `AuthManager.verify_password(password, password_hash)` — verify bcrypt.
  - `AuthManager.validate_email(email)` — regex validation.
  - `AuthManager.validate_password(password)` — strength rules.
  - `AuthManager.create_access_token(data, expires_delta)` — JWT creation.
  - `AuthManager.decode_token(token)` — JWT decode.
  - `AuthManager.sign_up(email, password, username)` — register user.
  - `AuthManager.login(email, password)` — login and store session state.
  - `AuthManager.logout()` — clear state and rerun.
  - `AuthManager.is_authenticated()` and `AuthManager.get_current_user()`.

- `auth_new.py`: SQLite-based auth + analytics + bookmark persistence.
  - `create_connection()` — create SQLite DB and tables.
  - `hash_password(password)` — SHA-256 password hashing.
  - `save_preferences(email, sources, category)` and `load_preferences(email)`.
  - `create_session_token(email)` and `validate_session_token(email, token)`.
  - `restore_session_from_query()` — populate session from auth token.
  - `sign_up()` and `login()` — Streamlit forms.
  - `logout()` — clear session and rerun.
  - bookmark helpers: `add_bookmark`, `get_bookmarks`, `delete_bookmark`.
  - reading analytics: `log_article_read`, `get_articles_read_count`, `get_total_reading_time`, `get_articles_by_category`, `get_articles_by_source`, `get_daily_reading_stats`, `get_hourly_pattern`, `get_favorite_topic`, `get_reading_streak`, `get_reading_activity`.
  - `show_auth_page()` — renders combined login/signup UI.

- `api/news_fetcher.py`: RSS aggregator and cache.
  - `NEWS_SOURCES` defines named RSS sources and categories.
  - `NewsFetcher.fetch_rss_feed(url, source_name, category)` — fetch XML, parse items, normalize fields, cache results, save to DB.
  - `NewsFetcher.get_news_for_user(user_id, selected_sources, category)` — collects articles for the user, deduplicates URLs, logs activity, limits to 30.
  - `NewsFetcher.search_news(query, category)` — full-text search using `NewsModel.search_articles()`.
  - async helpers `fetch_rss_async()` and `fetch_multiple_sources()` are present but not fully implemented.

- `database/connection.py`: PostgreSQL connection manager.
  - `PostgreSQLManager._initialize_pool()` — create a connection pool.
  - `get_connection()` and `get_cursor(commit=False)` context managers.
  - `execute_query(query, params, fetch_one, fetch_all)`.
  - `close_all_connections()`.
  - `get_db_manager()` cached Streamlit resource.
  - `db_manager` global singleton is used by models.

- `database/models.py`: persistence and schema.
  - `UserModel` CRUD and preference updates.
  - `BookmarkModel` add, remove, query, existence check.
  - `ActivityModel` logging and retrieval.
  - `NewsModel` table creation, article save, full-text search.
  - `NewsModel.create_tables()` runs automatically on import.

- `utils/logger.py`: logging and instrumentation.
  - `setup_logger(log_level, log_to_file)` configures console and file output, rotation, retention, compression, and security logging.
  - `log_error`, `log_info`, `log_warning`, `log_debug`.
  - `log_user_action()` for user-specific events.
  - `log_performance()` decorator.

- `utils/rate_limiter.py`: rate limiting.
  - `RateLimiter` sliding-window algorithm.
  - `is_allowed()`, `get_status()`, `reset_client()`, `reset_all()`.
  - `check_rate_limit(client_id, max_requests, window_seconds)` wrapper.

- `utils/__init__.py` exports all helper utilities.
  - cache helpers: `CacheManager`, `cached`, `st_cached_fetch`.
  - rate limiter exports.
  - logger exports.
  - helper functions: `validate_url`, `clean_html`, `truncate_text`, `format_date`, `extract_domain`, `generate_id`, `safe_get`, `chunk_list`, `is_valid_email`, `slugify`, `get_time_ago`.

### `pages/` folder overview

`pages/` contains Streamlit page modules designed for multi-page apps:
- `01_📊_Dashboard.py` — news feed dashboard with custom cards, search, filters, bookmarks, and activity tracking.
- `02_🔖_Saved_News.py` — saved news/bookmark list page.
- `03_⚙️_Settings.py` — settings and preferences UI.
- `04_📈_Analytics.py` — analytics UI with Plotly charts and metrics, using analytics helper functions from `auth_new.py`.
- `05_👤_Profile.py` — user profile page with account information and delete account action.

### Production and validation files

- `validate_env.py` — validates required environment variables and warns on weak configuration.
- `health.py` — performs runtime health checks including database connectivity.
- `test_basic.py` — basic pytest tests for environment, health, DB connectivity, rate limiting, and auth validation.
- `README.md` — installation, deployment, and production deployment guidance.

### Deployment files

- `Dockerfile` — builds a Python 3.10 Slim image, installs dependencies, copies files, and starts Streamlit.
- `docker-compose.yml` — runs the app container and binds port `8501`.

### Tech stack and tools

- Python 3.10
- Streamlit for UI
- PostgreSQL for production DB
- SQLite for legacy/local auth in `Home.py`/`auth_new.py`
- `psycopg2-binary` for PostgreSQL access
- `bcrypt` and `python-jose` for auth security
- `requests` and `xmltodict` for RSS ingestion
- `aiohttp` and `cachetools` for async and cached feed fetching
- `loguru` for logging
- `python-dotenv` for `.env` configuration
- `pytest` for tests

### Environment and production requirements

The production environment should define:
- `DATABASE_URL` — PostgreSQL connection string
- `SECRET_KEY` — strong secret (recommended 32+ characters)
- `DEBUG` — `False` for production
- `JWT_ALGORITHM`, `JWT_EXPIRATION_HOURS`
- `DATABASE_POOL_SIZE` for Postgres pooling
- `RSS_TIMEOUT`, `RSS_CACHE_DURATION`, `MAX_ARTICLES_PER_FEED`

The `.env.example` has been updated to require `DATABASE_URL`.

### Current repo warnings and important notes

- There are two auth implementations in the same repo, which is a key architectural inconsistency.
- `Home.py` and `auth_new.py` still use local SQLite, whereas `app.py` and `api/auth.py` use PostgreSQL.
- `pages/04_📈_Analytics.py` depends on analytics data functions in `auth_new.py`.
- If `DATABASE_URL` is missing, `validate_env.py` fails.
- `health.py` depends on `psycopg2` and a valid PostgreSQL DB to report healthy.

### What Claude must remember

- Treat the project as a Streamlit news aggregator with two parallel auth paths.
- The main backend functionality includes RSS fetching, caching, storing articles, bookmarks, activity logging, and analytics.
- Production readiness is improved, but the repo still requires environment setup and Postgres validation.
- Answer questions using exact module names, function names, and implementation intent.
- Mention the two auth channels and the fact that `auth_new.py` is the legacy/local path.
