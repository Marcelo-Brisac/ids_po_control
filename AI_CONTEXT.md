# AI Development Context - IDS PO Control

## Project Overview
**Status**: Active Development  
**Last Updated**: June 24, 2026  
**Current Phase**: Docker setup complete, ready for production deployment

## Tech Stack
- **Backend**: Django 5.x + Python 3.13
- **Database**: PostgreSQL 16 (Docker)
- **Static Files**: WhiteNoise for production serving
- **PDF Generation**: WeasyPrint
- **Deployment**: Docker + Docker Compose (2 containers)

## Architecture

### Containers
1. **ids_po_web** (Django + Gunicorn) - Port 8000
2. **ids_po_db** (PostgreSQL 16) - Port 5432

### Key Design Decisions

#### Database Structure
- **Issuer**: Can have multiple emails (separate IssuerEmail model) and multiple bank accounts
- **Supplier**: Can have multiple bank accounts with separate addresses (account_address field)
- **PO**: Links issuer and supplier, contains items and payment terms
- **Optional Fields**: tax_id is optional for both Issuer and Supplier
- **Field Naming**: Changed from "Requested Delivery Date" to "Lead Time Requested"

#### PDF Generation
- **Problem**: iframe-based PDF preview blocked by Microsoft Edge
- **Solution**: Created HTML preview page (po_pdf_view.html) that renders PO content directly
- **Implementation**: Separate template for browser viewing, WeasyPrint for PDF download
- **View**: po_pdf_view() passes all necessary data to HTML template

#### Static Files
- **Problem**: CSS files not loading in Docker container
- **Solution**: Added WhiteNoise middleware and CompressedManifestStaticFilesStorage
- **Configuration**: STATIC_URL = "/static/" with STATIC_ROOT = BASE_DIR / "staticfiles"

#### Authentication & Security
- **CSRF**: Dynamic CSRF middleware removed (not needed in Docker)
- **Cookies**: Configured for Docker environment (CSRF_COOKIE_SECURE=False for dev)
- **Hosts**: ALLOWED_HOSTS=["*"] for flexibility

## Database Schema

```
Issuer
├── id
├── name
├── address
├── tax_id (optional)
└── emails (1:N → IssuerEmail)

IssuerEmail
├── id
├── issuer_id (FK)
└── email

BankAccount (for Issuer)
├── id
├── issuer_id (FK)
├── account_number
├── account_currency
└── bank_name

Supplier
├── id
├── name
├── address
└── tax_id (optional)

SupplierBankAccount
├── id
├── supplier_id (FK)
├── account_address (separate from supplier address)
├── account_number
├── account_currency
└── bank_name

PO (Purchase Order)
├── id
├── po_number (unique)
├── contract_number
├── issued_at
├── issuer_id (FK)
├── supplier_id (FK)
├── requested_delivery_date (verbose_name="Lead Time Requested")
├── warranty
├── created_at
└── updated_at

POItem
├── id
├── po_id (FK)
├── commercial_model_name
├── description
├── quantity
├── unit_price
└── unit_price_currency

POPaymentTerm
├── id
├── po_id (FK)
├── event_name
├── percentage_due
└── expected_date
```

## Current Features

### Implemented
- [x] CRUD for Purchase Orders
- [x] CRUD for Issuers and Suppliers (via Django Admin)
- [x] Multiple emails per Issuer
- [x] Multiple bank accounts per Issuer/Supplier
- [x] PO Items (multiple items per PO)
- [x] Payment Terms (multiple terms per PO)
- [x] PDF generation and download
- [x] HTML preview for PO (Edge-compatible)
- [x] Django Admin interface
- [x] Docker setup with PostgreSQL
- [x] Static files serving with WhiteNoise

### Not Implemented
- [ ] Invoice model (structure not defined yet)
- [ ] Multiple PO templates (user wants to select different templates)
- [ ] User authentication beyond Django admin
- [ ] Approval workflow
- [ ] Dashboard/reports
- [ ] Email notifications

## Known Issues & Solutions

### 1. Microsoft Edge blocking PDF iframe
**Issue**: Edge blocks iframes with PDFs due to security policies  
**Solution**: Created HTML preview (po_pdf_view.html) instead of iframe  
**Files**: 
- `procurement/templates/procurement/po_pdf_view.html`
- `procurement/views.py` → `po_pdf_view()`

### 2. Static files not loading in Docker
**Issue**: CSS files returning 404  
**Solution**: Added WhiteNoise for static file serving  
**Files**:
- `portal/settings.py` → Added WhiteNoise middleware and storage
- `requirements.txt` → Added whitenoise>=6.6.0

### 3. libgdk-pixbuf package name in Debian
**Issue**: Package name changed in newer Debian versions  
**Solution**: Changed `libgdk-pixbuf2.0-0` to `libgdk-pixbuf-2.0-0`  
**File**: `Dockerfile`

## Development Workflow

### Local Development (with Docker)
```bash
# Start containers
docker-compose up -d

# View logs
docker-compose logs -f web

# Access Django shell
docker-compose exec web python manage.py shell

# Create migrations
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Rebuild after code changes
docker-compose up -d --build
```

### Access Points
- **Portal**: http://localhost:8000
- **Admin**: http://localhost:8000/admin
- **Default credentials**: admin / admin123

## Next Steps (Priority Order)

### 1. Invoice Model & Integration
**Status**: User wants to define structure  
**Task**: Wait for user to provide invoice table structure  
**Notes**: Should follow same pattern as PO (items, payment terms)

### 2. Multiple PO Templates
**Status**: User mentioned wanting different templates  
**Task**: Design template selection system  
**Options**:
- Store templates as HTML files in `templates/po_templates/`
- Add `template_name` field to PO model
- Create template selection dropdown in PO form

### 3. Production Deployment
**Status**: Docker setup ready, need server configuration  
**Tasks**:
- Set up reverse proxy (nginx)
- Configure SSL/TLS certificates
- Update ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS
- Set DEBUG=False
- Generate strong SECRET_KEY
- Configure CSRF_COOKIE_SECURE=True and SESSION_COOKIE_SECURE=True

### 4. User Authentication
**Status**: Only Django admin authentication exists  
**Options**:
- Use Django's built-in auth system
- Add custom user model with roles (admin, operator, approver)
- Integrate with external auth (OAuth, LDAP)

### 5. Approval Workflow
**Status**: Not started  
**Requirements**:
- Add status field to PO (draft, pending, approved, rejected)
- Add approval history tracking
- Add email notifications
- Add role-based permissions

## Code Conventions

### Naming
- **Models**: Singular (e.g., `PO`, `Issuer`, `Supplier`)
- **Tables**: Pluralized by Django (e.g., `po`, `issuer`, `supplier`)
- **Fields**: snake_case (e.g., `po_number`, `issued_at`)
- **Related names**: Plural (e.g., `issuer.bank_accounts`, `po.items`)

### Templates
- **Location**: `procurement/templates/procurement/`
- **Naming**: `po_list.html`, `po_detail.html`, `po_form.html`, `po_pdf_view.html`, `po_pdf.html`
- **Base template**: `base.html`

### Views
- **List**: `po_list()` - List all POs
- **Detail**: `po_detail()` - Show PO details
- **Create/Edit**: `po_form()` - Create or edit PO (pk=None for create)
- **PDF Download**: `po_pdf()` - Generate and download PDF
- **PDF Preview**: `po_pdf_view()` - Show HTML preview

## Important Files

### Configuration
- `portal/settings.py` - Django settings with PostgreSQL and WhiteNoise
- `docker-compose.yml` - Docker orchestration
- `Dockerfile` - Application container build
- `requirements.txt` - Python dependencies

### Models
- `procurement/models.py` - All database models

### Views
- `procurement/views.py` - All view functions
- `procurement/urls.py` - URL routing

### Templates
- `procurement/templates/procurement/base.html` - Base template
- `procurement/templates/procurement/po_list.html` - PO listing
- `procurement/templates/procurement/po_detail.html` - PO detail view
- `procurement/templates/procurement/po_form.html` - PO create/edit form
- `procurement/templates/procurement/po_pdf.html` - PDF template (WeasyPrint)
- `procurement/templates/procurement/po_pdf_view.html` - HTML preview template

### Admin
- `procurement/admin.py` - Django admin configuration

## Testing Checklist

When making changes, verify:
- [ ] Django server starts without errors
- [ ] Admin interface accessible at /admin/
- [ ] Can create/edit/delete POs
- [ ] PDF download works
- [ ] HTML preview works in all browsers (especially Edge)
- [ ] CSS loads correctly
- [ ] Multiple emails display correctly for Issuers
- [ ] Bank accounts display with correct addresses

## Git Repository
**URL**: https://github.com/Marcelo-Brisac/ids_po_control  
**Branch**: main  
**Last commit**: Add WhiteNoise for static files serving (2be32df)

## Contact & Support
- **Developer**: Marcelo Brisac (GitHub: Marcelo-Brisac)
- **Project started**: June 23, 2026
- **Development environment**: Docker on Windows (Docker Desktop)
