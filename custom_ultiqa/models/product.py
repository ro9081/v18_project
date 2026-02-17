from odoo import api, fields, models

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _description = 'Product'

    ultiqa_is_time_sharing = fields.Boolean(string='Is Time Sharing')

