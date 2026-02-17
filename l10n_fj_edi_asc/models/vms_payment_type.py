from odoo import models, fields

class VmsPaymentType(models.Model):
    _name = 'vms.payment.type'
    _description = 'Vms Payment Type'
    _order = 'code'

    name = fields.Char(string='Name')
    code = fields.Integer(string='Payment Code', required=True, help="VMS Payment Code (0=Other, 1=Cash, 2=Card, ...)")
