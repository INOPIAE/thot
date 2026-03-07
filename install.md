# NLF Database Application Setup Guide

## Prerequisites

- Python 3.9+
- Node.js 16+
- PostgreSQL 12+
- Visual Studio Code

## Project Structure

```
nlf/db/
├── backend/           # Python FastAPI backend
│   ├── app/          # Main application code
│   │   ├── models/   # SQLAlchemy models
│   │   ├── routes/   # API routes
│   │   ├── schemas/  # Pydantic schemas
│   │   ├── services/ # Business logic
│   │   └── utils/    # Utilities
│   ├── tests/        # Unit tests
│   ├── scripts/      # Initialization scripts
│   ├── config.py     # Configuration
│   ├── requirements.txt
│   └── package.json
│
├── frontend/          # Vue.js frontend
│   ├── src/
│   │   ├── components/  # Vue components
│   │   ├── views/       # Page views
│   │   ├── stores/      # Pinia stores
│   │   ├── services/    # API services
│   │   ├── locales/     # i18n translations
│   │   └── config/      # Frontend config
│   ├── tests/          # Unit tests
│   ├── package.json
│   └── vite.config.js
│
└── .gitignore        # Git ignore rules
```

## Backend Setup

### 1. Install PostgreSQL

**Windows:**
- Download from https://www.postgresql.org/download/windows/
- Create a database for development and testing:

```sql
-- As postgres user
CREATE USER nlf_user WITH PASSWORD 'nlf_password';
CREATE DATABASE nlf_db OWNER nlf_user;
CREATE DATABASE nlf_db_test OWNER nlf_user;
ALTER ROLE nlf_user SET client_encoding TO 'utf8';
ALTER ROLE nlf_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE nlf_user SET default_transaction_deferrable TO on;
```

### 2. Create Python Virtual Environment

```bash
cd backend
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3.5. Install Poppler (Required for PDF Thumbnails)

The application uses `pdf2image` for generating PDF thumbnails with watermarks, which requires Poppler to be installed on your system.

**Windows:**
1. Download Poppler for Windows from: https://github.com/oschwartz10612/poppler-windows/releases/
2. Extract the ZIP file to a location (e.g., `C:\Program Files\poppler`)
3. Add the `bin` folder to your PATH environment variable:
   - Right-click "This PC" → Properties → Advanced system settings
   - Click "Environment Variables"
   - Under "System variables", find "Path" and click "Edit"
   - Add new entry: `C:\Program Files\poppler\Library\bin`
   - Click OK and restart your terminal

**Alternative (using Chocolatey):**
```bash
choco install poppler
```

**macOS (using Homebrew):**
```bash
brew install poppler
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install poppler-utils
```

**Verify Installation:**
```bash
pdftoppm -h
```
If successful, you should see the help output for pdftoppm.

### 4. Configure Environment Variables

Create `.env` file in `backend/` directory:

```env
# Environment
ENVIRONMENT=development

# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=nlf_user
DB_PASSWORD=nlf_password
DB_NAME=nlf_db

# Secret Key (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
SECRET_KEY=your-secret-key-here

# SMTP Configuration (Gmail example)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@nlfdatabase.com
SMTP_FROM_NAME=NLF Database

# Frontend URL
FRONTEND_URL=http://localhost:3000

# CORS
CORS_ORIGINS=http://localhost:3000

# File Upload Configuration
UPLOAD_DIRECTORY=./uploads
MAX_UPLOAD_SIZE=52428800

# Watermark Configuration (optional)
# Path to logo image to include in PDF watermarks
# WATERMARK_IMAGE_PATH=./assets/logo.png

# Logging
LOG_LEVEL=INFO
```

### 5. (Optional) Configure Logo and Favicons

#### Application Logo (Header & Watermarks)

If you want to include your company logo in the application header and PDF watermarks:

1. **Create assets directory:**
   ```bash
   mkdir backend/assets
   ```

2. **Place your logo** (PNG recommended for transparency):
   ```
   backend/assets/logo.png
   ```

3. **Configure in `.env`:**
   ```env
   # Logo URL (served via /assets mount point)
   LOGO_URL=/assets/logo.png
   
   # Watermark logo path (for PDF overlay)
   WATERMARK_IMAGE_PATH=./assets/logo.png
   ```

Logo specifications:
- Recommended size: 100-200px width for header, proportionally scaled for watermarks
- Formats: PNG (with alpha channel for transparency), JPEG, GIF
- Logo is served via FastAPI's `/assets` static mount point
- Frontend fetches logo URL from backend config endpoint

#### Favicons

1. **Place favicons** in the assets directory:
   ```bash
   mkdir backend/assets/favicons
   ```

2. **Add favicon files:**
   ```
   backend/assets/favicons/
   ├── favicon.ico
   ├── favicon-16x16.png
   ├── favicon-32x32.png
   ├── favicon-96x96.png
   ├── apple-icon-*.png
   ├── android-icon-192x192.png
   ├── ms-icon-*.png
   └── manifest.json
   ```

3. **Configuration:**
   - Favicons are automatically loaded from backend `/assets/favicons/` endpoint
   - Frontend loads favicons dynamically using `VITE_BACKEND_URL` environment variable
   - No hardcoded URLs needed in HTML

**How it works:**
- Backend serves static files via `/assets` mount (configured in `app/__init__.py`)
- Frontend utility `src/utils/favicon.js` dynamically injects favicon links at runtime
- URLs are environment-specific (dev: `http://localhost:8000`, prod: from `.env.production`)

### 6. Initialize Database

```bash
python scripts/init_db.py
```

This will:
- Create all database tables
- Seed default roles and permissions
- Create default restrictions (none, confidential, locked, privacy)
- Create default work statuses (not yet, running, finished)

### 7. Create Upload Directory

The application stores uploaded PDF files in the filesystem. Create the upload directory:

```bash
# Create directory
mkdir uploads

# On Windows:
# md uploads
```

The directory structure will be automatically managed:
```
uploads/
  └── {record_id}/
      └── {page_id}.pdf
```

> **Note:** Make sure the directory has appropriate permissions for the backend process to write files.

### 8. Test Email Configuration

Before running the application, test your SMTP configuration:

```bash
# Test with default recipient (SMTP_USER email)
python scripts/test_email.py

# Test with custom recipient
python scripts/test_email.py your-email@example.com
```

This script will:
1. **Validate Configuration** - Check if SMTP credentials are set
2. **Test Connection** - Connect to SMTP server (TLS/SSL)
3. **Send Test Email** - Send a sample email to verify delivery

**Expected output on success:**
```
============================================================
✅ ALL TESTS PASSED - Email configuration is working!
============================================================
```

**Common SMTP Configurations:**

| Provider | Server | Port | Security |
|----------|--------|------|----------|
| Gmail | smtp.gmail.com | 587 | TLS |
| Office 365 | smtp.office365.com | 587 | TLS |
| Postfix (local) | localhost | 25 | None |
| STRATO | smtp.strato.de | 465 | SSL |

> **Note:** The `SMTP_FROM_EMAIL` must match your authenticated SMTP account email address.

### 9. Run Development Server

```bash
python -m app.main
# or
uvicorn app.main:app --reload
```

Server will be available at: http://localhost:8000

**API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 7. Run Backend Tests

```bash
pytest tests/ -v --cov=app
```

OR

```bash
pytest tests/ -v --cov=app --watch
```

## Frontend Setup

### 1. Install Node Dependencies

> **Node version**
> Vite 7+ requires Node 20.19 or later (or ≥22.12). If you see an `EBADENGINE` warning
> you can either upgrade Node or adjust `package.json` to use `vite@^5`.

```bash
cd frontend
npm install
```

### 2. Create Environment Configuration

Create `.env` file in `frontend/` directory:

```env
# Backend API Base URL (without /api/v1 suffix)
VITE_BACKEND_URL=http://localhost:8000

# API URL (full path to API endpoints)
VITE_API_URL=http://localhost:8000/api/v1
```

**For Production:**

Create `.env.production` file:

```env
# Backend API Base URL (replace with your production domain)
VITE_BACKEND_URL=https://api.yourdomain.com

# API URL (full path to API endpoints)
VITE_API_URL=https://api.yourdomain.com/api/v1
```

These environment variables are used for:
- API calls to backend
- Loading logo from backend `/assets/logo.png`
- Loading favicons from backend `/assets/favicons/`
- Dynamic configuration at build time via Vite

### 3. Run Development Server

```bash
npm run dev
```

Application will be available at: **http://localhost:5173**

The frontend will automatically fetch configuration from the backend at startup via:
- `GET http://localhost:8000/api/v1/config`

### 4. Run Frontend Tests

```bash
npm run test
```

> **Security audit**
> After installing dependencies run `npm audit` and optionally `npm audit fix` or
> `npm audit fix --force` to resolve vulnerabilities. Be cautious: forced
> upgrades can introduce breaking changes.


With UI:
```bash
npm run test:ui
```

With coverage:
```bash
npm run test:coverage
```

### 5. Build for Production

```bash
npm run build
```

## VS Code Setup

### Recommended Extensions

Install these extensions in VS Code:

1. **Python**
   - ms-python.python
   - ms-python.vscode-pylance

2. **Vue**
   - Vue.volar
   - vue-official.vue

3. **Database**
   - cweijan.vscode-postgresql

4. **Code Quality**
   - dbaeumer.vscode-eslint
   - ms-python.flake8
   - charliermarsh.ruff

5. **Utilities**
   - REST Client
   - Thunder Client
   - Postman

### VS Code Workspace Settings

Create `.vscode/settings.json`:

```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.python"
  },
  "[vue]": {
    "editor.defaultFormatter": "Vue.volar"
  },
  "[javascript]": {
    "editor.defaultFormatter": "dbaeumer.vscode-eslint"
  }
}
```

### Debug Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload"],
      "console": "integratedTerminal",
      "jinja": true,
      "justMyCode": false,
      "cwd": "${workspaceFolder}/backend"
    },
    {
      "name": "Frontend: Debug",
      "type": "firefox",
      "request": "launch",
      "url": "http://localhost:3000",
      "pathMapping": {
        "/": "${workspaceFolder}/frontend/",
        "/src/": "${workspaceFolder}/frontend/src/"
      }
    }
  ]
}
```

## Running Both Backend and Frontend

### Option 1: Separate Terminals

**Terminal 1 - Backend:**
```bash
cd backend
venv\Scripts\activate  # Windows
python -m app.main
```

Backend will be available at: **http://localhost:8000**

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Frontend will be available at: **http://localhost:5173**

### Option 2: Using Docker Compose

Ensure Docker and Docker Compose are installed, then:

```bash
docker-compose up
```

This will start:
- PostgreSQL database at `localhost:5432`
- Backend at `http://localhost:8000`
- Frontend at `http://localhost:3000`

**Optional: Build without cache**
```bash
docker-compose up --build --no-cache
```

Services will be available at:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Database: localhost:5432

**Stop services:**
```bash
docker-compose down
```

**Stop services and remove volumes:**
```bash
docker-compose down -v
```

### Option 3: Using VS Code Tasks

Create `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Backend: Start Server",
      "type": "shell",
      "command": "cd backend && source venv/bin/activate && python -m app.main",
      "isBackground": true,
      "problemMatcher": {
        "pattern": {
          "regexp": "^.*$",
          "file": 1,
          "location": 2,
          "message": 3
        },
        "background": {
          "activeOnStart": true,
          "beginsPattern": "^Uvicorn running.*",
          "endsPattern": "^Application startup complete"
        }
      }
    },
    {
      "label": "Frontend: Start Dev Server",
      "type": "shell",
      "command": "cd frontend && npm run dev",
      "isBackground": true,
      "problemMatcher": {
        "pattern": {
          "regexp": "^.*$"
        },
        "background": {
          "activeOnStart": true,
          "beginsPattern": "^  Local:.*",
          "endsPattern": "^ready in.*"
        }
      }
    },
    {
      "label": "Backend: Run Tests",
      "type": "shell",
      "command": "cd backend && source venv/bin/activate && pytest tests/ -v",
      "group": {
        "kind": "test",
        "isDefault": true
      }
    },
    {
      "label": "Frontend: Run Tests",
      "type": "shell",
      "command": "cd frontend && npm run test",
      "group": {
        "kind": "test"
      }
    }
  ]
}
```

Run tasks with: `Ctrl+Shift+P` → "Tasks: Run Task"

## Application Configuration

The application configuration is loaded from the backend at startup.

### Frontend Configuration Loading

1. When the frontend starts, it initializes the app store
2. The store fetches configuration from `GET /api/v1/config`
3. All app settings are available in the Pinia store: `useAppStore()`

### Backend Configuration

Edit `backend/config.py` or set environment variables to customize:

```python
# Application
APP_NAME = "NLF Database"
APP_VERSION = "1.0.0"
COMPANY_NAME = "Your Company"
LOGO_URL = "/static/logo.png"
COPYRIGHT_YEAR = 2026

# Security
TOKEN_REFRESH_INTERVAL_MINUTES = 55
SESSION_TIMEOUT_MINUTES = 60

# UI
ITEMS_PER_PAGE_DEFAULT = 10
ITEMS_PER_PAGE_OPTIONS = [10, 20, 50]

# Features
FEATURE_OTP_ENABLED = True
FEATURE_EMAIL_VERIFICATION_ENABLED = True
FEATURE_CORPORATE_APPROVALS_ENABLED = True

# Languages
DEFAULT_LANGUAGE = "en"
```

### Accessing Configuration in Frontend

```javascript
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()

// Get specific config value
const appName = appStore.getConfig('appName', 'NLF Database')
const itemsPerPage = appStore.getConfig('itemsPerPageDefault', 10)

// Get entire config object
const config = appStore.config
```

## Application Configuration

Alembic is integrated into the backend for managing database schema changes.

### Initial Database Setup

1. **Install dependencies** (already in `requirements.txt`):

    ```bash
    cd backend
    pip install -r requirements.txt
    ```

2. **Initialize the database** (runs Alembic migrations automatically):

    ```bash
    python scripts/init_db.py
    ```

    This will:
    - Run all pending Alembic migrations to create tables
    - Seed default roles and permissions
    - Create `alembic_version` table to track migration state

### Creating New Migrations

> **Note:** Alembic uses timezone-aware datetimes for generation and needs `python-dateutil` (>= 2.9.0).
> Make sure it is installed (added to `requirements.txt`).

After making changes to your models, generate a new migration:

```bash
cd backend
pip install -r requirements.txt   # ensure dateutil is present
alembic revision --autogenerate -m "description of your changes"
```

Example:
```bash
alembic revision --autogenerate -m "add user verification fields"
```

A new migration file will be created in `alembic/versions/`.

### Applying Migrations

Apply all pending migrations to the database:

```bash
alembic upgrade head
```

### Downgrading

If you need to rollback to a previous version:

```bash
alembic downgrade -1         # Downgrade one migration
alembic downgrade -2         # Downgrade two migrations
alembic downgrade revision   # Downgrade to specific revision
```

### See Current Migration Status

```bash
alembic current              # Show current database revision
alembic history              # Show migration history
```

### Migration Files

Migration files are stored in `backend/alembic/versions/` with naming pattern:
```
001_initial_migration.py
002_add_user_fields.py
003_create_audit_table.py
```

Each migration file has:
- `upgrade()` - Operations to apply when migrating forward
- `downgrade()` - Operations to reverse when downgrading

See the [Alembic Documentation](https://alembic.sqlalchemy.org/) for advanced usage.

---

## Using the Application

### First Steps After Setup

1. **Start both servers** (Backend and Frontend)
2. **Open the frontend** in your browser: http://localhost:5173
3. **Register a new account**
   - The first user will automatically receive the **admin** role
   - Subsequent users receive the **user** role
4. **Check your email** for the verification link
5. **Complete registration** by setting your password

### Working with Records

Records are the primary data entities in the system.

#### Creating a Record

1. Navigate to **Records** in the main menu
2. Click **Create Record**
3. Fill in the form:
   - **Title** (required): Main identifier for the record
   - **Signature**: Optional reference number
   - **Description**: Detailed information about the record
   - **Comment**: Additional notes
   - **Keywords (Names)**: Comma-separated list (e.g., "Müller, Schmidt, Meyer")
   - **Keywords (Locations)**: Comma-separated list (e.g., "Berlin, München, Hamburg")
   - **Restriction**: Access control level (none, confidential, locked, privacy)
   - **Work Status**: Current status (not yet, running, finished)
4. Click **Save**

#### Searching Records

Use the search fields to filter records:
- **Title Search**: Full-text search in titles
- **Signature Search**: Search by signature/reference number
- **Keyword Search**: Uses phonetic search algorithms
  - Cologne Phonetic (optimized for German names)
  - Double Metaphone (optimized for English)

This enables fuzzy matching (e.g., "Müller" will also find "Mueller" or "Muller").

### Working with Pages

Pages belong to records and can contain PDF documents.

#### Adding a Page to a Record

1. Open a record (click **Edit** in the records list)
2. Click **Manage Pages** button
3. Click **Add Page** on the pages overview
4. Fill in the form:
   - **Page Name** (required): Identifier for this page
   - **Description**: Brief description
   - **Page Content**: Text transcription of the document
   - **Comment**: Additional notes
   - **Upload PDF File**: Select a PDF file (max 50MB)
   - **Restriction**: Access control level
   - **Work Status**: Current status
5. Click **Save**

#### Viewing Pages

From the pages list, you can:
- **View**: See all page details (text only, no PDF display)
- **Edit**: Modify page information or upload a new PDF
- **Delete**: Remove the page (soft delete, can be restored by admin)

#### Accessing PDF Files

PDF files are stored in the backend filesystem:
```
backend/uploads/{record_id}/{page_id}.pdf
```

They are accessible via:
```
http://localhost:8000/uploads/{record_id}/{page_id}.pdf
```

> **Note:** The overview page shows only text information. To view the actual PDF, you would need to implement a separate viewer page (not included in basic setup).

### User Management (Admin/Support Only)

Admins and support staff can:
- View all registered users
- Edit user details
- Approve corporate memberships
- Reset user passwords
- Activate/deactivate accounts

Access via: **Administration** → **User Management**

### Role Management (Admin/Support Only)

Manage user roles and permissions:
- Assign roles to users
- Create new roles
- Configure role permissions

Access via: **Administration** → **Roles**

---

## Troubleshooting

### Backend Issues

**ModuleNotFoundError: No module named 'app'**
- Make sure you're in the backend directory
- Ensure virtual environment is activated

**Database Connection Error**
- Check PostgreSQL is running
- Verify database credentials in .env
- Ensure databases exist (nlf_db and nlf_db_test)

**SMTP Connection Error**
- For Gmail, use App Password (not regular password)
- Enable Less Secure App Access or use App Passwords
- Check SMTP_PORT (usually 587 for TLS)

### Frontend Issues

**npm ERR! code ERESOLVE**
- Try: `npm install --legacy-peer-deps`

**Vite port already in use**
- Kill process on port 3000 or specify different port

**Compilation errors in Vue components**
- Check Vue 3 and Volar compatibility
- Reload VS Code window

## Testing

### Backend Unit Tests

```bash
cd backend
pytest tests/ -v                    # Run all tests
pytest tests/test_user_service.py   # Run specific test file
pytest tests/ -v --cov=app          # With coverage
```

### Frontend Unit Tests

```bash
cd frontend
npm run test                        # Run tests
npm run test:ui                     # Run with UI
npm run test:coverage               # Run with coverage
```

## Security Notes

⚠️ **Important:**

1. **Change default SECRET_KEY** in production
2. **Never commit .env files** - use .env.example
3. **Use HTTPS in production**
4. **Implement proper CORS** - don't allow all origins
5. **Use strong database passwords**
6. **Enable database backups**
7. **Implement rate limiting** for API endpoints
8. **Regular security updates** for dependencies

## Production Deployment

For production deployment, refer to:
- FastAPI: https://fastapi.tiangolo.com/deployment/
- Vue.js: https://vitejs.dev/guide/ssr.html
- PostgreSQL: https://www.postgresql.org/docs/current/sql-createdatabase.html

## Support

For issues or questions, create a GitHub Issue or contact support.
