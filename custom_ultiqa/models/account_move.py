from odoo import fields, models, api

class UTmBoolean(models.Model):
    _inherit = 'account.move.line'

    ultiqa_agent_booking = fields.Boolean(string="Paid To Agent")

class UTMAmount(models.Model):
    _inherit = 'account.move'

    ultiqa_booking_remainings = fields.Monetary(string="Amount Paid To Agent",compute='_compute_booking_remaining',store=True)
    ultiqa_total = fields.Monetary(string="Balance Amount to be Paid",compute='_compute_booking_remaining',store=True)

    @api.depends('invoice_line_ids.ultiqa_agent_booking', 'invoice_line_ids.price_subtotal', 'amount_total')
    def _compute_booking_remaining(self):
        for move in self:
            move.ultiqa_booking_remainings = sum(line.price_subtotal for line in move.invoice_line_ids if line.ultiqa_agent_booking)
            move.ultiqa_total = move.amount_total - move.ultiqa_booking_remainings