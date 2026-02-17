from odoo import models, fields, _

class PosPaymenMethod(models.Model):
    _inherit = "pos.payment.method"
    vms_payment_id = fields.Many2one('vms.payment.type', string='Vms Payment Type')
