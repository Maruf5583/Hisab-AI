import uuid
from decimal import Decimal
from datetime import date
import pytest
from app.core.database import Base
from app.models import (
    User,
    Business,
    BusinessMembership,
    Party,
    Document,
    DocumentPage,
    DocumentExtraction,
    Invoice,
    InvoiceItem,
    Payment,
    PaymentAllocation,
    LedgerEntry,
    AuditLog,
    IdempotencyRecord,
)
from app.schemas.party import PartyCreate
from app.schemas.invoice import InvoiceCreate


def test_models_metadata_tables():
    """Verify that all 14 tables are registered on Base.metadata."""
    table_names = set(Base.metadata.tables.keys())
    expected_tables = {
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
    assert expected_tables.issubset(table_names), f"Missing tables: {expected_tables - table_names}"


def test_party_schema_with_bengali_support():
    party_data = {
        "name": "মেসার্স রহিম ট্রেডার্স (Rahim Traders)",
        "party_type": "buyer",
        "phone": "01711000000",
        "address": "কারওয়ান বাজার, ঢাকা (Karwan Bazar, Dhaka)",
        "opening_balance": Decimal("15000.50"),
        "opening_balance_type": "receivable",
    }
    party = PartyCreate(**party_data)
    assert party.name == "মেসার্স রহিম ট্রেডার্স (Rahim Traders)"
    assert party.opening_balance == Decimal("15000.50")
    assert isinstance(party.opening_balance, Decimal)


def test_invoice_schema_monetary_precision():
    invoice_data = {
        "party_id": uuid.uuid4(),
        "invoice_type": "sales",
        "invoice_number": "INV-2026-001",
        "issue_date": date(2026, 10, 28),
        "subtotal": Decimal("1000.25"),
        "tax_amount": Decimal("150.04"),
        "total_amount": Decimal("1150.29"),
        "notes": "চালান নং ১২৩৪৫ - সম্পূর্ণ ক্যাশ লেনদেন",
    }
    invoice = InvoiceCreate(**invoice_data)
    assert invoice.total_amount == Decimal("1150.29")
    assert invoice.subtotal + invoice.tax_amount == invoice.total_amount
