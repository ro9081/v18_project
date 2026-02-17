from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError

class PosCustomSaleInvoiceController(http.Controller):

    @http.route('/pos/create_copy_invoice', type='json', auth='user')
    def create_sale_and_refund_copy_invoice(self, move_id):
        print('==================== inside contoller')
        move = request.env['account.move'].sudo().browse(move_id)
        if not move.exists():
            return {'error': 'Invoice not found.'}
        try:
            move.action_copy_sale_and_refund_invoice()
            return {
                'success': True,
                'Invoice Number': move.name
            }
        except ValidationError as ve:
            return {
                'success': False,
                'error': str(ve)
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Unexpected error: {e}"
            }

    @http.route('/pos/order_print_data', type='json', auth='user')
    def get_order_print_data(self, move_id):
        print('==================== inside contoller')
        employee = request.env['hr.employee'].search([('user_id', '=', request.env.uid)], limit=1)
        move = request.env['account.move'].sudo().browse(move_id)
        # pos_order = request.env['post.order'].sudo().search([('account_move', '=', move.id)])
        if not move.exists():
            return {'error': 'Invoice not found.'}
        try:
            return_data = {}
            edi_data = move._get_l10n_in_edi_response_json()
            return_data['ultiqa_invoice_no'] = edi_data.get('tin', '')
            return_data['ultiqa_cashier'] = employee.ultiqa_cashier
            return_data['ultiqa_tin'] = employee.ultiqa_tin
            return_data['ultiqa_buyer_cost_center_id'] = edi_data.get('buyerCostCenterId', '')
            return_data['ultiqa_sdc_invoice_no'] = edi_data.get('invoiceNumber', '')
            # return_data['ultiqa_ref_doc_number'] = ultiqa_ref_doc_number
            # return_data['ultiqa_ref_doc_date'] = original_invoice.invoice_date
            all_labels = set()
            for line in move.invoice_line_ids:
                tax_labels = [tax.ultiqa_tax_label for tax in line.tax_ids if tax.ultiqa_tax_label] or ['B']
                all_labels.update(tax_labels)
            # return_data['ultiqa_tax_labels'] = ','.join(sorted(all_labels)) if all_labels else "B"
            return_data['ultiqa_tax_items'] = edi_data.get("taxItems", [])
            tax_lines = []
            total_tax = 0.0
            # for item in tax_items:
            #     label = item.get("label", "")
            #     name = item.get("categoryName", "")
            #     rate = item.get("rate", 0)
            #     amount = item.get("amount", 0.0)
            #     total_tax += amount
            #     tax_lines.append(f"{label} - {name} - {rate}% - {amount}")
            return_data['ultiqa_tax_lines'] = "\n".join(tax_lines)
            return_data['ultiqa_total_tax'] = total_tax
            return_data['ultiqa_journal_text'] = edi_data.get("journal", "")
            return_data['ultiqa_transaction_type'] = None
            # return_data['ultiqa_match'] = re.search(r'-{5,}(.*?)\-{5,}', journal_text)
            return return_data
        except ValidationError as ve:
            return {
                'success': False,
                'error': str(ve)
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Unexpected error: {e}"
            }