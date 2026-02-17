from odoo import models, fields

class TaxLabelConfig(models.Model):
    _name = 'vsdc.tax.label.config'
    _description = 'VSDC Tax Label Mapping'

    tax_id = fields.Many2one('account.tax')
    name = fields.Char(string='Name')
