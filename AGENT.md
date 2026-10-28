# AGENT.md — HisabAI Development Rules

## 1. Default mode: Discovery
When starting a new task or repository, inspect before changing anything. Do not immediately write code, edit files, create migrations, install packages or run destructive commands.

First establish:
- What exists in the repository
- What the user is asking for
- Which requirements are confirmed
- Which decisions remain open
- Which files and tests may be affected

Present a short plan and acceptance criteria before implementation. If the user has already explicitly approved a phase and its scope, proceed within that scope.

## 2. Product definition
HisabAI is a document-assisted accounting application for Bangladesh-based businesses. It handles Bengali/English printed and handwritten invoices, receipts and vouchers. OCR/extraction proposes data; authorized users review it; only approved documents can affect accounting records.

Priority order:
1. Accounting correctness and data integrity
2. Security and tenant isolation
3. Traceability and auditability
4. Reliable document review workflow
5. OCR automation
6. Convenience and visual polish

## 3. Confirmed stack
- Python 3.12+
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x and Alembic
- PostgreSQL
- React + TypeScript + Vite
- PyMuPDF for PDF text extraction/rendering
- Pluggable OCR provider, initially Google Cloud Vision
- Pillow/OpenCV for image preprocessing
- Deterministic Python extraction rules first
- Optional LLM fallback, disabled by default
- pytest and suitable frontend tests
- Docker Compose for local dependencies

Do not silently replace these technologies. If an alternative would materially improve the project, explain the trade-offs and ask first.

## 4. Requirement status
Mark decisions in plans and documentation as:
- **CONFIRMED** — explicitly requested or approved
- **OPEN QUESTION** — requires product-owner decision
- **ASSUMPTION** — temporary choice, clearly documented

Do not turn an assumption into a confirmed requirement.

## 5. Coding workflow
For every implementation phase:
1. State scope and acceptance criteria.
2. Inspect relevant existing files.
3. Make the smallest coherent change.
4. Add/update tests.
5. Run the relevant tests, lint/type checks where available.
6. Report exact commands and actual outcomes.
7. Update README/API docs/config examples if behavior changed.

Do not claim tests pass if they were not run. If a command cannot be run, say why and provide the unverified status.

## 6. Architecture principles
- Use clear separation between API routes, schemas, domain/services, repositories/data access and infrastructure providers.
- Keep OCR providers and LLM providers behind interfaces.
- Keep accounting calculations deterministic and independent of AI providers.
- Use dependency injection and typed configuration.
- Keep route handlers thin; put business logic in services.
- Use database migrations for schema changes.
- Avoid premature microservices. Keep the initial application a modular monolith; background workers can be separated operationally when needed.
- Do not add abstractions without a clear reason.

## 7. Document processing rules
- Text PDFs: attempt embedded-text extraction before OCR.
- Scanned PDFs/images: preprocess cautiously, then use the configured OCR provider.
- Preserve original documents and extracted source evidence.
- Store page number, bounding box and provider confidence when available.
- Normalize Bengali and English digits and labels without discarding the original OCR text.
- Never fabricate a missing amount, party, date or invoice number.
- Treat handwritten Bengali and ambiguous documents as requiring human review unless benchmarked evidence supports safe automation.
- The OCR provider must be optional in local development; missing credentials must produce a helpful status/error, not application startup failure.
- Do not log private document content or secrets.

## 8. Accounting invariants
- Use `Decimal` in Python and `NUMERIC(18,2)` in PostgreSQL for money.
- Every record must be scoped to an authorized business.
- Do not trust client-supplied business IDs without membership/permission checks.
- Only approved documents can be posted.
- Posting is transactional and idempotent.
- Reprocessing an OCR job must not create accounting entries.
- Repeated approval requests must not create duplicate ledger entries.
- Posted records must not be silently overwritten. Use auditable reversals/adjustments.
- Track customer receipts and supplier payments separately from invoices.
- Allocate payments explicitly. Unallocated advances remain unapplied until assigned.
- Prevent over-allocation unless a specifically designed credit/advance workflow allows it.
- Reconcile party balances and cashbook from posted transactions.
- Do not call sales minus purchases “profit” without the required expense, inventory/cost and adjustment data.

## 9. Security requirements
- Never commit secrets or real credentials.
- Keep `.env` out of version control; maintain `.env.example` with placeholders.
- Validate upload type, size and page count.
- Store uploaded files privately, outside public static directories.
- Authorize every file download.
- Use secure password/session/token handling according to the approved auth design.
- Enforce role permissions and business membership.
- Audit approvals, posting, reversals, sensitive edits and permission changes.
- Use safe error responses and avoid leaking stack traces or document contents to users.
- Add tests for cross-tenant access denial.

## 10. Frontend rules
- Use TypeScript types that reflect backend API schemas.
- Include loading, empty, validation, success and error states.
- Do not fabricate live dashboard data.
- Keep document preview and extracted fields side by side where screen space allows.
- Display source evidence and validation warnings for extracted fields.
- Make approval explicit and show the impact of posting.
- Support responsive layout and keyboard-accessible controls.
- Centralize API client configuration and environment variables; never put secrets in frontend variables.

## 11. API and database conventions
- Version API routes, e.g. `/api/v1`.
- Use consistent error responses and status codes.
- Add pagination to list endpoints.
- Use UUID IDs unless existing approved conventions differ.
- Add foreign keys, indexes, uniqueness constraints and timestamps where appropriate.
- Add idempotency protection to posting/payment operations.
- Document API routes and configuration.
- Do not expose internal storage paths.

## 12. Testing requirements
At minimum test:
- Bengali/English digit normalization
- Amount and date parsing
- Missing and conflicting fields
- Duplicate file/document detection
- Party fuzzy-match suggestions
- Partial payments and multiple allocations
- Over-allocation rejection
- Unapplied advances
- Receivable/payable calculations
- Cashbook calculations
- Posting atomicity/idempotency
- Reversal/audit trail
- Tenant isolation and permissions
- OCR provider missing-credential behavior
- API validation and frontend review workflow

Use realistic synthetic fixtures or authorized redacted samples. Never commit real customer invoices or private business records.

## 13. Git and change safety
- Never delete or overwrite user work without explicit permission.
- Do not rewrite Git history or force-push unless explicitly approved.
- Do not run destructive database commands against any non-test database.
- Keep changes focused and reviewable.
- Explain any new dependency and why it is needed.

## 14. Completion report
When a phase is complete, report:
- What changed
- Important files created/modified
- Commands/tests actually run and results
- Known limitations
- Security/accounting implications
- Next recommended phase

Do not claim production readiness until security, backup/restore, migrations, monitoring, reconciliation and deployment have been reviewed.
