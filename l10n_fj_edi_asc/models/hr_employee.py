from odoo import models, fields, _, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    ultiqa_cashier = fields.Char(string='Cashier')
    ultiqa_tin = fields.Char(string='TIN')
