from odoo import models

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def action_create_payments(self):

        res = super(AccountPaymentRegister, self).action_create_payments()
        for wizard in self:
            for move in wizard.line_ids.move_id:
                if move.move_type == 'out_invoice':
                    sale_orders = move.invoice_line_ids.mapped('sale_line_ids.order_id')
                    for sale_order in sale_orders:
                        total_qty = sum(line.product_uom_qty for line in sale_order.order_line)
                        if sale_order.partner_id and sale_order.partner_id.ultiqa_contact_type == 'member' and sale_order.order_line[0].product_template_id.ultiqa_is_time_sharing:
                            sale_order.partner_id.ultiqa_time_share_balance += total_qty
        return res
