# Development Guide - NLF Database Application

This guide provides essential information for developers working on the NLF Database project.

## Quick Start for New Developers

### 1. Clone and Setup Backend

```bash
cd backend
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure .env
copy .env.example .env
# Edit .env with your local database credentials
```

### 1.5. Install Poppler (Required for PDF Thumbnails)

The application requires Poppler for generating PDF thumbnails with watermarks.

**Windows:**
```bash
# Using Chocolatey:
choco install poppler

# Or download from:
# https://github.com/oschwartz10612/poppler-windows/releases/
# Extract and add bin folder to PATH
```

**macOS:**
```bash
brew install poppler
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install poppler-utils
```

**Verify installation:**
```bash
pdftoppm -h
```

### 2. Setup Frontend

```bash
cd frontend
npm install

# Create .env.local
cat > .env.local << EOF
VITE_BACKEND_URL=http://localhost:8000
VITE_ROOT_MOUNT=
EOF
```

### 3. Initialize Database

```bash
cd backend
python scripts/init_db.py
```

This will:
- Run Alembic migrations to create tables
- Seed default roles and permissions

### 4. Start Development Servers

**Terminal 1 - Backend:**
```bash
cd backend
python -m app.main
# Server: http://localhost:8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
# App: http://localhost:5173
```

---

## Application Configuration

### How It Works

The frontend loads configuration from the backend at startup:

1. **Frontend** starts → calls `useAppStore().initializeConfig()`
2. **Backend** endpoint: `GET /api/v1/config` is called
3. **Configuration** is loaded from `backend/config.py` and cached in Pinia store
4. **Components** access config via `appStore.getConfig(key)`

### Configuration Endpoint

```
GET /api/v1/config
```

Returns public application configuration:
```json
{
  "appName": "NLF Database",
  "appVersion": "1.0.0",
  "companyName": "Your Company",
  "logoUrl": "/static/logo.png",
  "copyrightYear": 2026,
  "itemsPerPageDefault": 10,
  "itemsPerPageOptions": [10, 20, 50],
  "tokenRefreshIntervalMinutes": 55,
  "sessionTimeoutMinutes": 60,
  "features": {
    "otp": true,
    "emailVerification": true,
    "corporateApprovals": true
  },
  "languages": {
    "en": "English",
    "de": "Deutsch"
  },
  "defaultLanguage": "en"
}
```

---

## Records & Pages Management

### Working with Records

Records are the primary data entities. Each record can have:
- Title, signature, description
- Keywords for names (with phonetic search)
- Keywords for locations (with phonetic search)
- Multiple pages with PDF files
- Access restrictions
- Work status tracking

#### Creating a Record

```javascript
// Frontend
import { recordService } from '@/services/record'

const newRecord = await recordService.createRecord({
  title: 'Archive Document 001',
  signature: 'ARC-2026-001',
  description: 'Historical document from 1920',
  keywords_names: 'Müller, Schmidt, Meyer',  // Comma-separated
  keywords_locations: 'Berlin, München, Hamburg',
  restriction_id: restrictionId,  // UUID
  workstatus_id: workstatusId    // UUID
})
```

#### Phonetic Search

Keywords are automatically indexed with:
- **Cologne Phonetic** (c_search) - German-optimized
- **Double Metaphone** (dblmeta_1, dblmeta_2) - English-optimized

This enables fuzzy search for names and locations.

### Working with Pages

Pages belong to records and can contain PDF files.

#### Creating a Page with PDF Upload

```javascript
// Frontend
import { pageService } from '@/services/page'

const formData = {
  name: 'Page 1',
  description: 'First page of the document',
  page: 'Transcribed text content',
  comment: 'Needs review',
  record_id: recordId,
  restriction_id: restrictionId,
  workstatus_id: workstatusId,
  file: pdfFile  // File object from <input type="file">
}

const newPage = await pageService.createPage(formData)
```

#### File Upload Configuration

Files are stored in the filesystem:
```
backend/uploads/
  └── {record_id}/
      └── {page_id}.pdf
```

Configuration in `.env`:
```env
UPLOAD_DIRECTORY=./uploads
MAX_UPLOAD_SIZE=52428800  # 50MB in bytes
```

The `location_file` field in the database stores the relative path: `{record_id}/{page_id}.pdf`

#### Accessing Uploaded Files

⚠️ **Security Note:** Direct access to uploaded files via `/uploads/` is deprecated for security reasons. Always use the watermarked endpoints for viewing and downloading PDFs.

---

### PDF Watermarking System

The application automatically adds watermarks to all PDFs when viewed or downloaded. This ensures document security and traceability.

#### Watermark Content

Every watermarked PDF includes:

1. **Diagonal Background**: Large "CONFIDENTIAL" text across the page
2. **Header Badge** (top-left):
   - Optional company logo (configurable via `WATERMARK_IMAGE_PATH`)
   - "CONFIDENTIAL" label
   - Username of the viewer
   - Download timestamp (YYYY-MM-DD HH:MM)
3. **Record Information** (top-right):
   - Record name
   - Record signature
   - Page identifier

#### API Endpoints for Watermarked Content

**View PDF with Watermark (inline):**
```
GET /api/v1/pages/{page_id}/view-pdf
Authorization: Bearer {token}
```
Returns: PDF with watermark for browser viewing

**Download PDF with Watermark:**
```
GET /api/v1/pages/{page_id}/download-watermarked
Authorization: Bearer {token}
```
Returns: PDF with watermark as file download

**Get Thumbnail with Watermark:**
```
GET /api/v1/pages/{page_id}/thumbnail?width=200
Authorization: Bearer {token}
```
Returns: JPEG thumbnail of first page with watermark

Query Parameters:
- `width`: Thumbnail width in pixels (default: 200, min: 50, max: 800)

#### Frontend Usage

```javascript
// Import page service
import { pageService } from '@/services/page'

// Load PDF for viewing
const pdfBlob = await pageService.getViewPdf(pageId)
const pdfUrl = URL.createObjectURL(pdfBlob)

// Load thumbnail
const thumbnailBlob = await pageService.getThumbnail(pageId, 300)
const thumbnailUrl = URL.createObjectURL(thumbnailBlob)

// Remember to revoke URLs to prevent memory leaks
URL.revokeObjectURL(pdfUrl)
URL.revokeObjectURL(thumbnailUrl)
```

#### Complete Example: PageViewer Component

```vue
<template>
  <div>
    <!-- Thumbnail -->
    <img :src="thumbnailUrl" alt="Thumbnail" />
    
    <!-- PDF Viewer -->
    <iframe :src="pdfUrl" type="application/pdf"></iframe>
  </div>
</template>

<script>
import { pageService } from '@/services/page'

export default {
  data() {
    return {
      pdfUrl: null,
      thumbnailUrl: null,
    }
  },
  async mounted() {
    // Load PDF and thumbnail
    const pdfBlob = await pageService.getViewPdf(this.pageId)
    this.pdfUrl = URL.createObjectURL(pdfBlob)
    
    const thumbBlob = await pageService.getThumbnail(this.pageId, 250)
    this.thumbnailUrl = URL.createObjectURL(thumbBlob)
  },
  beforeUnmount() {
    // Clean up blob URLs
    if (this.pdfUrl) URL.revokeObjectURL(this.pdfUrl)
    if (this.thumbnailUrl) URL.revokeObjectURL(this.thumbnailUrl)
  },
}
</script>
```

#### Watermark Configuration

Configure watermark appearance in `backend/config.py`:

```python
# Optional watermark image (company logo)
WATERMARK_IMAGE_PATH = os.getenv('WATERMARK_IMAGE_PATH', None)

@staticmethod
def get_watermark_image_path():
    """Return Path object for watermark image or None."""
    if config.WATERMARK_IMAGE_PATH:
        path = Path(config.WATERMARK_IMAGE_PATH)
        if path.exists() and path.is_file():
            return path
    return None
```

Place your logo image at the configured path, e.g.:
```
backend/assets/logo.png
```

And set in `.env`:
```env
WATERMARK_IMAGE_PATH=./assets/logo.png
```

Supported formats: PNG, JPEG, GIF (PNG with transparency recommended)

#### Backend Implementation

The watermark service uses:
- **ReportLab** - Generate PDF overlays with text and images
- **PyPDF** - Merge watermark with original PDF
- **pdf2image** + **Pillow** - Generate thumbnails from PDFs
- **Poppler** - Convert PDF pages to images (system dependency)

Key service methods in `backend/app/services/pdf_watermark_service.py`:
- `create_watermarked_pdf()` - Add watermark to all pages
- `create_thumbnail_with_watermark()` - Generate first-page thumbnail with overlay

#### Security Considerations

✅ **Benefits:**
- Every viewed/downloaded PDF is user-specific
- Audit trail: Username + timestamp on every document
- No direct file access without authentication
- Blob URLs prevent caching in browser

⚠️ **Important:**
- Watermarks are generated on-the-fly (performance consideration for large PDFs)
- Consider caching watermarked versions for frequently accessed documents
- Rate limiting recommended for public-facing instances

### Modifying Configuration

1. **Edit** `backend/config.py`:
   ```python
   APP_NAME = "My Company Database"
   COMPANY_NAME = "My Company"
   ```

2. **Backend restarts automatically** (in development with `--reload`)

3. **Frontend fetches new config** on next app reload - no code changes needed!

---

## Database Migrations with Alembic

### Standard Workflow

#### 1. Modify a Model

Edit any model file in `backend/app/models/`:

```python
# backend/app/models/user.py
class User(BaseModel):
    __tablename__ = "users"
    
    # ... existing fields ...
    
    # Add new field:
    phone_number = Column(String(20), nullable=True)
```

#### 2. Generate Migration

```bash
cd backend
alembic revision --autogenerate -m "add phone field to users"
```

This creates a new file in `alembic/versions/` with:
- `upgrade()` - SQL operations to apply the change
- `downgrade()` - SQL operations to reverse the change

#### 3. Review Migration

**Always review the generated migration before applying!**

```bash
cat alembic/versions/002_add_phone_field_to_users.py
```

Look for:
- Correct table names
- Correct column names and types
- Foreign key constraints
- Index definitions

#### 4. Apply Migration

```bash
alembic upgrade head
```

This runs all pending migrations. You'll see output like:

```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 002_...
```

#### 5. Test the Changes

Run your test suite:

```bash
# Backend tests
pytest tests/ -v

# Frontend tests
npm run test
```

---

### Common Migration Scenarios

#### Adding a New Column

```bash
alembic revision --autogenerate -m "add email verification field"
```

Generated migration looks like:
```python
def upgrade():
    op.add_column('users', 
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false')
    )

def downgrade():
    op.drop_column('users', 'email_verified')
```

#### Removing a Column

```bash
alembic revision --autogenerate -m "remove deprecated field"
```

Generated migration:
```python
def upgrade():
    op.drop_column('users', 'deprecated_field')

def downgrade():
    op.add_column('users',
        sa.Column('deprecated_field', sa.String(255), nullable=True)
    )
```

#### Renaming a Column

```bash
alembic revision --autogenerate -m "rename username to login"
```

#### Creating a New Table

Add the model file to `backend/app/models/`, then:

```bash
alembic revision --autogenerate -m "create audit log table"
```

#### Adding Index or Constraint

Modify model relationships/constraints, then:

```bash
alembic revision --autogenerate -m "add unique constraint on email"
```

---

### Migration Management

#### View Current Revision

```bash
alembic current
# Output: 002_add_phone_field_to_users
```

#### View Migration History

```bash
alembic history
# Output:
# <base> -> 001_initial_migration, create users and roles tables
# 001_initial_migration -> 002_add_phone_field_to_users, add phone field to users
```

#### Downgrade One Migration

```bash
alembic downgrade -1
```

Data loss warning: Downgrades may lose data depending on the migration!

#### Downgrade to Specific Revision

```bash
alembic downgrade 001_initial_migration
```

---

### Troubleshooting Migrations

#### "No changes detected in models"

**Cause:** Alembic can't find differences between models and database.

**Solutions:**
1. Ensure model changes are saved
2. Check `alembic/env.py` correctly imports `target_metadata`
3. Verify the model is imported in `app/models/__init__.py`

#### "Could not locate a marked branch point"

**Cause:** Migration history is inconsistent.

**Solution:** Check `alembic_version` table:
```bash
psql nlf_db -c "SELECT * FROM alembic_version;"
```

#### Migration fails with SQL error

**Cause:** Generated SQL may need manual adjustment.

**Solution:**
1. Edit the `.py` file in `alembic/versions/`
2. Modify the SQL in `upgrade()` or `downgrade()`
3. Re-run: `alembic upgrade head`

---

## Running Tests

### Backend Unit Tests

```bash
cd backend

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_user_service.py -v

# Run with coverage
pytest tests/ -v --cov=app

# Run with markers
pytest tests/ -v -m "not slow"
```

### Frontend Unit Tests

```bash
cd frontend

# Run tests
npm run test

# Run with UI
npm run test:ui

# Run with coverage
npm run test:coverage
```

---

## API Development

### Adding a New Endpoint

1. **Create route in `backend/app/routes/`:**

```python
# backend/app/routes/items.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import ItemResponse, ItemCreateRequest
from app.services import ItemService

router = APIRouter(prefix="/items", tags=["items"])

@router.get("", response_model=list[ItemResponse])
async def list_items(db: Session = Depends(get_db)):
    """List all items"""
    return ItemService.list_items(db)

@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    item: ItemCreateRequest,
    db: Session = Depends(get_db)
):
    """Create a new item"""
    return ItemService.create_item(db, item)
```

2. **Create schema in `backend/app/schemas/__init__.py`:**

```python
class ItemCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

class ItemResponse(ItemCreateRequest):
    id: UUID
    created_on: datetime
    
    class Config:
        from_attributes = True
```

3. **Create service in `backend/app/services/item_service.py`:**

```python
class ItemService:
    @staticmethod
    def list_items(db: Session) -> list:
        return db.query(Item).all()
    
    @staticmethod
    def create_item(db: Session, data: ItemCreateRequest) -> Item:
        item = Item(name=data.name, description=data.description)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
```

4. **Register route in `backend/app/routes/api.py`:**

```python
from app.routes import items

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(items.router)
```

5. **Create tests in `backend/tests/test_items.py`:**

```python
def test_list_items(client, db):
    response = client.get("/api/v1/items")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

---

## Frontend Development

### Project Structure

```
frontend/src/
├── components/       # Reusable Vue components
├── views/           # Page components (routed)
├── stores/          # Pinia state management
├── services/        # API services
├── locales/         # i18n translations
├── router/          # Vue Router configuration
└── App.vue          # Root component
```

### Creating a New Page

1. **Create view component:**

```vue
<!-- frontend/src/views/ItemsPage.vue -->
<template>
  <div class="items-page">
    <h1>{{ $t('items.title') }}</h1>
    
    <button @click="createItem">{{ $t('items.create') }}</button>
    
    <div v-if="items.length">
      <div v-for="item in items" :key="item.id" class="item-card">
        {{ item.name }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useItemStore } from '@/stores/items'

const itemStore = useItemStore()
const items = ref([])

onMounted(async () => {
  await itemStore.fetchItems()
  items.value = itemStore.items
})

const createItem = () => {
  // Handle create
}
</script>
```

2. **Create Pinia store:**

```js
// frontend/src/stores/items.js
import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as itemService from '@/services/items'

export const useItemStore = defineStore('items', () => {
  const items = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchItems() {
    loading.value = true
    try {
      items.value = await itemService.listItems()
    } catch (err) {
      error.value = err.message
    } finally {
      loading.value = false
    }
  }

  async function create(data) {
    return await itemService.createItem(data)
  }

  return { items, loading, error, fetchItems, create }
})
```

3. **Add route:**

```js
// frontend/src/router/index.js
const routes = [
  // ...
  {
    path: '/items',
    name: 'Items',
    component: () => import('@/views/ItemsPage.vue'),
    meta: { requiresAuth: true }
  }
]
```

4. **Add i18n translations:**

```js
// frontend/src/locales/messages.js
const messages = {
  en: {
    items: {
      title: 'Items',
      create: 'Create Item'
    }
  },
  de: {
    items: {
      title: 'Elemente',
      create: 'Element erstellen'
    }
  }
}
```

---

## API Endpoints Reference

### Authentication & Users

#### Authentication
- `POST /api/v1/auth/register` - Register new user
- `GET /api/v1/auth/register/confirm/{token}` - Confirm registration
- `POST /api/v1/auth/login` - Login with username/password
- `POST /api/v1/auth/password-reset` - Request password reset
- `POST /api/v1/auth/password-reset/confirm/{token}` - Confirm password reset

#### User Profile
- `GET /api/v1/users/profile` - Get current user profile
- `PUT /api/v1/users/profile` - Update profile (first name, last name, language)
- `POST /api/v1/users/password-change` - Change password
- `POST /api/v1/users/email-change` - Request email change
- `POST /api/v1/users/email-change/confirm/{token}` - Confirm email change

#### User Management (Admin/Support)
- `GET /api/v1/users` - List all users (with pagination and filters)
- `GET /api/v1/users/{user_id}` - Get user details
- `PUT /api/v1/users/{user_id}` - Update user (support/admin)
- `POST /api/v1/users/{user_id}/password-reset` - Trigger password reset
- `PUT /api/v1/users/{user_id}/roles` - Update user roles

### Records Management

#### Records CRUD
- `GET /api/v1/records` - List all records
  - Query params: `title`, `signature`, `keywords_names`, `keywords_locations`, `skip`, `limit`
- `GET /api/v1/records/{record_id}` - Get record details
- `POST /api/v1/records` - Create new record
  - Body: `title`, `signature`, `description`, `comment`, `keywords_names`, `keywords_locations`, `restriction_id`, `workstatus_id`
- `PUT /api/v1/records/{record_id}` - Update record
- `DELETE /api/v1/records/{record_id}` - Delete record (soft delete)

#### Record Metadata
- `GET /api/v1/records/restrictions` - Get all restrictions
  - Returns: `none`, `confidential`, `locked`, `privacy`
- `GET /api/v1/records/workstatus` - Get all work statuses
  - Returns: `not yet`, `running`, `finished` (for area: record)

#### Example: Create Record

```bash
curl -X POST "http://localhost:8000/api/v1/records" \\
  -H "Authorization: Bearer {token}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "title": "Archive Document 2026-001",
    "signature": "ARC-2026-001",
    "description": "Historical document from Berlin",
    "keywords_names": "Müller, Schmidt",
    "keywords_locations": "Berlin, München",
    "restriction_id": "uuid-restriction-none",
    "workstatus_id": "uuid-workstatus-not-yet"
  }'
```

### Pages Management

#### Pages CRUD
- `GET /api/v1/pages` - List all pages
  - Query params: `record_id`, `name`, `skip`, `limit`
- `GET /api/v1/pages/{page_id}` - Get page details
- `POST /api/v1/pages` - Create new page with file upload
  - Content-Type: `multipart/form-data`
  - Fields: `name`, `description`, `page`, `comment`, `record_id`, `restriction_id`, `workstatus_id`, `file`
- `PUT /api/v1/pages/{page_id}` - Update page
  - Fields: Same as POST, plus `delete_file` (boolean)
- `DELETE /api/v1/pages/{page_id}` - Delete page (soft delete)

#### File Access
- `GET /uploads/{record_id}/{filename}` - Download uploaded PDF file

#### Example: Create Page with PDF Upload

```bash
curl -X POST "http://localhost:8000/api/v1/pages" \\
  -H "Authorization: Bearer {token}" \\
  -F "name=Page 1" \\
  -F "description=First page of document" \\
  -F "page=Transcribed text content" \\
  -F "record_id=uuid-record-id" \\
  -F "restriction_id=uuid-restriction-none" \\
  -F "file=@document.pdf"
```

#### Example: Update Page (Replace PDF)

```bash
curl -X PUT "http://localhost:8000/api/v1/pages/{page_id}" \\
  -H "Authorization: Bearer {token}" \\
  -F "name=Updated Page 1" \\
  -F "restriction_id=uuid-restriction-confidential" \\
  -F "file=@new_document.pdf"
```

### Configuration
- `GET /api/v1/config` - Get public application configuration

### Role Management (Admin only)
- `GET /api/v1/admin/roles` - List all roles
- `POST /api/v1/admin/roles` - Create new role
- `PUT /api/v1/admin/roles/{role_id}` - Update role
- `DELETE /api/v1/admin/roles/{role_id}` - Delete role

---

## Code Style & Quality

### Backend

**Format code with Black:**
```bash
black backend/app
```

**Sort imports with isort:**
```bash
isort backend/app
```

**Lint with flake8:**
```bash
flake8 backend/app --max-line-length=120
```

### Frontend

**Format with Prettier (if configured):**
```bash
npm run format
```

**Lint with ESLint:**
```bash
npm run lint
```

---

## Debugging

### Backend Debugging

**Print Debugging:**
```python
import logging
logger = logging.getLogger(__name__)

logger.debug(f"User ID: {user_id}")
logger.info("Processing started")
logger.warning("Potential issue")
logger.error(f"Error occurred: {str(e)}")
```

**VS Code Debugger:**

1. Set breakpoint by clicking line number
2. Launch "Python: FastAPI" from debug menu
3. Requests will pause at breakpoints

### Frontend Debugging

**Vue DevTools:**
- Install [Vue DevTools extension](https://devtools.vuejs.org/)
- Inspect component state and events

**Console Logging:**
```js
console.log('value:', value)
console.error('error:', error)
```

**VS Code Debugger:**
1. Install "Firefox Debugger" extension
2. Set breakpoints
3. Press F5 to launch Firefox with debugger

---

## Environment Variables

### Backend `.env`

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=nlf_user
DB_PASSWORD=your_password
DB_NAME=nlf_db

# Security
SECRET_KEY=your-secret-key-here

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=NLF Database

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### Frontend `.env.local`

```env
VITE_API_URL=http://localhost:8000/api/v1
```

---

## Common Development Tasks

### Reset Database (Development Only)

```bash
# Drop and recreate database
psql -U postgres -c "DROP DATABASE nlf_db;"
psql -U postgres -c "CREATE DATABASE nlf_db OWNER nlf_user;"

# Re-run migrations
python scripts/init_db.py
```

### View Database Tables

```bash
psql nlf_db -U nlf_user

# List tables
\dt

# Describe table
\d users

# View data
SELECT * FROM users;
```

### Create a Test User

```python
# In Python shell:
from app.services import UserService
from app.database import SessionLocal

db = SessionLocal()
user = UserService.create_user(
    db=db,
    username="testuser",
    email="test@example.com",
    password="TestPassword123!",
    is_first_user=False
)
print(f"Created user: {user.id}")
```

---

## API Testing - Watermarked PDFs

### Testing Watermark Endpoints

Once you have pages with uploaded PDFs, you can test the watermark endpoints.

#### 1. Get a Valid JWT Token

```bash
# Login to get access token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'

# Response includes: {"access_token": "eyJ0eXAi..."}
```

#### 2. List Pages to Get Page ID

```bash
curl -X GET http://localhost:8000/api/v1/pages \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Response includes array of pages with IDs
```

#### 3. Test Thumbnail Endpoint

```bash
# Get thumbnail with watermark (200px width)
curl -X GET "http://localhost:8000/api/v1/pages/{PAGE_ID}/thumbnail?width=200" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  --output thumbnail.jpg

# Get larger thumbnail (400px width)
curl -X GET "http://localhost:8000/api/v1/pages/{PAGE_ID}/thumbnail?width=400" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  --output thumbnail_large.jpg
```

#### 4. Test PDF View Endpoint

```bash
# Get PDF for viewing (inline)
curl -X GET "http://localhost:8000/api/v1/pages/{PAGE_ID}/view-pdf" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  --output view.pdf

# Open in browser (copy the URL with token)
# http://localhost:8000/api/v1/pages/{PAGE_ID}/view-pdf
```

#### 5. Test PDF Download Endpoint

```bash
# Download watermarked PDF
curl -X GET "http://localhost:8000/api/v1/pages/{PAGE_ID}/download-watermarked" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  --output watermarked_download.pdf
```

### Using httpie (Alternative)

If you have [httpie](https://httpie.io/) installed:

```bash
# Login
http POST :8000/api/v1/auth/login username=admin password=yourpass

# Get thumbnail (httpie automatically saves token if configured)
http GET :8000/api/v1/pages/{PAGE_ID}/thumbnail width==250 \
  Authorization:"Bearer YOUR_TOKEN" > thumb.jpg

# View PDF
http GET :8000/api/v1/pages/{PAGE_ID}/view-pdf \
  Authorization:"Bearer YOUR_TOKEN" > view.pdf
```

### Testing from Frontend

Open the browser DevTools Network tab when viewing a page to see:

```
Request URL: http://localhost:8000/api/v1/pages/{id}/view-pdf
Request Method: GET
Status Code: 200 OK
Content-Type: application/pdf

Request Headers:
  Authorization: Bearer eyJ0eXAiOi...
  
Response Headers:
  Content-Disposition: inline; filename="document_watermarked.pdf"
  Cache-Control: no-store, no-cache, must-revalidate
```

### Verifying Watermark Content

Open any downloaded/viewed PDF and verify it contains:

1. **Diagonal "CONFIDENTIAL"** text across pages
2. **Header badge** with:
   - Company logo (if configured)
   - Username (from JWT token)
   - Current timestamp
3. **Record information** (top-right):
   - Record name
   - Record signature
   - Page identifier

### Performance Testing

Test watermark generation speed:

```python
# backend/scripts/test_watermark_performance.py
import time
from pathlib import Path
from datetime import datetime
from app.services.pdf_watermark_service import (
    create_watermarked_pdf,
    create_thumbnail_with_watermark
)

pdf_path = Path("uploads/test-record/test.pdf")

# Test PDF watermarking
start = time.time()
pdf_bytes = create_watermarked_pdf(
    source_pdf=pdf_path,
    username="testuser",
    downloaded_at=datetime.now(),
    record_name="Test Record",
    record_signature="TEST-001",
    page_text="Page 1"
)
print(f"PDF watermark: {time.time() - start:.2f}s ({len(pdf_bytes) / 1024:.1f} KB)")

# Test thumbnail generation
start = time.time()
thumb_bytes = create_thumbnail_with_watermark(
    source_pdf=pdf_path,
    username="testuser",
    downloaded_at=datetime.now(),
    record_name="Test Record",
    record_signature="TEST-001",
    page_text="Page 1",
    thumbnail_width=300
)
print(f"Thumbnail: {time.time() - start:.2f}s ({len(thumb_bytes) / 1024:.1f} KB)")
```

Expected performance (depends on PDF size/complexity):
- **Small PDFs** (1-5 pages): 0.5-2 seconds
- **Medium PDFs** (10-20 pages): 2-5 seconds
- **Large PDFs** (50+ pages): 5-15 seconds
- **Thumbnails**: 0.3-1 second (first page only)

---

## Useful Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)
- [Vue 3 Documentation](https://vuejs.org/)
- [Pinia Store](https://pinia.vuejs.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

## Getting Help

1. Check the [install.md](install.md) for setup issues
2. Review the [README.md](README.md) for project overview
3. Look at existing tests for usage examples
4. Check Alembic history: `alembic history`
5. Ask senior developers or create GitHub issues

---

**Last Updated:** March 6, 2026

