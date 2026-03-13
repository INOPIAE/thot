# NLF Database Application

Professional Database Management System with Vue.js Frontend and FastAPI Backend.

## Features

### Authentication & User Management
- ✅ User Authentication with JWT tokens
- ✅ Two-Factor Authentication (OTP)
- ✅ OTP Reset via Email (User + Support initiated)
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
- ✅ **PDF Watermarking with User Information**
- ✅ **Dynamic Thumbnail Generation with Watermarks**
- ✅ File Upload to Filesystem
- ✅ Restriction & WorkStatus Management
- ✅ Full-text Search and Filtering

### Technical Features
- ✅ Multi-language Support (English, German)
- ✅ PostgreSQL Database with SQLAlchemy ORM
- ✅ Alembic migrations support for schema changes
- ✅ RESTful API with FastAPI
- ✅ Vue.js 3 Frontend with Pinia Store
- ✅ Dynamic Logo and Favicon Loading from Backend
- ✅ External Legal HTML Content (Imprint, Data Protection, Terms of Service per language)
- ✅ Environment-based Configuration (Dev/Production)
- ✅ Comprehensive Unit Tests

## Requirements

- Python 3.9+
- Node.js 16+
- PostgreSQL 12+
- **PyMuPDF runtime support** (installed via `requirements.txt`)
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

Legal pages:
- Imprint and Data Protection are available in the frontend information area.
- Terms of Service remains available at `/terms-of-service` and via registration / Swagger links, but is intentionally not shown in the navigation.

## API Quick Guide (Swagger)

### 1. Open API Docs
- Start backend and open: `http://localhost:8000/docs`
- Base API prefix is: `/api/v1`

### 2. Login (Get JWT Token)
- Open endpoint: `POST /api/v1/auth/login`
- Click `Try it out`
- Enter JSON body:

```json
{
  "username": "your_username",
  "password": "your_password",
  "otp_code": "123456"
}
```

Notes:
- `otp_code` is required when OTP is enabled for the user.
- `otp_code` is also required for users with role `support` or `admin`.
- On success, response contains `access_token` and `token_type`.

### 3. Authenticate in Swagger
- Click `Authorize` (top-right).
- Paste the token from `access_token` into the bearer auth field.
- If needed, use format: `Bearer <access_token>`.
- Click `Authorize`, then `Close`.

### 4. Call Protected Endpoints
- Example: `GET /api/v1/users/profile`
- Click `Try it out` -> `Execute`
- If authentication is correct, you get the user profile response.

### 5. Typical Auth Errors
- `401 Unauthorized`: token missing/invalid/expired.
- `401 Unauthorized`: login failed (e.g. wrong credentials, missing OTP, invalid OTP, inactive account).

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
- `POST /api/v1/auth/register` - Register new user. When `CLOSED_REGISTRATION=true` and at least one user already exists, this endpoint is limited to authenticated `support` or `admin` users. The bootstrap case stays open until the first user exists.
- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/password-reset` - Request password reset
- `POST /api/v1/auth/password-reset/confirm/{token}` - Confirm password reset
- `GET /api/v1/auth/otp-reset/confirm/{token}` - Validate support OTP reset link and return temporary OTP setup payload
- `POST /api/v1/auth/otp-reset/confirm/{token}` - Confirm OTP reset with one OTP code

### User Profile
- `GET /api/v1/users/profile` - Get user profile
- `PUT /api/v1/users/profile` - Update profile
- `POST /api/v1/users/password-change` - Change password
- `POST /api/v1/users/email-change` - Change email

### User Management (Admin/Support)
- `GET /api/v1/users` - List users (with filtering and pagination)
- `GET /api/v1/users/{id}` - Get user details
- `PUT /api/v1/users/{id}` - Update user
- `PUT /api/v1/users/{id}/password-reset` - Trigger password reset email (support/admin)
- `PUT /api/v1/users/{id}/otp-reset` - Trigger OTP reset email (support/admin, 24h expiry by default)

Notes:
- User list/detail responses include `otp_enabled` so support can see whether OTP is configured.
- Support-triggered OTP reset stores link tokens in `otp_reset_tokens` and follows the same confirmation flow as user OTP reset.

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
- `GET /api/v1/pages/{id}/view-pdf` - **View PDF with user-specific watermark (inline)**
- `GET /api/v1/pages/{id}/thumbnail?width=200` - **Get thumbnail with watermark**
- `GET /api/v1/pages/{id}/download-watermarked` - **Download PDF with watermark**
- `GET /uploads/{record_id}/{filename}` - **(Deprecated) Direct file access - use watermarked endpoints**

### Configuration
- `GET /api/v1/config` - Get public application configuration, including `features.closedRegistration` and `features.closedRegistrationConfigured`

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
USER_OTP_RESET_TOKEN_EXPIRE_HOURS=1
SUPPORT_OTP_RESET_TOKEN_EXPIRE_HOURS=24

# Application Configuration
APP_NAME=NLF Database
COMPANY_NAME=Your Company
LOGO_URL=/assets/logo.png

# Feature Flags
FEATURE_OTP_ENABLED=true
FEATURE_EMAIL_VERIFICATION_ENABLED=true
FEATURE_CORPORATE_APPROVALS_ENABLED=true
CLOSED_REGISTRATION=false

# File Upload Configuration
UPLOAD_DIRECTORY=./uploads
MAX_UPLOAD_SIZE=52428800

# Logo & Watermark Configuration
# Logo URL is served via /assets static mount
WATERMARK_IMAGE_PATH=./assets/logo.png
```

### Frontend (.env)
```env
# Backend API Base URL (without /api/v1 suffix)
VITE_BACKEND_URL=http://localhost:8000

# API URL (full path to API endpoints)
VITE_API_URL=http://localhost:8000/api/v1
```

### Frontend (.env.production)
```env
# Production backend URL
VITE_BACKEND_URL=https://api.yourdomain.com
VITE_API_URL=https://api.yourdomain.com/api/v1
```

**Important Notes:**
- `LOGO_URL` is a URL path (e.g., `/assets/logo.png`), served via backend static mount
- `WATERMARK_IMAGE_PATH` is a file system path (e.g., `./assets/logo.png`), relative to backend directory
- Frontend automatically fetches logo URL from backend config endpoint
- Favicons are loaded dynamically from `/assets/favicons/` using `VITE_BACKEND_URL`

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

GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later) - See `LICENSE` for details.

## Support

For issues or questions:
1. Check the [Installation Guide](install.md)
2. Review API Documentation
3. Create an issue in the project Git repository (to be published)

## Author

Your Company

---

**Version:** 1.0.0  
**Last Updated:** 2026-02-28
