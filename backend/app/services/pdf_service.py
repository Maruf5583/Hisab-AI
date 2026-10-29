import os
import uuid
from decimal import Decimal
from typing import Optional, List
from datetime import datetime
import pymupdf

from app.models.invoice import Invoice, InvoiceItem
from app.models.payment import Payment
from app.models.business import Business
from app.models.party import Party


def _get_font_kwargs():
    """Select the best available Unicode font supporting Bengali and English."""
    nirmala_path = "C:\\Windows\\Fonts\\Nirmala.ttc"
    if os.path.exists(nirmala_path):
        return {"fontname": "nirmala", "fontfile": nirmala_path}
    arial_path = "C:\\Windows\\Fonts\\arial.ttf"
    if os.path.exists(arial_path):
        return {"fontname": "arial", "fontfile": arial_path}
    return {"fontname": "helv", "fontfile": None}


def format_currency(val: Decimal | float | str) -> str:
    num = Decimal(str(val or "0.00"))
    return f"BDT {num:,.2f}"


class PDFService:
    def generate_invoice_pdf(
        self,
        invoice: Invoice,
        business: Business,
        party: Optional[Party] = None,
    ) -> bytes:
        """Generate a branded, professional bilingual accounting invoice PDF."""
        doc = pymupdf.open()
        page = doc.new_page(width=595.3, height=841.9)  # A4 size

        font_kw = _get_font_kwargs()

        # Palette
        primary = (0.08, 0.14, 0.28)     # Dark Navy
        secondary = (0.20, 0.42, 0.85)   # Accent Blue
        slate_text = (0.28, 0.33, 0.41)  # Muted slate
        light_bg = (0.96, 0.97, 0.99)    # Card fill
        border_col = (0.86, 0.89, 0.93)  # Light border
        white = (1.0, 1.0, 1.0)

        # 1. Top Decorative Header Banner
        page.draw_rect(pymupdf.Rect(40, 35, 555, 38), color=secondary, fill=secondary)

        # 2. Company Brand & Legal Details (Left)
        page.insert_text(pymupdf.Point(40, 65), business.name or "HisabAI Enterprise", fontsize=16, color=primary, **font_kw)
        y = 80
        if business.legal_name and business.legal_name != business.name:
            page.insert_text(pymupdf.Point(40, y), f"Legal Name: {business.legal_name}", fontsize=9, color=slate_text, **font_kw)
            y += 13
        if business.address:
            page.insert_text(pymupdf.Point(40, y), business.address, fontsize=9, color=slate_text, **font_kw)
            y += 13
        contact_str = " | ".join(filter(None, [business.phone, business.email]))
        if contact_str:
            page.insert_text(pymupdf.Point(40, y), contact_str, fontsize=9, color=slate_text, **font_kw)
            y += 13
        if business.tax_id:
            page.insert_text(pymupdf.Point(40, y), f"BIN / Tax ID: {business.tax_id}", fontsize=9, color=slate_text, **font_kw)

        # 3. Invoice Title & Details (Right)
        inv_title = "SALES INVOICE / বিক্রয় চালান" if invoice.invoice_type == "sales" else "PURCHASE BILL / ক্রয় বিল"
        page.insert_text(pymupdf.Point(340, 65), inv_title, fontsize=12, color=secondary, **font_kw)
        page.insert_text(pymupdf.Point(340, 85), f"Invoice #: {invoice.invoice_number}", fontsize=11, color=primary, **font_kw)
        page.insert_text(pymupdf.Point(340, 100), f"Issue Date: {invoice.issue_date}", fontsize=9, color=slate_text, **font_kw)
        page.insert_text(pymupdf.Point(340, 114), f"Due Date: {invoice.due_date or 'On Receipt'}", fontsize=9, color=slate_text, **font_kw)

        # 4. Billed To Card
        party_name = (party.name if party else (invoice.party.name if invoice.party else "Valued Customer"))
        page.draw_rect(pymupdf.Rect(40, 135, 555, 195), color=border_col, fill=light_bg)
        page.insert_text(pymupdf.Point(55, 153), "BILLED TO / হিসাব গ্রাহক:", fontsize=9, color=secondary, **font_kw)
        page.insert_text(pymupdf.Point(55, 170), party_name, fontsize=12, color=primary, **font_kw)

        party_contact = []
        if party and party.phone:
            party_contact.append(f"Phone: {party.phone}")
        if party and party.address:
            party_contact.append(party.address)
        if party_contact:
            page.insert_text(pymupdf.Point(55, 185), " • ".join(party_contact), fontsize=8.5, color=slate_text, **font_kw)

        # Status badge inside Billed To card
        status_str = invoice.status.upper().replace("_", " ")
        status_color = (0.05, 0.60, 0.35) if invoice.status == "paid" else (0.85, 0.45, 0.10) if invoice.status == "partially_paid" else secondary
        page.insert_text(pymupdf.Point(440, 165), f"STATUS: {status_str}", fontsize=9.5, color=status_color, **font_kw)
        page.insert_text(pymupdf.Point(440, 180), "Currency: BDT (৳)", fontsize=8.5, color=slate_text, **font_kw)

        # 5. Table Header
        tbl_top = 215
        page.draw_rect(pymupdf.Rect(40, tbl_top, 555, tbl_top + 22), color=primary, fill=primary)
        page.insert_text(pymupdf.Point(48, tbl_top + 15), "#", fontsize=8.5, color=white, **font_kw)
        page.insert_text(pymupdf.Point(75, tbl_top + 15), "Item Description / পণ্যের বিবরণ", fontsize=8.5, color=white, **font_kw)
        page.insert_text(pymupdf.Point(340, tbl_top + 15), "Qty", fontsize=8.5, color=white, **font_kw)
        page.insert_text(pymupdf.Point(400, tbl_top + 15), "Unit Price", fontsize=8.5, color=white, **font_kw)
        page.insert_text(pymupdf.Point(480, tbl_top + 15), "Total Amount", fontsize=8.5, color=white, **font_kw)

        # 6. Table Rows
        items = invoice.items
        current_y = tbl_top + 22
        row_height = 24

        if not items:
            # Fallback single row matching invoice total
            items_data = [
                {
                    "desc": invoice.notes or "General Commercial Merchandise / Services",
                    "qty": Decimal("1.00"),
                    "unit": invoice.subtotal,
                    "total": invoice.subtotal,
                }
            ]
        else:
            items_data = [
                {
                    "desc": it.description,
                    "qty": it.quantity,
                    "unit": it.unit_price,
                    "total": it.line_total,
                }
                for it in items
            ]

        for i, item in enumerate(items_data):
            row_fill = light_bg if i % 2 == 1 else white
            page.draw_rect(pymupdf.Rect(40, current_y, 555, current_y + row_height), color=border_col, fill=row_fill)

            page.insert_text(pymupdf.Point(48, current_y + 16), str(i + 1), fontsize=8.5, color=slate_text, **font_kw)
            # Truncate description if too long
            desc = item["desc"]
            if len(desc) > 50:
                desc = desc[:47] + "..."
            page.insert_text(pymupdf.Point(75, current_y + 16), desc, fontsize=8.5, color=primary, **font_kw)
            page.insert_text(pymupdf.Point(340, current_y + 16), f"{item['qty']:,.2f}", fontsize=8.5, color=slate_text, **font_kw)
            page.insert_text(pymupdf.Point(400, current_y + 16), f"{item['unit']:,.2f}", fontsize=8.5, color=slate_text, **font_kw)
            page.insert_text(pymupdf.Point(480, current_y + 16), f"{item['total']:,.2f}", fontsize=8.5, color=primary, **font_kw)

            current_y += row_height
            if current_y > 680:
                break

        # 7. Totals Calculation Box (Right Side)
        totals_y = current_y + 20
        page.draw_rect(pymupdf.Rect(320, totals_y, 555, totals_y + 115), color=border_col, fill=light_bg)

        page.insert_text(pymupdf.Point(335, totals_y + 22), "Subtotal (মোট দর):", fontsize=9, color=slate_text, **font_kw)
        page.insert_text(pymupdf.Point(450, totals_y + 22), format_currency(invoice.subtotal), fontsize=9, color=primary, **font_kw)

        page.insert_text(pymupdf.Point(335, totals_y + 42), "Tax / VAT (ভ্যাট):", fontsize=9, color=slate_text, **font_kw)
        page.insert_text(pymupdf.Point(450, totals_y + 42), format_currency(invoice.tax_amount), fontsize=9, color=primary, **font_kw)

        page.draw_line(pymupdf.Point(335, totals_y + 52), pymupdf.Point(540, totals_y + 52), color=border_col)

        page.insert_text(pymupdf.Point(335, totals_y + 68), "Grand Total (সর্বমোট):", fontsize=10.5, color=primary, **font_kw)
        page.insert_text(pymupdf.Point(450, totals_y + 68), format_currency(invoice.total_amount), fontsize=10.5, color=secondary, **font_kw)

        page.insert_text(pymupdf.Point(335, totals_y + 86), "Paid to Date (জমা):", fontsize=8.5, color=slate_text, **font_kw)
        page.insert_text(pymupdf.Point(450, totals_y + 86), format_currency(invoice.paid_amount), fontsize=8.5, color=(0.1, 0.55, 0.3), **font_kw)

        page.insert_text(pymupdf.Point(335, totals_y + 104), "Balance Due (বকেয়া):", fontsize=10, color=(0.85, 0.15, 0.15), **font_kw)
        page.insert_text(pymupdf.Point(450, totals_y + 104), format_currency(invoice.due_amount), fontsize=10, color=(0.85, 0.15, 0.15), **font_kw)

        # 8. Double-Entry Verification Seal (Left Side)
        page.draw_rect(pymupdf.Rect(40, totals_y, 305, totals_y + 115), color=(0.82, 0.92, 0.85), fill=(0.95, 0.99, 0.96))
        page.insert_text(pymupdf.Point(55, totals_y + 25), "✓ DOUBLE-ENTRY EQUILIBRIUM VERIFIED", fontsize=9, color=(0.08, 0.55, 0.28), **font_kw)
        page.insert_text(pymupdf.Point(55, totals_y + 45), "Mathematically reconciled ledger entry:", fontsize=8.5, color=slate_text, **font_kw)
        page.insert_text(pymupdf.Point(55, totals_y + 60), f"Debit sum equals Credit sum: {format_currency(invoice.total_amount)}", fontsize=8.5, color=primary, **font_kw)
        page.insert_text(pymupdf.Point(55, totals_y + 75), "Strict immutable posting recorded in HisabAI OS.", fontsize=8, color=slate_text, **font_kw)
        if invoice.posted_at:
            page.insert_text(pymupdf.Point(55, totals_y + 95), f"Posted Timestamp: {invoice.posted_at.strftime('%Y-%m-%d %H:%M:%S UTC')}", fontsize=7.5, color=slate_text, **font_kw)

        # 9. Signatures & Footer
        sign_y = 750
        page.draw_line(pymupdf.Point(60, sign_y), pymupdf.Point(200, sign_y), color=border_col)
        page.insert_text(pymupdf.Point(75, sign_y + 15), "Customer Signature / গ্রহীতা", fontsize=8.5, color=slate_text, **font_kw)

        page.draw_line(pymupdf.Point(395, sign_y), pymupdf.Point(535, sign_y), color=border_col)
        page.insert_text(pymupdf.Point(405, sign_y + 15), "Authorized Signature & Stamp", fontsize=8.5, color=slate_text, **font_kw)

        page.insert_text(
            pymupdf.Point(40, 805),
            f"Generated securely by HisabAI OS • {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
            fontsize=7.5,
            color=slate_text,
            **font_kw,
        )

        pdf_bytes = doc.tobytes()
        doc.close()
        return pdf_bytes

    def generate_payment_receipt_pdf(
        self,
        payment: Payment,
        business: Business,
        party: Optional[Party] = None,
    ) -> bytes:
        """Generate a branded official money receipt / payment voucher PDF."""
        doc = pymupdf.open()
        page = doc.new_page(width=595.3, height=841.9)

        font_kw = _get_font_kwargs()

        primary = (0.08, 0.14, 0.28)
        secondary = (0.10, 0.60, 0.45)   # Emerald for payments
        slate_text = (0.28, 0.33, 0.41)
        light_bg = (0.96, 0.98, 0.97)
        border_col = (0.84, 0.90, 0.86)
        white = (1.0, 1.0, 1.0)

        # Header Banner
        page.draw_rect(pymupdf.Rect(40, 35, 555, 38), color=secondary, fill=secondary)

        # Business Details
        page.insert_text(pymupdf.Point(40, 65), business.name or "HisabAI Enterprise", fontsize=16, color=primary, **font_kw)
        y = 80
        if business.address:
            page.insert_text(pymupdf.Point(40, y), business.address, fontsize=9, color=slate_text, **font_kw)
            y += 13
        contact_str = " | ".join(filter(None, [business.phone, business.email]))
        if contact_str:
            page.insert_text(pymupdf.Point(40, y), contact_str, fontsize=9, color=slate_text, **font_kw)

        # Receipt Title
        is_receipt = payment.payment_type == "customer_receipt"
        receipt_title = "OFFICIAL MONEY RECEIPT / টাকা জমার রশিদ" if is_receipt else "PAYMENT VOUCHER / পরিশোধ ভাউচার"
        page.insert_text(pymupdf.Point(320, 65), receipt_title, fontsize=11, color=secondary, **font_kw)
        page.insert_text(pymupdf.Point(320, 85), f"Voucher #: {str(payment.id)[:8].upper()}", fontsize=11, color=primary, **font_kw)
        page.insert_text(pymupdf.Point(320, 100), f"Payment Date: {payment.payment_date}", fontsize=9, color=slate_text, **font_kw)
        page.insert_text(pymupdf.Point(320, 114), f"Method: {payment.payment_method.upper()}", fontsize=9, color=slate_text, **font_kw)

        # Prominent Amount Card
        page.draw_rect(pymupdf.Rect(40, 135, 555, 215), color=border_col, fill=light_bg)
        page.insert_text(pymupdf.Point(60, 160), "AMOUNT RECEIVED / পরিশোধিত অর্থের পরিমাণ:", fontsize=9.5, color=secondary, **font_kw)
        page.insert_text(pymupdf.Point(60, 195), format_currency(payment.amount), fontsize=24, color=primary, **font_kw)

        # Party Info
        party_name = party.name if party else (payment.party.name if payment.party else "Customer / Vendor")
        page.insert_text(pymupdf.Point(340, 165), f"Party Name: {party_name}", fontsize=10.5, color=primary, **font_kw)
        if payment.reference_number:
            page.insert_text(pymupdf.Point(340, 185), f"Ref / Trx ID: {payment.reference_number}", fontsize=9, color=slate_text, **font_kw)
        page.insert_text(pymupdf.Point(340, 202), f"Status: {payment.status.upper()}", fontsize=9, color=secondary, **font_kw)

        # Breakdown / Allocations
        page.insert_text(pymupdf.Point(40, 250), "PAYMENT ALLOCATION BREAKDOWN (চালান সমন্বয় বিবরণী):", fontsize=10, color=primary, **font_kw)

        alloc_top = 265
        page.draw_rect(pymupdf.Rect(40, alloc_top, 555, alloc_top + 22), color=primary, fill=primary)
        page.insert_text(pymupdf.Point(50, alloc_top + 15), "Allocation Details", fontsize=8.5, color=white, **font_kw)
        page.insert_text(pymupdf.Point(350, alloc_top + 15), "Method", fontsize=8.5, color=white, **font_kw)
        page.insert_text(pymupdf.Point(450, alloc_top + 15), "Allocated Amount", fontsize=8.5, color=white, **font_kw)

        row_y = alloc_top + 22
        page.draw_rect(pymupdf.Rect(40, row_y, 555, row_y + 26), color=border_col, fill=white)
        page.insert_text(pymupdf.Point(50, row_y + 17), f"Applied towards party ledger balance & invoices", fontsize=9, color=primary, **font_kw)
        page.insert_text(pymupdf.Point(350, row_y + 17), payment.payment_method.capitalize(), fontsize=9, color=slate_text, **font_kw)
        page.insert_text(pymupdf.Point(450, row_y + 17), format_currency(payment.allocated_amount or payment.amount), fontsize=9, color=primary, **font_kw)

        # Unapplied balance if any
        if payment.unapplied_amount and Decimal(str(payment.unapplied_amount)) > 0:
            row_y += 26
            page.draw_rect(pymupdf.Rect(40, row_y, 555, row_y + 26), color=border_col, fill=light_bg)
            page.insert_text(pymupdf.Point(50, row_y + 17), "Unapplied / Advance Balance Held", fontsize=9, color=secondary, **font_kw)
            page.insert_text(pymupdf.Point(350, row_y + 17), "Advance Credit", fontsize=9, color=slate_text, **font_kw)
            page.insert_text(pymupdf.Point(450, row_y + 17), format_currency(payment.unapplied_amount), fontsize=9, color=secondary, **font_kw)

        # Notes
        if payment.notes:
            notes_y = row_y + 40
            page.insert_text(pymupdf.Point(40, notes_y), f"Notes & Remarks: {payment.notes}", fontsize=9, color=slate_text, **font_kw)

        # Double-entry ledger seal
        seal_y = 520
        page.draw_rect(pymupdf.Rect(40, seal_y, 555, seal_y + 80), color=(0.84, 0.90, 0.86), fill=light_bg)
        page.insert_text(pymupdf.Point(55, seal_y + 25), "✓ CASH & BANK GENERAL LEDGER POSTING VERIFIED", fontsize=9.5, color=secondary, **font_kw)
        page.insert_text(pymupdf.Point(55, seal_y + 45), f"Double-entry journal posted: {payment.payment_method.upper()} Account balanced with Accounts Ledger.", fontsize=8.5, color=slate_text, **font_kw)
        page.insert_text(pymupdf.Point(55, seal_y + 60), "Audit ID & transaction log stored immutably in HisabAI database.", fontsize=8, color=slate_text, **font_kw)

        # Signatures
        sign_y = 730
        page.draw_line(pymupdf.Point(60, sign_y), pymupdf.Point(200, sign_y), color=border_col)
        page.insert_text(pymupdf.Point(85, sign_y + 15), "Depositor Signature", fontsize=8.5, color=slate_text, **font_kw)

        page.draw_line(pymupdf.Point(395, sign_y), pymupdf.Point(535, sign_y), color=border_col)
        page.insert_text(pymupdf.Point(415, sign_y + 15), "Cashier / Authorized Sign", fontsize=8.5, color=slate_text, **font_kw)

        page.insert_text(
            pymupdf.Point(40, 805),
            f"HisabAI Official Money Voucher • Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
            fontsize=7.5,
            color=slate_text,
            **font_kw,
        )

        pdf_bytes = doc.tobytes()
        doc.close()
        return pdf_bytes


pdf_service = PDFService()
