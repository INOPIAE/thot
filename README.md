# NLF Database Application

Professional Database Management System with Vue.js Frontend and FastAPI Backend.

## Features

### Authentication & User Management
- ✅ User Authentication with JWT tokens
- ✅ Two-Factor Authentication (OTP)
- ✅ Role-Based Access Control (RBAC)
- ✅ User Registration with Email Verification
- ✅ Password Reset Functionality
- ✅ Email Change with Verification
- ✅ User Profile Management
- ✅ Support Team User Management

### Records & Data Management
- ✅ Record Management (CRUD operations)
- ✅ Keyword Management for Names and Locations
- ✅ Phonetic Search (Cologne Phonetic & Double Metaphone)
- ✅ Pages Management with PDF Upload
- ✅ File Upload to Filesystem
- ✅ Restriction & WorkStatus Management
- ✅ Full-text Search and Filtering

### Technical Features
- ✅ Multi-language Support (English, German)
- ✅ PostgreSQL Database with SQLAlchemy ORM
- ✅ Alembic migrations support for schema changes
- ✅ RESTful API with FastAPI
- ✅ Vue.js 3 Frontend with Pinia Store
- ✅ Comprehensive Unit Tests

## Requirements

- Python 3.9+
- Node.js 16+
- PostgreSQL 12+
- Visual Studio Code

## Quick Start

### 1. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate (Windows)
pip install -r requirements.txt

# Configure .env file (copy from .env.example)
cp .env.example .env

# Initialize database
python scripts/init_db.py

# Start development server
python -m app.main
```

Backend runs at: `http://localhost:8000`

### 2. Frontend Setup

```bash
cd frontend
npm install

# Configure .env.local file (copy from .env.example)
cp .env.example .env.local

# Start development server
npm run dev
```

Frontend runs at: `http://localhost:3000`

## Documentation

- [Installation & Setup Guide](install.md)
- [API Documentation](http://localhost:8000/docs) (Swagger UI)
- [API ReDoc](http://localhost:8000/redoc)

## Project Structure

```
nlf/db/
├── backend/           # Python FastAPI backend
│   ├── app/          # Main application
│   ├── scripts/      # Database initialization
│   ├── tests/        # Backend unit tests
│   └── config.py     # Configuration
│
├── frontend/         # Vue.js frontend
│   ├── src/         # Source code
│   ├── tests/       # Frontend unit tests
│   └── vite.config.js
│
└── install.md        # Setup guide
```

## Testing

### Backend
```bash
cd backend
pytest tests/ -v --cov=app
```

### Frontend
```bash
cd frontend
npm run test
```

## Database

### Create Databases
```sql
CREATE USER nlf_user WITH PASSWORD 'nlf_password';
CREATE DATABASE nlf_db OWNER nlf_user;
CREATE DATABASE nlf_db_test OWNER nlf_user;
```

### Models

#### Authentication & Authorization
- **User** - User accounts with authentication
- **Role** - User roles (admin, support, user)
- **Permission** - Granular permissions
- **UserRole** - User-to-role mapping
- **RolePermission** - Role-to-permission mapping
- **UserRegistration** - Registration tokens
- **PasswordResetToken** - Password reset tokens

#### Records & Data
- **Record** - Main data records with title, signature, description
- **Page** - Pages within records with PDF file support
- **KeywordName** - Keywords for names (with phonetic search)
- **KeywordLocation** - Keywords for locations (with phonetic search)
- **RecordsKeywordsName** - Record-to-name-keyword mapping
- **RecordsKeywordsLocation** - Record-to-location-keyword mapping
- **Restriction** - Access restrictions (none, confidential, locked, privacy)
- **RestrictionDetail** - Detailed restriction information
- **WorkStatus** - Workflow status tracking
- **WorkStatusArea** - Status area categories (record, page)

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/password-reset` - Request password reset
- `POST /api/v1/auth/password-reset/confirm/{token}` - Confirm password reset

### User Profile
- `GET /api/v1/users/profile` - Get user profile
- `PUT /api/v1/users/profile` - Update profile
- `POST /api/v1/users/password-change` - Change password
- `POST /api/v1/users/email-change` - Change email

### User Management (Admin/Support)
- `GET /api/v1/users` - List users (with filtering and pagination)
- `GET /api/v1/users/{id}` - Get user details
- `PUT /api/v1/users/{id}` - Update user

### Records Management
- `GET /api/v1/records` - List records (with search and pagination)
- `GET /api/v1/records/{id}` - Get record details
- `POST /api/v1/records` - Create new record
- `PUT /api/v1/records/{id}` - Update record
- `DELETE /api/v1/records/{id}` - Delete record (soft delete)
- `GET /api/v1/records/restrictions` - Get available restrictions
- `GET /api/v1/records/workstatus` - Get available work statuses

### Pages Management
- `GET /api/v1/pages` - List pages (filterable by record_id)
- `GET /api/v1/pages/{id}` - Get page details
- `POST /api/v1/pages` - Create new page with PDF upload
- `PUT /api/v1/pages/{id}` - Update page (with optional file upload)
- `DELETE /api/v1/pages/{id}` - Delete page (soft delete)
- `GET /uploads/{record_id}/{filename}` - Download uploaded PDF file

### Configuration
- `GET /api/v1/config` - Get public application configuration

## Environment Variables

### Backend (.env)
```env
ENVIRONMENT=development
DB_HOST=localhost
DB_PORT=5432
DB_USER=nlf_user
DB_PASSWORD=nlf_password
DB_NAME=nlf_db
SECRET_KEY=your-secret-key
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# File Upload Configuration
UPLOAD_DIRECTORY=./uploads
MAX_UPLOAD_SIZE=52428800
```

### Frontend (.env.local)
```env
VITE_API_URL=http://localhost:8000/api/v1
```

## Development Workflow

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Write/update tests
4. Commit: `git commit -am 'Add feature'`
5. Push: `git push origin feature/your-feature`
6. Create Pull Request

## Code Quality

- Backend: Python with Black, Flake8, isort
- Frontend: JavaScript/Vue with ESLint

```bash
# Backend
cd backend
black app tests
flake8 app tests

# Frontend
cd frontend
npm run lint
```

## Security

⚠️ **Important Notes:**
- Change SECRET_KEY in production
- Use environment variables for sensitive data
- Enable HTTPS in production
- Implement rate limiting
- Regular dependency updates

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
1. Check the [Installation Guide](install.md)
2. Review API Documentation
3. Create a GitHub Issue

## Author

Your Company

---

**Version:** 1.0.0  
**Last Updated:** 2026-02-28
