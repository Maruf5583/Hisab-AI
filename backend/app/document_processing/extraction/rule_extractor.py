import re
import uuid
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.document_processing.normalization import (
    normalize_bengali_digits,
    parse_monetary_amount,
    parse_flexible_date,
)
from app.document_processing.extraction.party_matcher import match_party_name


def extract_deterministic_fields(
    raw_text: str,
    business_id: uuid.UUID,
    db: Session,
) -> Dict[str, Any]:
    """Extract candidate accounting fields and validation warnings deterministically from text."""
    if not raw_text:
        return {
            "document_type_candidate": "unknown",
            "party_name_candidate": None,
            "matched_party_id": None,
            "document_number_candidate": None,
            "issue_date_candidate": None,
            "due_date_candidate": None,
            "subtotal_candidate": None,
            "tax_amount_candidate": None,
            "total_amount_candidate": None,
            "paid_amount_candidate": None,
            "due_amount_candidate": None,
            "confidence_score": Decimal("0.0000"),
            "warnings": ["Empty or unreadable document text."],
            "metadata": {},
        }

    warnings: List[str] = []
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    # 1. Document Type Detection
    doc_type = "unknown"
    lower_text = raw_text.lower()
    if re.search(r"বিক্রয়\s*চালান|sales\s*invoice|ক্যাশ\s*মেমো|cash\s*memo", lower_text):
        doc_type = "sales_invoice"
    elif re.search(r"(?<!বি)ক্রয়\s*চালান|purchase\s*invoice|purchase\s*bill", lower_text):
        doc_type = "purchase_invoice"
    elif re.search(r"টাকা\s*জমা\s*রশিদ|মানি\s*রিসিট|রসিদ|money\s*receipt|payment\s*receipt", lower_text):
        doc_type = "payment_receipt"
    elif re.search(r"ডেবিট\s*ভাউচার|ক্রেডিট\s*ভাউচার|খরচ\s*ভাউচার|ভাউচার|voucher", lower_text):
        doc_type = "voucher"
    elif re.search(r"চালান|invoice|বিল", lower_text):
        doc_type = "sales_invoice"

    # 2. Document Number
    doc_number = None
    doc_num_pattern = r"(?:চালান\s*নং|বিল\s*নং|মেমো\s*নং|invoice\s*no\.?|inv\s*#?|bill\s*no\.?|memo\s*no\.?|voucher\s*no\.?)\s*[:\-]?\s*([A-Za-z0-9\-\/]+)"
    match_num = re.search(doc_num_pattern, raw_text, re.IGNORECASE)
    if match_num:
        doc_number = match_num.group(1).strip()
    else:
        warnings.append("Document number could not be detected automatically.")

    # 3. Issue Date
    issue_date = None
    date_pattern = r"(?:তারিখ|date)\s*[:\-]?\s*([০-৯0-9\/\-\.]+)"
    match_date = re.search(date_pattern, raw_text, re.IGNORECASE)
    if match_date:
        issue_date = parse_flexible_date(match_date.group(1))
    if not issue_date:
        # Fallback: scan any line that contains a valid date format
        for line in lines:
            d = parse_flexible_date(line)
            if d:
                issue_date = d
                break
    if not issue_date:
        warnings.append("Issue date could not be detected automatically.")

    # 4. Party Name Candidate & Fuzzy Matching
    party_name = None
    party_pattern = r"(?:নাম|ক্রেতার\s*নাম|গ্রাহক|মেসার্স|customer|buyer|client|party|bill\s*to|sold\s*to|supplier)\s*[:\-]?\s*([^\n\r,\.]+)"
    match_party = re.search(party_pattern, raw_text, re.IGNORECASE)
    if match_party:
        party_name = match_party.group(1).strip()
    elif lines:
        # Fallback: check first 2 lines for common business header
        first_line = lines[0]
        if len(first_line) > 3 and not re.search(r"invoice|চালান|বিল|তারিখ|date", first_line, re.IGNORECASE):
            party_name = first_line

    matched_party_id = None
    if party_name:
        matched_party_id, matched_name, score = match_party_name(party_name, business_id, db)
        if not matched_party_id:
            warnings.append(f"Party candidate '{party_name}' could not be matched with high confidence to an existing party.")
    else:
        warnings.append("Party name could not be detected automatically.")

    # 5. Amounts: Total, Paid, Due, Subtotal, Tax
    total_amount = None
    paid_amount = None
    due_amount = None
    subtotal = None
    tax_amount = None

    # Total Amount
    total_pattern = r"(?:সর্বমোট|মোট\s*টাকা|মোট\s*মূল্য|গ্র্যান্ড\s*টোটাল|grand\s*total|net\s*amount|total\s*amount|total)\s*[:\-]?\s*([^\n\r]+)"
    match_total = re.search(total_pattern, raw_text, re.IGNORECASE)
    if match_total:
        total_amount = parse_monetary_amount(match_total.group(1))

    # Paid Amount
    paid_pattern = r"(?:নগদ\s*পরিশোধ|জমা\s*টাকা|পরিশোধ|পেইড|paid\s*amount|cash\s*paid|cash\s*received|paid)\s*[:\-]?\s*([^\n\r]+)"
    match_paid = re.search(paid_pattern, raw_text, re.IGNORECASE)
    if match_paid:
        paid_amount = parse_monetary_amount(match_paid.group(1))

    # Due Amount
    due_pattern = r"(?:বাকি\s*টাকা|বাকি|দেনা|due\s*amount|balance\s*due|due)\s*[:\-]?\s*([^\n\r]+)"
    match_due = re.search(due_pattern, raw_text, re.IGNORECASE)
    if match_due:
        due_amount = parse_monetary_amount(match_due.group(1))

    # Subtotal
    subtotal_pattern = r"(?:উপমোট|সাবটোটাল|subtotal|sub\s*total)\s*[:\-]?\s*([^\n\r]+)"
    match_sub = re.search(subtotal_pattern, raw_text, re.IGNORECASE)
    if match_sub:
        subtotal = parse_monetary_amount(match_sub.group(1))

    # Tax Amount
    tax_pattern = r"(?:ভ্যাট|ট্যাক্স|vat|tax)\s*[:\-]?\s*([^\n\r]+)"
    match_tax = re.search(tax_pattern, raw_text, re.IGNORECASE)
    if match_tax:
        tax_amount = parse_monetary_amount(match_tax.group(1))

    # Fallback: If total not found by label, look for largest monetary amount in document
    if total_amount is None:
        all_amounts: List[Decimal] = []
        for line in lines:
            amt = parse_monetary_amount(line)
            if amt and amt > Decimal("0.00"):
                all_amounts.append(amt)
        if all_amounts:
            total_amount = max(all_amounts)
            warnings.append("Total amount inferred from largest detected value. Please verify.")
        else:
            warnings.append("Total amount could not be detected. Please input manually.")

    # 6. Mathematical Consistency Checks
    if total_amount and subtotal and tax_amount:
        if (subtotal + tax_amount) != total_amount:
            warnings.append(f"Subtotal ({subtotal}) + Tax ({tax_amount}) != Total ({total_amount})")

    if total_amount and paid_amount is not None and due_amount is not None:
        if (paid_amount + due_amount) != total_amount:
            warnings.append(f"Paid amount ({paid_amount}) + Due amount ({due_amount}) != Total ({total_amount})")

    # If total is found and paid is found but due is None, compute due
    if total_amount is not None and paid_amount is not None and due_amount is None:
        due_amount = max(Decimal("0.00"), total_amount - paid_amount)

    # 7. Confidence Score Calculation
    detected_count = sum(1 for f in [doc_number, issue_date, party_name, total_amount] if f is not None)
    confidence = Decimal(str(round(detected_count / 4.0, 2)))

    return {
        "document_type_candidate": doc_type,
        "party_name_candidate": party_name,
        "matched_party_id": matched_party_id,
        "document_number_candidate": doc_number,
        "issue_date_candidate": issue_date,
        "due_date_candidate": None,
        "subtotal_candidate": subtotal,
        "tax_amount_candidate": tax_amount,
        "total_amount_candidate": total_amount,
        "paid_amount_candidate": paid_amount,
        "due_amount_candidate": due_amount,
        "confidence_score": confidence,
        "warnings": warnings,
        "metadata": {"rule_based": True},
    }
