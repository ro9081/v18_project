# -*- coding: utf-8 -*-
import requests

from odoo import models, fields, _,api
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    module_l10n_fj_edi_asc = fields.Boolean(string='Fiji Electronic Invoicing')
    ultiqa_pfx_path = fields.Char(string="PFX Certificate Path")
    ultiqa_pfx_password = fields.Char(string="PFX Password")
    ultiqa_pac_value = fields.Char(string="PAC Header Value")
    ultiqa_base_url = fields.Char(string="URL")

    @api.model
    def get_values(self):
        res = super().get_values()
        config = self.env['ir.config_parameter'].sudo()
        res.update({
            'ultiqa_pfx_path': config.get_param('l10n_fj_edi_asc.ultiqa_pfx_path', default=''),
            'ultiqa_pfx_password': config.get_param('l10n_fj_edi_asc.ultiqa_pfx_password', default=''),
            'ultiqa_pac_value': config.get_param('l10n_fj_edi_asc.ultiqa_pac_value', default=''),
            'ultiqa_base_url': config.get_param('l10n_fj_edi_asc.ultiqa_base_url', default=''),
        })
        return res

    def set_values(self):
        super().set_values()
        config = self.env['ir.config_parameter'].sudo()
        config.set_param('l10n_fj_edi_asc.ultiqa_pfx_path', self.ultiqa_pfx_path or '')
        config.set_param('l10n_fj_edi_asc.ultiqa_pfx_password', self.ultiqa_pfx_password or '')
        config.set_param('l10n_fj_edi_asc.ultiqa_pac_value', self.ultiqa_pac_value or '')
        config.set_param('l10n_fj_edi_asc.ultiqa_base_url', self.ultiqa_base_url or '')
