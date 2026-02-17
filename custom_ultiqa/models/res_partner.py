from odoo import api, fields, models,_

class ResPartner(models.Model):
    _inherit = 'res.partner'
    _description = 'Partner'

    # is_member = fields.Boolean('Is Member')
    ultiqa_contact_type = fields.Selection([('agent', 'Agent'), ('member', 'Member')], default=False, string='Contact Type')
    ultiqa_membership_code = fields.Char(string='Membership Code', copy=False, tracking=True)
    ultiqa_agent_commission = fields.Float(string='Agent Commission')
    ultiqa_time_share_balance = fields.Float(string='Time Share Balance (in Days)', tracking=True)
    ultiqa_booking_history_line = fields.One2many('ultiqa.booking_history', 'member_id')

    @api.onchange('ultiqa_contact_type')
    def onchange_agent_true(self):
        if self.ultiqa_contact_type == 'agent':
            self.agent = True
        else:
            self.agent = False
