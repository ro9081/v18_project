from odoo import models, fields, _,api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    ultiqa_buyer_costcenter = fields.Char(string='buyerCostCenterId')
