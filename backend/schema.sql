-- =============================================================================
-- HisabAI Database Schema (PostgreSQL)
-- Focus: Multi-tenant, Accounting Invariants, Auditability, Document Pipeline
-- =============================================================================

-- Ensure UUID generation extension is available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. USERS
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 2. BUSINESSES (Tenants)
CREATE TABLE IF NOT EXISTS businesses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    legal_name VARCHAR(255),
    tax_id VARCHAR(100),
    currency VARCHAR(10) NOT NULL DEFAULT 'BDT',
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_businesses_slug ON businesses(slug);

-- 3. BUSINESS MEMBERSHIPS (Tenant Scoping & RBAC)
CREATE TABLE IF NOT EXISTS business_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('owner', 'accountant', 'reviewer', 'viewer')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_business_user UNIQUE (business_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_memberships_business_user ON business_memberships(business_id, user_id);

-- 4. PARTIES (Customers, Suppliers, or Both)
CREATE TABLE IF NOT EXISTS parties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    party_type VARCHAR(50) NOT NULL CHECK (party_type IN ('buyer', 'supplier', 'both')),
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    tax_id VARCHAR(100),
    opening_balance NUMERIC(18, 2) NOT NULL DEFAULT 0.00,
    opening_balance_type VARCHAR(20) NOT NULL DEFAULT 'receivable' CHECK (opening_balance_type IN ('receivable', 'payable')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_parties_business_id ON parties(business_id);
CREATE INDEX IF NOT EXISTS idx_parties_name ON parties(business_id, name);

-- 5. DOCUMENTS (Uploaded Scans, Photos, PDFs)
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    uploaded_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    original_filename VARCHAR(255) NOT NULL,
    stored_path VARCHAR(500) NOT NULL,
    file_hash_sha256 VARCHAR(64) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    page_count INTEGER NOT NULL DEFAULT 1,
    document_type VARCHAR(50) NOT NULL DEFAULT 'unknown' CHECK (document_type IN ('sales_invoice', 'purchase_invoice', 'payment_receipt', 'voucher', 'unknown')),
    status VARCHAR(50) NOT NULL DEFAULT 'uploaded' CHECK (status IN ('uploaded', 'processing', 'needs_review', 'approved', 'rejected', 'posted')),
    rejection_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_documents_business_status ON documents(business_id, status);
CREATE INDEX IF NOT EXISTS idx_documents_business_hash ON documents(business_id, file_hash_sha256);

-- 6. DOCUMENT PAGES (OCR text and block coordinates)
CREATE TABLE IF NOT EXISTS document_pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    width INTEGER,
    height INTEGER,
    has_native_text BOOLEAN NOT NULL DEFAULT FALSE,
    raw_text TEXT,
    ocr_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_document_page UNIQUE (document_id, page_number)
);

CREATE INDEX IF NOT EXISTS idx_doc_pages_document_id ON document_pages(document_id);

-- 7. DOCUMENT EXTRACTIONS (Candidate values with confidence and evidence)
CREATE TABLE IF NOT EXISTS document_extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    document_type_candidate VARCHAR(50),
    party_name_candidate VARCHAR(255),
    matched_party_id UUID REFERENCES parties(id) ON DELETE SET NULL,
    document_number_candidate VARCHAR(100),
    issue_date_candidate DATE,
    due_date_candidate DATE,
    subtotal_candidate NUMERIC(18, 2),
    tax_amount_candidate NUMERIC(18, 2),
    total_amount_candidate NUMERIC(18, 2),
    paid_amount_candidate NUMERIC(18, 2),
    due_amount_candidate NUMERIC(18, 2),
    confidence_score NUMERIC(5, 4),
    extraction_metadata JSONB,
    warnings JSONB,
    is_human_corrected BOOLEAN NOT NULL DEFAULT FALSE,
    corrected_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_doc_extractions_document ON document_extractions(document_id);

-- 8. INVOICES (Sales and Purchase Invoices)
CREATE TABLE IF NOT EXISTS invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    party_id UUID NOT NULL REFERENCES parties(id) ON DELETE RESTRICT,
    invoice_type VARCHAR(50) NOT NULL CHECK (invoice_type IN ('sales', 'purchase')),
    invoice_number VARCHAR(100) NOT NULL,
    issue_date DATE NOT NULL,
    due_date DATE,
    subtotal NUMERIC(18, 2) NOT NULL DEFAULT 0.00,
    tax_amount NUMERIC(18, 2) NOT NULL DEFAULT 0.00,
    total_amount NUMERIC(18, 2) NOT NULL,
    paid_amount NUMERIC(18, 2) NOT NULL DEFAULT 0.00,
    due_amount NUMERIC(18, 2) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'partially_paid', 'paid', 'reversed')),
    notes TEXT,
    created_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_at TIMESTAMPTZ,
    posted_at TIMESTAMPTZ,
    idempotency_key VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_business_invoice UNIQUE (business_id, invoice_type, invoice_number)
);

CREATE INDEX IF NOT EXISTS idx_invoices_business_party ON invoices(business_id, party_id);
CREATE INDEX IF NOT EXISTS idx_invoices_business_status ON invoices(business_id, status);
CREATE INDEX IF NOT EXISTS idx_invoices_issue_date ON invoices(business_id, issue_date);

-- 9. INVOICE ITEMS (Line-item items, optional for MVP)
CREATE TABLE IF NOT EXISTS invoice_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    description VARCHAR(500) NOT NULL,
    quantity NUMERIC(14, 4) NOT NULL DEFAULT 1.0000,
    unit_price NUMERIC(18, 2) NOT NULL DEFAULT 0.00,
    line_total NUMERIC(18, 2) NOT NULL DEFAULT 0.00,
    tax_rate NUMERIC(5, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice ON invoice_items(invoice_id);

-- 10. PAYMENTS (Customer receipts & Supplier disbursements)
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    party_id UUID NOT NULL REFERENCES parties(id) ON DELETE RESTRICT,
    payment_type VARCHAR(50) NOT NULL CHECK (payment_type IN ('customer_receipt', 'supplier_payment')),
    payment_method VARCHAR(50) NOT NULL DEFAULT 'cash' CHECK (payment_method IN ('cash', 'bank', 'bkash', 'nagad', 'other')),
    payment_date DATE NOT NULL,
    amount NUMERIC(18, 2) NOT NULL,
    allocated_amount NUMERIC(18, 2) NOT NULL DEFAULT 0.00,
    unapplied_amount NUMERIC(18, 2) NOT NULL,
    reference_number VARCHAR(100),
    notes TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'approved', 'posted', 'reversed')),
    created_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    posted_at TIMESTAMPTZ,
    idempotency_key VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payments_business_party ON payments(business_id, party_id);
CREATE INDEX IF NOT EXISTS idx_payments_business_date ON payments(business_id, payment_date);

-- 11. PAYMENT ALLOCATIONS (Explicit matching between payments and invoices)
CREATE TABLE IF NOT EXISTS payment_allocations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    payment_id UUID NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE RESTRICT,
    allocated_amount NUMERIC(18, 2) NOT NULL,
    allocation_date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_allocations_payment ON payment_allocations(payment_id);
CREATE INDEX IF NOT EXISTS idx_allocations_invoice ON payment_allocations(invoice_id);

-- 12. LEDGER ENTRIES (Double-entry journal records: single source of truth)
CREATE TABLE IF NOT EXISTS ledger_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    transaction_type VARCHAR(50) NOT NULL CHECK (transaction_type IN ('opening_balance', 'sales_invoice', 'purchase_invoice', 'customer_receipt', 'supplier_payment', 'reversal', 'adjustment')),
    reference_id UUID NOT NULL,
    entry_date DATE NOT NULL,
    account_name VARCHAR(100) NOT NULL CHECK (account_name IN ('accounts_receivable', 'accounts_payable', 'cash_in_hand', 'bank', 'sales_revenue', 'purchase_expense')),
    debit NUMERIC(18, 2) NOT NULL DEFAULT 0.00,
    credit NUMERIC(18, 2) NOT NULL DEFAULT 0.00,
    party_id UUID REFERENCES parties(id) ON DELETE SET NULL,
    description TEXT,
    is_reversal BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ledger_business_date ON ledger_entries(business_id, entry_date);
CREATE INDEX IF NOT EXISTS idx_ledger_business_account ON ledger_entries(business_id, account_name);
CREATE INDEX IF NOT EXISTS idx_ledger_party ON ledger_entries(business_id, party_id);

-- 13. AUDIT LOGS (Immutable tracking of all sensitive operations)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID REFERENCES businesses(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID NOT NULL,
    changes JSONB,
    ip_address VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_business ON audit_logs(business_id, created_at);

-- 14. IDEMPOTENCY RECORDS (Guarantees safe atomic posting)
CREATE TABLE IF NOT EXISTS idempotency_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    key VARCHAR(255) NOT NULL,
    request_hash VARCHAR(64) NOT NULL,
    response_code INTEGER NOT NULL,
    response_body JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_business_idempotency_key UNIQUE (business_id, key)
);

CREATE INDEX IF NOT EXISTS idx_idempotency_lookup ON idempotency_records(business_id, key);
