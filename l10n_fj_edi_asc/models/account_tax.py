from odoo import models, fields

class TaxLabelConfig(models.Model):
    _inherit = 'account.tax'
    _description = 'Tax'

    ultiqa_tax_label = fields.Char(string='Fiji Tax Label')
