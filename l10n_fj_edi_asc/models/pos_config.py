from odoo import models, fields, _,api

class PosConig(models.Model):
    _inherit = 'pos.config'

    module_l10n_fj_edi_asc = fields.Boolean(string='Fiji Electronic Invoicing')
    ultiqa_pfx_path = fields.Binary(string="PFX Certificate Path")
    ultiqa_pfx_password = fields.Char(string="PFX Password")
    ultiqa_pac_value = fields.Char(string="PAC Header Value")
    ultiqa_base_url = fields.Char(string="URL")
    asc_allow_pdf_download = fields.Boolean('Allow PDF Download', default=True)