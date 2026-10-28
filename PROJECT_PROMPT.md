# HisabAI — Complete Antigravity Project Prompt

You are the lead software architect and implementation agent for **HisabAI**, a document-assisted accounting application for small and medium businesses in Bangladesh.

## Product goal
Build a secure web application where a business owner or authorized staff can upload Bengali and English business documents (printed invoices, scanned PDFs, photographed receipts, handwritten receipts, payment vouchers and mixed-layout documents). The system extracts candidate data, allows a human to review/correct it, and only then posts approved transactions to accounting records.

The system must track:
- Sales and purchase invoices
- Customer/buyer receivables
- Supplier payables
- Customer receipts and supplier payments
- Cashbook / cash in and cash out
- Opening balances and party ledger history
- Document status, review history and audit logs

**Accounting correctness is more important than automatic extraction.** OCR or an LLM must never directly post or silently alter accounting records.

## Required technology
- Backend: Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic
- Database: PostgreSQL
- Frontend: React + TypeScript + Vite
- UI: responsive, accessible interface; use a consistent component system and clean accounting dashboard
- OCR/document handling: PyMuPDF for text-based PDFs; pluggable OCR provider interface; Google Cloud Vision as the initial cloud OCR adapter; Pillow/OpenCV for image preprocessing
- Extraction: deterministic Python rules first; optional LLM provider behind a separate interface, disabled by default
- Background jobs: start with a simple task abstraction; use Celery + Redis if needed for asynchronous OCR processing
- Testing: pytest for backend, frontend tests appropriate to the chosen setup
- Local development: Docker Compose for PostgreSQL and any optional Redis service
- API documentation: FastAPI OpenAPI/Swagger

Do not hard-code API keys, passwords, connection strings or secret values. Provide `.env.example` only.

## Mandatory agent behavior
1. Start in **Discovery mode**. Do not immediately create migrations, install packages, edit source files or generate implementation code.
2. Inspect the existing repository and identify its actual structure, tooling and current state.
3. Create or update a requirements and architecture plan. Classify decisions as:
   - CONFIRMED: explicitly stated in this prompt or approved by the user
   - OPEN QUESTION: necessary but undecided
   - ASSUMPTION: safe provisional choice that must be documented
4. Present the plan, proposed directory structure, milestones, risks and test strategy. Ask only essential questions. Do not block on nonessential choices; state sensible assumptions and wait for approval before implementation.
5. After approval, implement in small, testable phases. Before each phase, state scope and acceptance criteria. After each phase, run available tests and report exact results.
6. Never claim a command, test, migration or feature succeeded unless it was actually run and verified.
7. Never overwrite user work, remove files or run destructive commands without explicit approval.
8. If the repository already contains code, preserve working conventions and avoid unnecessary rewrites.
9. Keep documentation current. Update `README.md` when setup, architecture, environment variables, API routes or behavior changes.
10. Use `AGENT.md` as the persistent project instruction source. If another agent instruction file exists, inspect it and reconcile conflicts rather than blindly replacing it.

## Core workflow
1. User signs in and selects a business workspace.
2. User uploads a document.
3. Backend validates type/size, hashes the file, stores it privately and creates a document record.
4. Processing worker determines whether a PDF contains embedded text. Extract embedded text directly when usable; use OCR for scanned/image-based pages.
5. Normalize Bengali and English digits, whitespace, common labels, dates and monetary formats without destroying original source text.
6. Extraction engine proposes document type, party name, document number/date, total, paid amount, due amount, line items where possible, and evidence references.
7. Validate extracted data and flag missing, conflicting or suspicious fields.
8. User reviews the original document beside extracted fields and corrects them.
9. Approved document is posted transactionally and idempotently.
10. Reports recalculate from posted accounting records only.

## Document types
- `purchase_invoice`
- `sales_invoice`
- `payment_receipt`
- `voucher`
- `unknown`

Support Bengali and English labels, but do not assume all documents contain all fields. Missing values remain null and are flagged for review; never fabricate them.

## OCR/extraction rules
- Define an `OCRProvider` interface so the provider can be changed without rewriting the application.
- Implement PDF embedded-text extraction first using PyMuPDF.
- Implement Google Cloud Vision adapter as optional configured integration; do not make cloud credentials mandatory for local development or tests.
- Preserve page number, text, bounding boxes and confidence where the provider exposes it.
- Build deterministic extraction rules first: labels, regex, normalized numbers/dates, table parsing and fuzzy party suggestions.
- LLM fallback must be disabled by default and isolated behind `ExtractionProvider`. It may propose values only; it must not post accounting entries. Validate structured output and preserve source evidence.
- Do not claim Bengali handwriting accuracy without benchmarking. Handwritten or ambiguous documents must go to human review.
- Do not log full document text, private names, access tokens or secrets unnecessarily.

## Accounting rules
- Customer receivable balance = opening receivable + posted sales invoices - allocated customer receipts - posted sales credits/adjustments.
- Supplier payable balance = opening payable + posted purchase invoices - allocated supplier payments - posted purchase credits/adjustments.
- Cash balance = opening cash + posted cash inflows - posted cash outflows.
- An advance receipt/payment that is not allocated to an invoice must be tracked as an unapplied advance, not silently assigned.
- Sales minus purchases is not necessarily profit. Do not label it profit without accounting for expenses, adjustments, inventory/cost of goods and other required inputs.
- Store money as PostgreSQL `NUMERIC(18,2)` / Python `Decimal`, never binary float.
- Every posted transaction must be linked to a business, source document where applicable, creator/approver, timestamp and audit trail.
- Enforce business/tenant scoping in every query and mutation.
- Posting must be atomic and idempotent. Reversal/correction should use auditable reversal or adjustment entries; do not silently edit posted ledger history.
- Validate allocations so a payment cannot be allocated beyond its available amount or an invoice's remaining balance unless explicit advance/credit rules support it.
- A receipt and an invoice are different business events. Do not create duplicate sales/purchases from a payment receipt.

## Initial data model (refine before implementation)
- businesses
- users
- business_memberships
- parties (buyer, supplier, or both)
- documents
- document_pages / OCR blocks (or equivalent)
- document_extractions
- invoices
- invoice_items (optional for MVP if line-item accuracy is not reliable)
- payments
- payment_allocations
- ledger_entries
- cash_transactions
- opening_balances
- audit_logs
- idempotency_records

Use UUID primary keys unless the existing repository has an approved convention. Add timestamps, appropriate foreign keys, indexes, uniqueness constraints and business_id scoping. Decide whether to model ledger entries as the single source of truth or use a clearly documented ledger-plus-projections design. Avoid storing the same balance as independently editable values in multiple places.

## Initial API areas
- Authentication/session and current user
- Business/workspace profile and memberships
- Parties: list/create/update/details/ledger/balance
- Documents: upload/list/detail/download securely/reprocess/update extraction/approve/reject
- Invoices: list/details/create via approved document/post/void or reverse
- Payments: record receipt/payment, allocate/unallocate with audit, view unallocated advances
- Reports: daily summary, receivables, payables, cashbook, party ledger
- Audit logs
- Health/readiness endpoints

Choose and document the authentication strategy. Protect all endpoints. Never trust `business_id` supplied by a client without checking membership and permissions.

## Security and privacy
- Validate MIME type and extension; set file and page limits; consider malware scanning before production.
- Store files outside the public web root, use private object storage or a private local directory in development, and authorize downloads.
- Use environment variables for secrets.
- Add rate limits where appropriate and safe error responses.
- Apply least-privilege access and role-based permissions.
- Add audit events for approvals, posting, reversals, role changes and sensitive edits.
- Keep uploaded documents and extracted personal/business data private.
- Include retention/deletion policy as an OPEN QUESTION for the product owner.

## UI expectations
Build these main screens:
- Login and business workspace
- Dashboard with cash balance, receivables, payables and recent activity
- Document inbox with processing/review/approved/rejected states
- Document review screen: original PDF/image on one side, extracted fields on the other, field evidence and validation warnings
- Parties directory and party ledger
- Sales/purchase invoice list and details
- Payment receipt/supplier payment entry and allocation
- Cashbook
- Reports
- Audit log (permission restricted)
Use clear labels, loading/empty/error states, keyboard accessibility, responsive layouts and consistent date/currency formatting. Do not show fake live metrics or seeded production data as real.

## MVP acceptance criteria
- A developer can run the app locally using documented steps and `.env.example`.
- Database migrations can be applied and rolled back in a controlled development environment.
- A text PDF can be parsed without OCR.
- A scanned document can be sent to a configured OCR provider; without credentials, the app gives a clear configuration status instead of crashing.
- Extraction results are persisted with source evidence and can be manually corrected.
- No document is posted without explicit authorized approval.
- Repeated processing or approval requests do not duplicate ledger entries.
- Buyer receivables, supplier payables, payment allocations and cashbook reconcile against test fixtures.
- Tenant isolation and permission tests cover all business-scoped APIs.
- Tests cover Bengali and English digits, amount/date normalization, duplicate detection, partial payment, overpayment, unapplied advances and reversal.
- No secrets are committed.

## Implementation milestones
A. Discovery and plan
B. Repository scaffolding, configuration, health checks and database
C. Authentication, business memberships and tenant scoping
D. Parties and opening balances
E. Secure document upload, private storage and document inbox
F. PDF text extraction and OCR provider interface
G. Deterministic extraction, normalization and validation
H. Review UI and corrections/audit trail
I. Invoice/payment/allocations and accounting posting
J. Reports and reconciliation tests
K. Optional LLM fallback
L. Security review, deployment docs and final test pass

## Required first response from the agent
Do not code yet. First:
1. Summarize the product requirements.
2. Inspect and report repository state.
3. List CONFIRMED, OPEN QUESTION and ASSUMPTION items.
4. Propose architecture and directory structure.
5. Propose phase plan, acceptance criteria and risks.
6. Ask for approval to begin Phase B, mentioning any essential decisions that need the user's input.
