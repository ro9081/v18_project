import binascii
from datetime import datetime
from odoo import models, fields, api
import qrcode
import base64
import io
import logging
from dateutil import parser
import re
_logger = logging.getLogger(__name__)

class PosOrder(models.Model):
    _inherit = 'pos.order'
    ultiqa_verification_qr = fields.Binary(string="Verification QR")
    ultiqa_invoice_no = fields.Char(string='invoiceNumber')
    ultiqa_cashier = fields.Char(string='Cashier')
    ultiqa_tin = fields.Char(string='Cashier Tin')
    ultiqa_buyer_cost_center_id = fields.Char(string="Buyer's Cost Center")
    ultiqa_transaction = fields.Char(string='Transaction Type')
    ultiqa_sdc_time = fields.Datetime(string='SDC Time')
    ultiqa_sdc_invoice_no = fields.Char(string='SDC Invoice No')
    ultiqa_invoice_counter = fields.Char(string='Invoice Counter')
    ultiqa_tax_labels = fields.Char(string="Tax Labels")
    ultiqa_tax_lines = fields.Text(string="Tax Lines")
    ultiqa_total_tax = fields.Float(string="Total Tax")
    ultiqa_product_label = fields.Char(string='Product-wise Tax Labels', compute='_compute_ultiqa_product_label',store=True)
    ultiqa_ref_doc_number = fields.Char(string='Ref.Document Number')
    ultiqa_ref_doc_date = fields.Char(string='Ref.Document Date')
    ultiqa_copy_sale = fields.Char(string='Copy Sale/Refund')

    @api.depends('ultiqa_copy_sale')
    def _compute_ultiqa_copy_sale(self):
        for order in self:
            if order.ultiqa_transaction in ['COPY SALE','COPY REFUND']:
                order.ultiqa_copy_sale = order.ultiqa_transaction

    @api.depends('lines.tax_ids', 'lines.product_id', 'lines')
    def _compute_ultiqa_product_label(self):
        for order in self:
            label_parts = []
            for line in order.lines:
                product_name = line.product_id.display_name
                tax_labels = [tax.ultiqa_tax_label for tax in line.tax_ids if tax.ultiqa_tax_label] or ['B']
                label = f"{product_name}: {', '.join(tax_labels)}" if tax_labels else f"{product_name}: B"
                label_parts.append(label)
            order.ultiqa_product_label = ' | '.join(label_parts)

    @api.depends('account_move')
    def _compute_is_invoiced(self):
        res = super()._compute_is_invoiced()
        original_invoice=''
        for order in self:
            order.is_invoiced = bool(order.account_move)
            domain = [
                ('partner_id', '=', order.account_move.partner_id.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('amount_total', '=', order.account_move.amount_total),
                ('invoice_date', '<=', order.account_move.invoice_date),
            ]
            domain_advance_sale = [
                ('partner_id', '=', order.account_move.partner_id.id),
                ('state', '=', 'posted'),
                ('invoice_date', '<=', order.account_move.invoice_date),
                ('ultiqa_ref_doc_number', '!=', False),
                ('amount_total', '>', 0.0),
                ('invoice_line_ids.product_id.name', '=', 'Down Payment (POS)')]
            employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            original_invoice = self.env['account.move'].search(domain, order='invoice_date desc', limit=1)
            has_down_payment = any(
                line.product_id.name.lower() == "down payment (pos)" and
                line.quantity < 0 and
                line.price_subtotal < 0
                for line in order.account_move.invoice_line_ids.filtered(
                    lambda l: l.display_type not in ('line_note', 'line_section', 'rounding')))
            if has_down_payment:
                original_invoice = self.env['account.move'].search(domain_advance_sale,  limit=1)
            if order.is_invoiced:
                edi_data = order.account_move._get_l10n_in_edi_response_json()
                order.ultiqa_invoice_no = edi_data.get('tin', '')
                order.ultiqa_cashier = employee.ultiqa_cashier
                order.ultiqa_tin = employee.ultiqa_tin
                order.ultiqa_buyer_cost_center_id = edi_data.get('buyerCostCenterId', '')
                order.ultiqa_sdc_invoice_no = edi_data.get('invoiceNumber', '')
                order.ultiqa_ref_doc_number = original_invoice.ultiqa_ref_doc_number
                order.ultiqa_ref_doc_date = original_invoice.invoice_date
                all_labels = set()
                for line in order.account_move.invoice_line_ids:
                    tax_labels = [tax.ultiqa_tax_label for tax in line.tax_ids if tax.ultiqa_tax_label] or ['B']
                    all_labels.update(tax_labels)
                order.ultiqa_tax_labels = ','.join(sorted(all_labels)) if all_labels else "B"
                tax_items = edi_data.get("taxItems", [])
                tax_lines = []
                total_tax = 0.0
                for item in tax_items:
                    label = item.get("label", "")
                    name = item.get("categoryName", "")
                    rate = item.get("rate", 0)
                    amount = item.get("amount", 0.0)
                    total_tax += amount
                    tax_lines.append(f"{label} - {name} - {rate}% - {amount}")
                order.ultiqa_tax_lines = "\n".join(tax_lines)
                order.ultiqa_total_tax = total_tax
                journal_text = edi_data.get("journal", "")
                transaction_type = None
                match = re.search(r'-{5,}(.*?)\-{5,}', journal_text)
                if match:
                    transaction_type = match.group(1).strip()
                    allowed_types = ['PROFORMA SALE','PROFORMA REFUND','NORMAL REFUND', 'NORMAL SALE', 'ADVANCE SALE', 'ADVANCE REFUND','COPY SALE','COPY REFUND']
                    if transaction_type in allowed_types:
                        self.ultiqa_transaction = transaction_type
                    else:
                        _logger.warning("Unknown transactionType received: %s", transaction_type)
                        order.ultiqa_transaction = False
                sdc_datetime_str = edi_data.get('sdcDateTime')
                if sdc_datetime_str:
                    try:
                        dt = parser.isoparse(sdc_datetime_str)
                        # convert to naive datetime (remove timezone info)
                        dt_naive = dt.astimezone().replace(tzinfo=None)
                        order.ultiqa_sdc_time = dt_naive
                    except Exception as e:
                        _logger.error("Error parsing sdcDateTime: %s - %s", sdc_datetime_str, e)
                        order.ultiqa_sdc_time = False
                else:
                    order.ultiqa_sdc_time = False
                order.ultiqa_invoice_counter = edi_data.get('invoiceCounter', '')
                img_str = edi_data.get('verificationQRCode', '')
                if img_str:
                    img_str = img_str + '=' * (-len(img_str) % 4)
                    try:
                        base64.b64decode(img_str)
                        order.ultiqa_verification_qr = img_str
                    except binascii.Error:
                        _logger.warning("Invalid base64 QR code in invoice: %s", img_str)
                        order.ultiqa_verification_qr = False
        return res