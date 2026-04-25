# 📰 Personalized News Recommendation System

A Streamlit-based news aggregation and recommendation application with user authentication, personalized preferences, bookmarks, and advanced search capabilities.

## Features

✨ **Core Features:**
- 🔐 User authentication (signup/login with SQLite)
- 📰 Multi-source news aggregation from RSS feeds
- 🎯 Personalized news recommendations based on categories and sources
- 🔖 Bookmark articles for later reading
- 🔍 Real-time search functionality
- 📤 Export news to JSON/CSV
- 💾 Persistent user preferences
- 🔄 Session persistence with token-based authentication
- ⚡ Retry logic with exponential backoff for network requests
- 📝 Comprehensive logging and error handling

## Tech Stack

- **Frontend:** Streamlit 1.28.1
- **Backend:** Python 3.10
- **Database:** SQLite
- **News Sources:** RSS/XML feeds
- **HTTP Client:** Requests library
- **Configuration:** Python-dotenv

## Installation

### Option 1: Automated Setup (Recommended)

**Windows:**
```bash
setup.bat
```

**Linux/macOS:**
```bash
bash setup.sh
```

### Option 2: Manual Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd News_Recommendation_System
```

2. Create and activate virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate.bat

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run the application:
```bash
streamlit run Home.py
```

The app will open at `http://localhost:8501`

## Configuration

Edit `.env` file to customize:
- `DATABASE_PATH`: Location of SQLite database
- `RSS_TIMEOUT`: Timeout for RSS feed requests (seconds)
- `RSS_CACHE_DURATION`: How long to cache RSS feeds (seconds)
- `DEBUG`: Enable debug logging
- `SECRET_KEY`: Change for production use

## Production Deployment

### Prerequisites

- PostgreSQL database (recommended for production)
- Docker and Docker Compose
- Environment variables configured

### Environment Setup

1. Copy environment template:
```bash
cp .env.example .env
```

2. Configure production settings in `.env`:
```bash
# Required for production
DATABASE_URL=postgresql://user:password@host:5432/dbname
SECRET_KEY=your-very-secure-secret-key-here
DEBUG=False

# Optional
JWT_EXPIRATION_HOURS=24
DATABASE_POOL_SIZE=20
```

### Docker Production Deployment

```bash
# Build and run
docker-compose up -d --build

# Check logs
docker-compose logs -f

# Health check
curl http://localhost:8501/_stcore/health
```

### Manual Production Deployment

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Validate environment:
```bash
python validate_env.py
```

3. Run health check:
```bash
python health.py
```

4. Start application:
```bash
streamlit run Home.py --server.port=8501 --server.address=0.0.0.0
```

### Production Checklist

- ✅ Environment variables configured
- ✅ Database connection tested
- ✅ Health checks passing
- ✅ Logs configured
- ✅ Error handling implemented
- ✅ Rate limiting enabled
- ✅ SSL/TLS configured (if needed)
- ✅ Backups configured
- ✅ Monitoring set up

### Monitoring

- Check application logs: `logs/app.log`
- Monitor database connections
- Health endpoint: `GET /health`
- Error logs: `logs/errors.log`

### Troubleshooting

- **Database connection issues**: Check `DATABASE_URL` format
- **Import errors**: Run `pip install -r requirements.txt`
- **Permission errors**: Ensure write access to `logs/` and database
- **Port conflicts**: Change `STREAMLIT_PORT` in `.env`
docker build -t news-app .
docker run -p 8501:8501 -v $(pwd)/news_recommendation.db:/app/news_recommendation.db news-app
```

## Project Structure

```
News_Recommendation_System/
├── Home.py                    # Main Streamlit application
├── auth_new.py               # Authentication & user management
├── News.py                   # News model/utilities
├── news_app.py               # Alternative news interface
├── config.py                 # Configuration management
├── utils.py                  # Utility functions & decorators
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
├── .gitignore               # Git ignore patterns
├── setup.sh                 # Linux/macOS setup script
├── setup.bat                # Windows setup script
├── Dockerfile               # Docker image definition
├── docker-compose.yml       # Docker Compose configuration
├── README.md                # This file
├── preferences/             # User preferences storage
└── data/                    # Data storage directory
```

## Usage

### Authentication
- **Sign Up:** Create new account with email and password
- **Login:** Access your personalized dashboard
- **Session Persistence:** Stay logged in across browser refresh using token-based authentication

### News Dashboard
1. **Quick Categories:** Click category buttons to view news by category
2. **Preferences:** Select preferred news sources and categories
3. **Search:** Find articles by keyword in real-time
4. **Bookmarks:** Save articles to read later
5. **Export:** Download displayed news as JSON or CSV

### Bookmarks Management
- Click bookmark icon to save articles
- View all bookmarks in the sidebar
- Delete bookmarks individually

### Search
- Type keywords in the search box
- Results update in real-time
- Search across article titles and descriptions

## API & Database

### Supported RSS Feeds
- Times of India News
- BBC News
- CNN News
- Reuters News
- The Guardian

### Database Schema

**Users Table:**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
```

**Sessions Table (Token-based auth):**
```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    token TEXT UNIQUE NOT NULL,
    created_at REAL NOT NULL,
    expires_at REAL NOT NULL
)
```

**Bookmarks Table:**
```sql
CREATE TABLE bookmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    title TEXT NOT NULL,
    link TEXT NOT NULL,
    source TEXT,
    saved_date TEXT
)
```

**Preferences Table:**
```sql
CREATE TABLE preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    selected_sources TEXT,
    selected_category TEXT
)
```

## Features in Detail

### 🔐 Authentication
- Secure password hashing with bcrypt
- Token-based session management
- 7-day session expiry
- Persistent login via URL query parameters

### 📰 News Aggregation
- Fetches from multiple RSS sources
- Caching to reduce API calls
- Retry logic with exponential backoff
- User-Agent header to bypass restrictions

### 🔍 Search & Filter
- Real-time keyword search
- Filter by category
- Filter by source
- Combined filtering

### 💾 Data Management
- Save user preferences
- Bookmark articles
- Export to JSON/CSV formats
- Session persistence

### 📊 Logging & Monitoring
- File and console logging
- Error tracking
- Debug mode support

## Troubleshooting

### Connection Errors
- Check internet connection
- Verify RSS feed URLs are accessible
- Increase `RSS_TIMEOUT` in `.env` if feeds are slow

### Database Errors
- Ensure `DATABASE_PATH` in `.env` is writable
- Check SQLite is installed
- Delete `news_recommendation.db` and restart to reset database

### Authentication Issues
- Clear browser cache/cookies
- Check `.env` has correct `SECRET_KEY`
- Verify email format is valid

### Docker Issues
```bash
# View logs
docker-compose logs -f

# Stop and remove containers
docker-compose down

# Rebuild image
docker-compose build --no-cache
docker-compose up -d
```

## Performance Tips

1. **Reduce RSS_CACHE_DURATION** for more fresh news (lower values = more API calls)
2. **Increase RSS_TIMEOUT** if feeds are slow
3. **Limit MAX_ARTICLES_PER_FEED** to reduce data size
4. **Use Docker** for consistent deployment performance

## Security Considerations

- ⚠️ **Change `SECRET_KEY` in `.env` for production**
- Use HTTPS in production (add reverse proxy like Nginx)
- Keep `.env` file out of version control (use `.gitignore`)
- Regularly update dependencies: `pip install -r requirements.txt --upgrade`
- Use strong passwords for admin accounts

## Contributing

To contribute improvements:
1. Create a new branch
2. Make changes
3. Test thoroughly
4. Submit pull request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review application logs in the logs directory
3. Create an issue on GitHub with detailed description

## Roadmap

- [ ] Email digest feature
- [ ] Advanced recommendation algorithm
- [ ] Multi-language support
- [ ] Mobile app companion
- [ ] Social sharing integration
- [ ] Sentiment analysis for articles
- [ ] Reading time estimation
- [ ] Dark mode support

## Version History

**v1.0.0** (Current)
- Initial release
- Core features: auth, news aggregation, bookmarks, search, export
- Token-based session persistence
- Docker support
- Comprehensive logging

---

**Built with ❤️ using Streamlit**
