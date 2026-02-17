from odoo import fields, models, api
from odoo.exceptions import ValidationError

class HotelReservationLine(models.Model):
    _inherit = "hotel.reservation.line"

    ultiqa_agent_booking_days = fields.Float(string='Membership Balance Days', store=True)
    via = fields.Selection([('direct', 'Walk-In'), ('agent', 'Agent'), ('Member', 'Member')], "Via", related='line_id.via')
    actual_number_of_days = fields.Float(string="Actual Booked Days", store=True)
    used_membership_days = fields.Float(string="Used Membership Days")
    skip_subtotal_compute = fields.Boolean(string="Skip Subtotal Calculation", default=False, compute='_compute_skip_subtotal_compute', store='True')
    days_of_stay = fields.Float(string="Days of Stay")


    # @api.onchange('checkin', 'checkout')
    # # @api.depends('line_id.shop_id')
    # def onchange_date_count_total_days(self):
    #     res = super().onchange_date_count_total_days()
    #     extra_days = 0.0
    #     if self.number_of_days > self.ultiqa_agent_booking_days:
    #         extra_days = self.number_of_days - self.ultiqa_agent_booking_days
    #         self.number_of_days = extra_days
    #
    #     return res

    @api.depends('number_of_days', 'checkin', 'checkout')
    def _compute_skip_subtotal_compute(self):
        for rec in self:
            if rec.number_of_days > rec.ultiqa_agent_booking_days and rec.via == 'Member':
                rec.skip_subtotal_compute = True
            else:
                rec.skip_subtotal_compute = False

    @api.onchange('line_id')
    def _onchange_line_id_set_member_balance(self):
        if self.line_id and self.line_id.member_id:
            self.ultiqa_agent_booking_days = self.line_id.member_id.ultiqa_time_share_balance

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'number_of_days' in vals:
                vals['actual_number_of_days'] = vals['number_of_days']
            line = self.env['hotel.reservation'].browse(vals.get('line_id'))
            if line and line.member_id:
                vals['ultiqa_agent_booking_days'] = line.member_id.ultiqa_time_share_balance
        return super().create(vals_list)

    @api.depends('actual_number_of_days', 'discount', 'price', 'taxes_id', 'number_of_days')
    def count_sub_total1(self):
        for line in self:
            base_price = line.price * (1 - (line.discount or 0.0) / 100.0)
            taxable_days = max(0, line.number_of_days - (line.ultiqa_agent_booking_days or 0.0))
            taxes = line.taxes_id.compute_all(base_price, line.line_id.currency_id, taxable_days, product=line.room_number, partner=line.line_id.partner_id)
            line.sub_total1 = taxes['total_excluded']
