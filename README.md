# HisabAI

**Document-assisted accounting for Bengali and English business documents.**

HisabAI helps a business organize invoices, receipts and vouchers, extract candidate information with OCR, review and correct it, and then record approved transactions for receivables, payables and cashbook reporting.

> **Accounting safety principle:** OCR and AI propose data. They do not independently post accounting entries. Authorized human review and deterministic validation are required before posting.

## Product goals

- Upload printed and handwritten Bengali/English documents.
- Support PDFs, scans and photographed pages.
- Extract candidate party, date, document number, total and payment amounts.
- Preserve OCR text and page/region evidence for review.
- Track sales, purchases, customer receipts, supplier payments and unapplied advances.
- Calculate buyer receivables, supplier payables and cashbook from posted transactions.
- Provide an audit trail for corrections, approvals, posting and reversals.
- Keep business data isolated by workspace.

## Planned technology

| Layer | Technology |
|---|---|
| Backend API | Python 3.12+, FastAPI, Pydantic v2 |
| Database | PostgreSQL |
| ORM/migrations | SQLAlchemy 2.x, Alembic |
| Frontend | React, TypeScript, Vite |
| PDF text extraction | PyMuPDF |
| Optional table extraction | pdfplumber |
| OCR | Pluggable provider; Google Cloud Vision initial adapter |
| Image preprocessing | Pillow, OpenCV |
| Matching | RapidFuzz |
| Background processing | Task abstraction; Celery + Redis when needed |
| Tests | pytest and frontend test tooling |

Technology choices and provider capabilities must be validated against actual sample documents before production use. Bengali handwriting is a particularly challenging case; uncertain results must go to manual review.

## Quick Start & Running the Project

### 1. Start the Backend API (FastAPI)
Run from the root project directory:
```bash
python main.py
# Or run with the convenience batch script on Windows:
.\run.bat
```
- API will start at: `http://127.0.0.1:8000`
- Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/api/v1/health`

### 2. Start the Frontend (Vite + React)
In a separate terminal:
```bash
cd frontend
npm run dev
```
- Frontend will run at: `http://localhost:5173`
- Pre-configured Vite proxy automatically routes `/api/` calls to `http://127.0.0.1:8000`.

### 3. Verification & Tests
- **Frontend Typecheck & Build**:
  ```bash
  npm --prefix frontend run build
  ```
- **Backend Test Suite (25 Tests Passing)**:
  ```powershell
  & "backend\.venv\Scripts\pytest" -v
  ```

## Processing workflow

1. User uploads a document.
2. API validates the file and stores it privately.
3. System detects whether PDF text is already available.
4. Embedded text is extracted directly when usable; scanned pages go through OCR.
5. The extraction engine normalizes Bengali/English digits, labels, dates and amounts.
6. Rules propose fields and attach evidence such as page and bounding box where available.
7. Validation detects missing fields, conflicting totals, likely duplicates and ambiguous parties.
8. Authorized user reviews the original and corrects the extracted fields.
9. User approves the document.
10. A transactional, idempotent posting operation creates the accounting records.
11. Reports use posted transactions only.

## Accounting rules

- **Buyer receivable** = opening receivable + posted sales invoices − allocated receipts − posted credits/adjustments.
- **Supplier payable** = opening payable + posted purchase invoices − allocated supplier payments − posted credits/adjustments.
- **Cash balance** = opening cash + posted cash inflows − posted cash outflows.
- Unallocated receipts/payments remain unapplied advances until explicitly allocated.
- An invoice and a payment receipt are different events. A receipt must not create a duplicate sale.
- Sales minus purchases is not necessarily profit.
- Money uses Python `Decimal` and PostgreSQL `NUMERIC(18,2)`.
- Posted history is not silently edited; corrections use auditable reversals or adjustments.

## Repository status

- **Implemented**:
  - Git repository initialization, `.gitignore`, `.env.example`, and `docker-compose.yml`.
  - Backend project scaffold with Python 3.11/3.12 compatibility (`FastAPI`, `Pydantic v2`, `SQLAlchemy 2.x`, `Alembic`, `psycopg3`).
  - Complete PostgreSQL database schema (`backend/schema.sql`) with 14 multi-tenant tables, UUID primary keys, and `NUMERIC(18,2)` monetary precision.
  - SQLAlchemy 2.0 ORM models (`app/models/`) and Pydantic v2 schemas (`app/schemas/`).
  - Active PostgreSQL database `hisabai_db` created and schema verified with 14 live tables.
  - Health check endpoints (`/health` and `/api/v1/health`).
  - Versioned API under `/api/v1/` (`/api/v1/health`, `/api/v1/auth`, `/api/v1/businesses`).
  - **Phase C — Authentication & Tenant Scoping**:
    - User registration (`POST /api/v1/auth/register`) with `bcrypt` password hashing.
    - User login (`POST /api/v1/auth/login`) with signed Bearer JWT token issuance.
    - Current user profile endpoint (`GET /api/v1/auth/me`).
    - Business workspace creation with automatic `owner` membership (`POST /api/v1/businesses/`).
    - Business list, detail, and member management (`/api/v1/businesses/{id}/members`).
    - Multi-tenant isolation guard (`get_current_business`) and RBAC checker (`require_business_role`).
  - **Phase D — Parties & Opening Balances**:
    - Party creation with Bengali name support (`POST /api/v1/parties/`).
    - Automatic double-entry ledger entry creation for opening receivable/payable balances.
    - Duplicate party name prevention per business workspace (HTTP 409).
    - Paginated party list with type filtering and Bengali text search (`GET /api/v1/parties/`).
    - Party balance calculation endpoint (`GET /api/v1/parties/{id}/balance`).
    - Chronological party ledger history (`GET /api/v1/parties/{id}/ledger`).
    - Cross-tenant party isolation enforcement (HTTP 404).
  - **Phase E — Document Upload & Private Storage**:
    - Secure document upload API supporting PDF, PNG, JPG, JPEG, and WebP (`POST /api/v1/documents/upload`).
    - File extension and size limit validation (up to 25MB, rejecting unsupported formats with HTTP 400/413).
    - SHA-256 content hashing and automatic duplicate upload detection per business workspace (HTTP 409).
    - PyMuPDF page count extraction and Pillow image verification.
    - Private file storage outside public web root with path traversal protection.
    - Authorized file download/streaming API (`GET /api/v1/documents/{id}/download`).
    - Document inbox listing with status and type filters (`GET /api/v1/documents/`).
    - Document rejection with explicit reason (`POST /api/v1/documents/{id}/reject`).
    - Cross-tenant document file and metadata isolation (HTTP 404).
  - **Phase F — PDF Text Extraction & OCR Provider Interface**:
    - Embedded native PDF text extraction using PyMuPDF without requiring OCR (`pdf_text.py`).
    - Pluggable `OCRProvider` abstraction (`base.py`, `factory.py`) with support for multiple backends.
    - Deterministic `MockOCRProvider` for offline development and CI test suites.
    - Resilient `GoogleVisionOCRProvider` adapter with missing-credential safety (produces clear status without crashing startup).
    - End-to-end document processing pipeline (`POST /api/v1/documents/{id}/process`).
    - Extracted pages, bounding blocks, and confidence inspection (`GET /api/v1/documents/{id}/pages`).
    - Automatic status transition to `needs_review` upon extraction completion.
  - **Phase G — Deterministic Extraction & Bengali Normalization**:
    - Bengali to English numeral normalization (`০-৯` ➔ `0-9`) and currency format parsing (`normalization.py`).
    - Flexible date parser supporting Bengali and English formats (`DD/MM/YYYY`, `YYYY-MM-DD`).
    - Deterministic extraction heuristics for document type, document number, issue date, subtotal, tax, total, paid, and due amounts (`rule_extractor.py`).
    - Token-based RapidFuzz party matching against workspace parties (`party_matcher.py`).
    - Mathematical consistency validation (Subtotal + Tax == Total, Paid + Due == Total) with warnings for discrepancies.
    - Human-in-the-loop manual correction endpoint (`PUT /api/v1/documents/{id}/extraction`).
  - **Phase H — Modern Accounting SaaS Frontend (React + TypeScript + Vite + Tailwind CSS)**:
    - Modular architecture with typed models (`types/`), domain API services (`api/`), reusable UI primitives (`Button`, `Card`, `Badge`, `Modal`), and responsive shell (`Sidebar`, `Header`).
    - **Dashboard Page (`DashboardPage.tsx`)**: High-fidelity reproduction of Reference Image 1 with 4 accent-border KPI cards, cash flow bar chart, invoices overview donut chart, and BDT (`৳`) currency formatting.
    - **Documents Inbox (`DocumentsPage.tsx`)**: Reproduction of Reference Image 2 with 4 status counter cards, filter pills, document table, and upload modal with drag-and-drop.
    - **Document Review Page (`DocumentReviewPage.tsx`)**: Highest-priority split-screen review matching Reference Image 3 (50% left original document preview with zoom/scale controls, 50% right editable extracted fields, mathematical consistency validation, confidence scores, source highlight inspection, Save Draft, Reject modal, and Approve & Post confirmation).
    - **Khata / Parties Page (`PartiesPage.tsx`)**: High-fidelity reproduction of Reference Image 4 with 3 summary KPI cards ("You'll get", "You'll give", "Net Balance"), search, customer/supplier filter tabs, Add Party modal, and running party ledger modal.
    - **Invoices Page (`InvoicesPage.tsx`)**: Sales invoices vs purchase bills register with status badges, line items detail modal, subtotal, tax/VAT, and due tracking.
    - **Payments Page (`PaymentsPage.tsx`)**: Money in (customer receipts) and money out (supplier payments) register with payment methods (Cash, Bank, bKash, Nagad) and allocation modal.
    - **General Ledger (`LedgerPage.tsx`)**: Chronological double-entry trial balance audit trail with automatic mathematical equilibrium verification.
    - **Financial Reports (`ReportsPage.tsx`)**: Aged receivables (দেনা বিবরণী), aged payables (পাওনা বিবরণী), and VAT summary.
    - **Settings Page (`SettingsPage.tsx`)**: Business profile management, OCR provider selection (Google Cloud Vision / PyMuPDF offline), and system architecture health diagnostics.
    - Full bilingual Bengali and English UI support (`বাংলা` / `EN` toggle in header).
    - 100% TypeScript and Vite build verification (`npm --prefix frontend run build` completes with 0 errors).
  - Comprehensive automated test suite (25 backend tests passing: live DB integration, metadata, health endpoints, Bengali text support, monetary precision, auth flow, cross-tenant access denial, party lifecycle, document storage, native PDF extraction, OCR pipeline, Bengali digit normalization, fuzzy party matching, and deterministic extraction).
- **Partially Implemented**:
  - Full end-to-end posting service from approved documents to invoices and ledger records.
- **Planned / Next**:
  - Phase I: Accounting posting and idempotent ledger entry recording from approved documents.
  - Phase J: Financial reconciliation and automated report generation.

## Suggested repository structure

```text
HisabAI/
├── AGENT.md
├── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/              # settings, security, logging
│   │   ├── api/v1/            # versioned route handlers
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── models/             # SQLAlchemy models
│   │   ├── repositories/       # data access
│   │   ├── services/           # accounting and workflow rules
│   │   ├── document_processing/
│   │   │   ├── pdf_text.py
│   │   │   ├── preprocessing.py
│   │   │   ├── providers/
│   │   │   ├── normalization.py
│   │   │   └── extraction/
│   │   └── workers/
│   └── tests/
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   ├── pages/
│   │   ├── lib/
│   │   └── types/
│   └── tests/
└── docs/
    ├── architecture.md
    ├── accounting-rules.md
    ├── api.md
    └── deployment.md
```

This is a proposed structure, not a requirement to restructure an existing repository unnecessarily.

## Local development

### Prerequisites

- Python 3.12+
- Node.js LTS and npm
- Docker Desktop / Docker Engine with Docker Compose
- Git
- Optional: Google Cloud Vision credentials for real OCR integration

### 1. Clone and configure

```bash
git clone <YOUR_REPOSITORY_URL>
cd HisabAI
cp .env.example .env
```

Edit `.env` with local development values. Never commit `.env`. The agent must create `.env.example` with placeholder values and document every variable.

### 2. Start dependencies

```bash
docker compose up -d postgres
```

If Redis is configured for background jobs:

```bash
docker compose up -d redis
```

Use service names and ports actually defined in `docker-compose.yml`; update these instructions if the implementation differs.

### 3. Start backend

```bash
cd backend
python -m venv .venv
```

Activate the environment:

**Windows PowerShell**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Linux/macOS**
```bash
source .venv/bin/activate
```

Install dependencies according to the project's chosen package manager. If `requirements.txt` is provided:

```bash
pip install -r requirements.txt
```

Apply migrations only to the intended local development database:

```bash
alembic upgrade head
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Expected development URLs, if configured:
- API: `http://127.0.0.1:8000`
- OpenAPI docs: `http://127.0.0.1:8000/docs`
- Health endpoint: check the implemented route and document its exact path.

### 4. Start frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Configure the frontend API base URL using a Vite environment variable, such as `VITE_API_BASE_URL`. Frontend-exposed variables must never contain secrets.

> Commands and paths above are a proposed setup. Confirm them against the actual files created by the agent.

## Environment variables

Maintain `.env.example` with placeholders for variables such as:

```dotenv
APP_ENV=development
APP_NAME=HisabAI
API_V1_PREFIX=/api/v1
DATABASE_URL=postgresql+psycopg://hisabai:change_me@localhost:5432/hisabai
UPLOAD_DIR=./private_uploads
MAX_UPLOAD_SIZE_MB=20
GOOGLE_CLOUD_PROJECT=
GOOGLE_APPLICATION_CREDENTIALS=
OCR_PROVIDER=google_vision
LLM_FALLBACK_ENABLED=false
REDIS_URL=redis://localhost:6379/0
```

These are illustrative configuration names. The implementation must keep configuration consistent and must not log secret values. Google credentials should follow the provider's recommended secure configuration; never paste a service-account key into source code.

## Initial API areas

Use a versioned API under `/api/v1`:

- Authentication and current user
- Business workspace and memberships
- Parties and party ledger
- Document upload, list, detail, private download, reprocess and review
- Approve/reject document
- Sales and purchase invoices
- Customer receipts and supplier payments
- Payment allocations and unapplied advances
- Daily summary, receivables, payables and cashbook reports
- Audit logs
- Health/readiness checks

Exact routes and schemas should be documented after implementation.

## Security checklist

- Keep uploads outside public static directories.
- Validate file type, size and page count.
- Authorize every document download.
- Scope all records and queries to the active business and user's permissions.
- Use password/session/token practices appropriate to the approved authentication design.
- Never commit credentials or real customer documents.
- Use safe errors and avoid logging document contents.
- Add audit logs for approvals, postings, reversals and sensitive changes.
- Test cross-tenant access denial.
- Define backup, restore, retention and deletion procedures before production.

## Testing

Backend tests should cover:
- Bengali and English digit normalization
- Date and amount parsing
- Missing or conflicting extraction fields
- Duplicate upload and duplicate posting
- Partial payments and multiple allocations
- Over-allocation rejection
- Unapplied advances
- Receivable/payable and cashbook calculations
- Transaction atomicity and idempotency
- Reversals and audit history
- Tenant isolation and role permissions
- Missing OCR credentials and provider failures

Use synthetic or authorized redacted test documents. Do not commit private business documents.

## Milestones

1. Discovery and architecture approval
2. Backend scaffold, configuration, PostgreSQL and migrations
3. Authentication, workspace membership and tenant isolation
4. Parties and opening balances
5. Private document upload and inbox
6. PDF text extraction and OCR provider interface
7. Rule-based extraction and validation
8. Document review UI and audit trail
9. Invoices, payments, allocations and posting
10. Reports and reconciliation tests
11. Optional LLM fallback
12. Security review, deployment and backup/restore documentation

## Limitations and non-goals for the first MVP

- Do not promise perfect handwritten Bengali OCR.
- Do not auto-post uncertain extracted values.
- Do not build multi-branch accounting, payroll, tax filing or full inventory accounting unless explicitly approved.
- Do not claim profit reporting without a complete and approved profit calculation model.
- Do not use an LLM as the accounting source of truth.

## Contributing / AI-agent workflow

Before changing code, follow `AGENT.md`. Work in small phases, add tests, run them, document actual results and ask before destructive operations. Never report unverified functionality as complete.
