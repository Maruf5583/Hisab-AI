import uuid
from decimal import Decimal
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.party import Party
from app.models.invoice import Invoice, InvoiceItem
from app.models.payment import Payment, PaymentAllocation
from app.models.ledger import LedgerEntry
from app.models.audit import AuditLog
from app.schemas.document import DocumentApprovalRequest, DocumentPostingResponse


class PostingService:
    """Service to safely and idempotently post approved documents to the double-entry accounting ledger."""

    def post_document(
        self,
        document_id: uuid.UUID,
        business_id: uuid.UUID,
        user_id: uuid.UUID,
        approval: DocumentApprovalRequest,
        db: Session,
    ) -> DocumentPostingResponse:
        # 1. Tenant-scoped Document verification
        doc = (
            db.query(Document)
            .filter(Document.id == document_id, Document.business_id == business_id)
            .first()
        )
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found in active business workspace.",
            )

        # 2. Idempotency Check: prevent double posting
        if doc.status == "posted":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Document '{doc.original_filename}' has already been approved and posted to the ledger.",
            )

        # 3. Tenant-scoped Party verification
        party = (
            db.query(Party)
            .filter(Party.id == approval.party_id, Party.business_id == business_id)
            .first()
        )
        if not party:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Party with ID {approval.party_id} not found in this business workspace.",
            )

        # 4. Mathematical consistency & normalization
        total_amt = approval.total_amount
        tax_amt = approval.tax_amount
        subtotal_amt = approval.subtotal

        if subtotal_amt == Decimal("0.00") and total_amt > tax_amt:
            subtotal_amt = total_amt - tax_amt

        # Validate subtotal + tax == total
        if subtotal_amt + tax_amt != total_amt:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Mathematical inconsistency: Subtotal ({subtotal_amt}) + "
                    f"Tax ({tax_amt}) does not equal Total ({total_amt})."
                ),
            )

        paid_amt = min(approval.paid_amount, total_amt)
        due_amt = max(Decimal("0.00"), total_amt - paid_amt)

        created_invoice: Optional[Invoice] = None
        created_payment: Optional[Payment] = None
        ledger_entries: List[LedgerEntry] = []
        now = datetime.now(timezone.utc)

        # 5. Process according to document type
        if approval.document_type in ["sales_invoice", "purchase_invoice"]:
            inv_type = "sales" if approval.document_type == "sales_invoice" else "purchase"

            # Check duplicate invoice number for this business and type
            existing_inv = (
                db.query(Invoice)
                .filter(
                    Invoice.business_id == business_id,
                    Invoice.invoice_type == inv_type,
                    Invoice.invoice_number == approval.document_number,
                )
                .first()
            )
            if existing_inv:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"An invoice with number '{approval.document_number}' and type "
                        f"'{inv_type}' already exists for this business."
                    ),
                )

            inv_status = "paid" if paid_amt >= total_amt else ("partially_paid" if paid_amt > Decimal("0.00") else "approved")

            created_invoice = Invoice(
                business_id=business_id,
                document_id=doc.id,
                party_id=party.id,
                invoice_type=inv_type,
                invoice_number=approval.document_number,
                issue_date=approval.issue_date,
                due_date=approval.due_date,
                subtotal=subtotal_amt,
                tax_amount=tax_amt,
                total_amount=total_amt,
                paid_amount=paid_amt,
                due_amount=due_amt,
                status=inv_status,
                notes=approval.notes,
                created_by_user_id=user_id,
                approved_by_user_id=user_id,
                approved_at=now,
                posted_at=now,
            )
            db.add(created_invoice)
            db.flush()

            # Optional default invoice line item
            inv_item = InvoiceItem(
                invoice_id=created_invoice.id,
                description=f"Items for {doc.original_filename}",
                quantity=Decimal("1.0000"),
                unit_price=subtotal_amt,
                line_total=subtotal_amt,
                tax_rate=Decimal("0.00") if subtotal_amt == Decimal("0.00") else (tax_amt / subtotal_amt * 100),
            )
            db.add(inv_item)

            # Double-Entry Ledger Postings
            if inv_type == "sales":
                # Debit: Accounts Receivable (Asset increase)
                ledger_entries.append(
                    LedgerEntry(
                        business_id=business_id,
                        transaction_type="sales_invoice",
                        reference_id=created_invoice.id,
                        entry_date=approval.issue_date,
                        account_name="accounts_receivable",
                        debit=total_amt,
                        credit=Decimal("0.00"),
                        party_id=party.id,
                        description=f"Sales Invoice #{approval.document_number} receivable for {party.name}",
                    )
                )
                # Credit: Sales Revenue (Income increase)
                ledger_entries.append(
                    LedgerEntry(
                        business_id=business_id,
                        transaction_type="sales_invoice",
                        reference_id=created_invoice.id,
                        entry_date=approval.issue_date,
                        account_name="sales_revenue",
                        debit=Decimal("0.00"),
                        credit=total_amt,
                        party_id=party.id,
                        description=f"Sales revenue from Invoice #{approval.document_number}",
                    )
                )

                # If immediate payment was made
                if paid_amt > Decimal("0.00"):
                    created_payment = Payment(
                        business_id=business_id,
                        document_id=doc.id,
                        party_id=party.id,
                        payment_type="customer_receipt",
                        payment_method="cash",
                        payment_date=approval.issue_date,
                        amount=paid_amt,
                        allocated_amount=paid_amt,
                        unapplied_amount=Decimal("0.00"),
                        reference_number=f"RCT-{approval.document_number}",
                        status="posted",
                        created_by_user_id=user_id,
                        approved_by_user_id=user_id,
                        posted_at=now,
                    )
                    db.add(created_payment)
                    db.flush()

                    # Payment allocation to invoice
                    allocation = PaymentAllocation(
                        business_id=business_id,
                        payment_id=created_payment.id,
                        invoice_id=created_invoice.id,
                        allocated_amount=paid_amt,
                        allocation_date=approval.issue_date,
                    )
                    db.add(allocation)

                    # Debit: Cash in hand (Asset increase)
                    ledger_entries.append(
                        LedgerEntry(
                            business_id=business_id,
                            transaction_type="customer_receipt",
                            reference_id=created_payment.id,
                            entry_date=approval.issue_date,
                            account_name="cash_in_hand",
                            debit=paid_amt,
                            credit=Decimal("0.00"),
                            party_id=party.id,
                            description=f"Cash receipt for Invoice #{approval.document_number}",
                        )
                    )
                    # Credit: Accounts Receivable (Asset decrease)
                    ledger_entries.append(
                        LedgerEntry(
                            business_id=business_id,
                            transaction_type="customer_receipt",
                            reference_id=created_payment.id,
                            entry_date=approval.issue_date,
                            account_name="accounts_receivable",
                            debit=Decimal("0.00"),
                            credit=paid_amt,
                            party_id=party.id,
                            description=f"Settlement of receivable for Invoice #{approval.document_number}",
                        )
                    )

            else:
                # Purchase Invoice
                # Debit: Purchase Expense / Inventory
                ledger_entries.append(
                    LedgerEntry(
                        business_id=business_id,
                        transaction_type="purchase_invoice",
                        reference_id=created_invoice.id,
                        entry_date=approval.issue_date,
                        account_name="purchase_expense",
                        debit=total_amt,
                        credit=Decimal("0.00"),
                        party_id=party.id,
                        description=f"Purchase bill #{approval.document_number} expense from {party.name}",
                    )
                )
                # Credit: Accounts Payable (Liability increase)
                ledger_entries.append(
                    LedgerEntry(
                        business_id=business_id,
                        transaction_type="purchase_invoice",
                        reference_id=created_invoice.id,
                        entry_date=approval.issue_date,
                        account_name="accounts_payable",
                        debit=Decimal("0.00"),
                        credit=total_amt,
                        party_id=party.id,
                        description=f"Accounts payable liability for Bill #{approval.document_number}",
                    )
                )

                # If immediate payment was disbursed
                if paid_amt > Decimal("0.00"):
                    created_payment = Payment(
                        business_id=business_id,
                        document_id=doc.id,
                        party_id=party.id,
                        payment_type="supplier_payment",
                        payment_method="cash",
                        payment_date=approval.issue_date,
                        amount=paid_amt,
                        allocated_amount=paid_amt,
                        unapplied_amount=Decimal("0.00"),
                        reference_number=f"PAY-{approval.document_number}",
                        status="posted",
                        created_by_user_id=user_id,
                        approved_by_user_id=user_id,
                        posted_at=now,
                    )
                    db.add(created_payment)
                    db.flush()

                    allocation = PaymentAllocation(
                        business_id=business_id,
                        payment_id=created_payment.id,
                        invoice_id=created_invoice.id,
                        allocated_amount=paid_amt,
                        allocation_date=approval.issue_date,
                    )
                    db.add(allocation)

                    # Debit: Accounts Payable (Liability decrease)
                    ledger_entries.append(
                        LedgerEntry(
                            business_id=business_id,
                            transaction_type="supplier_payment",
                            reference_id=created_payment.id,
                            entry_date=approval.issue_date,
                            account_name="accounts_payable",
                            debit=paid_amt,
                            credit=Decimal("0.00"),
                            party_id=party.id,
                            description=f"Payment settlement for Bill #{approval.document_number}",
                        )
                    )
                    # Credit: Cash in hand (Asset decrease)
                    ledger_entries.append(
                        LedgerEntry(
                            business_id=business_id,
                            transaction_type="supplier_payment",
                            reference_id=created_payment.id,
                            entry_date=approval.issue_date,
                            account_name="cash_in_hand",
                            debit=Decimal("0.00"),
                            credit=paid_amt,
                            party_id=party.id,
                            description=f"Cash payment for Bill #{approval.document_number}",
                        )
                    )

        else:
            # Standalone payment receipt or voucher
            is_receipt = approval.document_type == "payment_receipt"
            pay_type = "customer_receipt" if is_receipt else "supplier_payment"

            created_payment = Payment(
                business_id=business_id,
                document_id=doc.id,
                party_id=party.id,
                payment_type=pay_type,
                payment_method="cash",
                payment_date=approval.issue_date,
                amount=total_amt,
                allocated_amount=Decimal("0.00"),
                unapplied_amount=total_amt,
                reference_number=approval.document_number,
                notes=approval.notes,
                status="posted",
                created_by_user_id=user_id,
                approved_by_user_id=user_id,
                posted_at=now,
            )
            db.add(created_payment)
            db.flush()

            if is_receipt:
                ledger_entries.append(
                    LedgerEntry(
                        business_id=business_id,
                        transaction_type="customer_receipt",
                        reference_id=created_payment.id,
                        entry_date=approval.issue_date,
                        account_name="cash_in_hand",
                        debit=total_amt,
                        credit=Decimal("0.00"),
                        party_id=party.id,
                        description=f"Receipt voucher #{approval.document_number} from {party.name}",
                    )
                )
                ledger_entries.append(
                    LedgerEntry(
                        business_id=business_id,
                        transaction_type="customer_receipt",
                        reference_id=created_payment.id,
                        entry_date=approval.issue_date,
                        account_name="accounts_receivable",
                        debit=Decimal("0.00"),
                        credit=total_amt,
                        party_id=party.id,
                        description=f"Payment received from {party.name}",
                    )
                )
            else:
                ledger_entries.append(
                    LedgerEntry(
                        business_id=business_id,
                        transaction_type="supplier_payment",
                        reference_id=created_payment.id,
                        entry_date=approval.issue_date,
                        account_name="accounts_payable",
                        debit=total_amt,
                        credit=Decimal("0.00"),
                        party_id=party.id,
                        description=f"Payment voucher #{approval.document_number} to {party.name}",
                    )
                )
                ledger_entries.append(
                    LedgerEntry(
                        business_id=business_id,
                        transaction_type="supplier_payment",
                        reference_id=created_payment.id,
                        entry_date=approval.issue_date,
                        account_name="cash_in_hand",
                        debit=Decimal("0.00"),
                        credit=total_amt,
                        party_id=party.id,
                        description=f"Cash paid to {party.name}",
                    )
                )

        # 6. Verify Mathematical Double-Entry Equilibrium
        total_debit = sum(e.debit for e in ledger_entries)
        total_credit = sum(e.credit for e in ledger_entries)
        if total_debit != total_credit:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Double-entry ledger imbalance detected! Total Debit ({total_debit}) != Total Credit ({total_credit}).",
            )

        # 7. Persist all ledger entries
        for entry in ledger_entries:
            db.add(entry)
        db.flush()

        # 8. Update Document status to posted
        doc.status = "posted"
        doc.document_type = approval.document_type
        db.add(doc)

        # 9. Record Immutable Audit Log
        audit = AuditLog(
            business_id=business_id,
            user_id=user_id,
            action="document_posted",
            entity_type="document",
            entity_id=doc.id,
            changes={
                "document_number": approval.document_number,
                "document_type": approval.document_type,
                "total_amount": str(total_amt),
                "invoice_id": str(created_invoice.id) if created_invoice else None,
                "payment_id": str(created_payment.id) if created_payment else None,
                "ledger_entries_count": len(ledger_entries),
            },
        )
        db.add(audit)

        # Commit entire atomic transaction
        db.commit()

        return DocumentPostingResponse(
            success=True,
            document_id=doc.id,
            document_status="posted",
            invoice_id=created_invoice.id if created_invoice else None,
            payment_id=created_payment.id if created_payment else None,
            ledger_entry_ids=[e.id for e in ledger_entries],
            total_posted_debit=total_debit,
            total_posted_credit=total_credit,
            message="Document successfully approved and posted to the double-entry accounting ledger.",
        )


posting_service = PostingService()
