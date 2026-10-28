import uuid
from decimal import Decimal
from datetime import date, datetime
import pytest
from sqlalchemy import text
from app.core.database import SessionLocal
from app.models import (
    User,
    Business,
    BusinessMembership,
    Party,
    Invoice,
    Payment,
    LedgerEntry,
)


def test_database_connection_and_table_count():
    """Verify live PostgreSQL connection and that all 14 tables exist in public schema."""
    with SessionLocal() as db:
        result = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """))
        tables = [row[0] for row in result.fetchall()]
        
        expected = {
            "users",
            "businesses",
            "business_memberships",
            "parties",
            "documents",
            "document_pages",
            "document_extractions",
            "invoices",
            "invoice_items",
            "payments",
            "payment_allocations",
            "ledger_entries",
            "audit_logs",
            "idempotency_records",
        }
        assert expected.issubset(set(tables)), f"Missing tables in database: {expected - set(tables)}"


def test_transactional_accounting_entry_lifecycle():
    """Verify transactional entity creation and monetary precision in PostgreSQL."""
    with SessionLocal() as db:
        unique_suffix = uuid.uuid4().hex[:8]
        
        # 1. Create Business
        business = Business(
            name=f"টেস্ট এন্টারপ্রাইজ {unique_suffix}",
            slug=f"test-ent-{unique_suffix}",
            legal_name="Test Enterprise Bangladesh Ltd.",
            currency="BDT",
        )
        db.add(business)
        db.flush()

        # 2. Create User
        user = User(
            email=f"user_{unique_suffix}@hisabai.local",
            hashed_password="fake-hashed-password",
            full_name="মারুফ হোসেন (Maruf Hossain)",
        )
        db.add(user)
        db.flush()

        # 3. Create Business Membership
        membership = BusinessMembership(
            business_id=business.id,
            user_id=user.id,
            role="owner",
        )
        db.add(membership)
        db.flush()

        # 4. Create Party with Bengali Name
        party = Party(
            business_id=business.id,
            name="মেসার্স করিম অ্যান্ড ব্রাদার্স",
            party_type="buyer",
            phone="01819000000",
            opening_balance=Decimal("5000.00"),
            opening_balance_type="receivable",
        )
        db.add(party)
        db.flush()

        # 5. Create Posted Sales Invoice
        invoice = Invoice(
            business_id=business.id,
            party_id=party.id,
            invoice_type="sales",
            invoice_number=f"INV-{unique_suffix}",
            issue_date=date(2026, 10, 28),
            subtotal=Decimal("10000.00"),
            tax_amount=Decimal("1500.00"),
            total_amount=Decimal("11500.00"),
            paid_amount=Decimal("0.00"),
            due_amount=Decimal("11500.00"),
            status="approved",
            created_by_user_id=user.id,
            approved_by_user_id=user.id,
            approved_at=datetime.utcnow(),
            posted_at=datetime.utcnow(),
        )
        db.add(invoice)
        db.flush()

        # 6. Create Double-Entry Ledger Records
        entry_ar = LedgerEntry(
            business_id=business.id,
            transaction_type="sales_invoice",
            reference_id=invoice.id,
            entry_date=invoice.issue_date,
            account_name="accounts_receivable",
            debit=Decimal("11500.00"),
            credit=Decimal("0.00"),
            party_id=party.id,
            description="বিক্রয় চালান ডেবিট",
        )
        entry_rev = LedgerEntry(
            business_id=business.id,
            transaction_type="sales_invoice",
            reference_id=invoice.id,
            entry_date=invoice.issue_date,
            account_name="sales_revenue",
            debit=Decimal("0.00"),
            credit=Decimal("11500.00"),
            party_id=party.id,
            description="বিক্রয় আয় ক্রেডিট",
        )
        db.add_all([entry_ar, entry_rev])
        db.commit()

        # Verify query and calculations
        saved_party = db.query(Party).filter(Party.id == party.id).first()
        assert saved_party is not None
        assert saved_party.name == "মেসার্স করিম অ্যান্ড ব্রাদার্স"
        assert saved_party.opening_balance == Decimal("5000.00")

        ledger_rows = db.query(LedgerEntry).filter(LedgerEntry.reference_id == invoice.id).all()
        assert len(ledger_rows) == 2
        total_debit = sum(row.debit for row in ledger_rows)
        total_credit = sum(row.credit for row in ledger_rows)
        assert total_debit == total_credit == Decimal("11500.00")

        # Cleanup test data (Cascading delete will remove all related rows)
        db.delete(business)
        db.delete(user)
        db.commit()
