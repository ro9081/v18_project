import math

from odoo import fields, models, api


class hotel_folio_line(models.Model):
    _inherit = 'hotel_folio.line'

    ultiqa_number_of_bookings = fields.Float(string='Number of Booking Days')
    ultiqa_member_of_bookings = fields.Float(string='Membership Balanced')
    ultiqa_via = fields.Selection([('direct', 'Walk-In'), ('agent', 'Agent'), ('Member', 'Member')], "Via", default='direct')
    skip_subtotal_compute = fields.Boolean(string="Skip Subtotal Calculation", default=False)
    is_greater_checkout = fields.Boolean(string="Is Greater Checkout", default=True, compute="_compute_is_greater_checkout",  store=True)

    @api.depends('checkout_date', 'folio_id.room_lines')
    def _compute_is_greater_checkout(self):
        for line in self:
            lines = line.folio_id.room_lines.filtered(lambda l: l.checkout_date)  # Only lines with a date
            if len(lines) >= 2:
                max_checkout = max(lines.mapped('checkout_date'))
                min_checkout = min(lines.mapped('checkout_date'))
                if line.checkout_date == min_checkout:
                    line.is_greater_checkout = False
                else:
                    line.is_greater_checkout = True
            else:
                line.is_greater_checkout = True

    @api.onchange('checkout_date', 'checkin_date')
    @api.depends('checkin_date', 'checkout_date', 'product_id', 'folio_id.shop_id')
    def on_change_checkout(self):
        res = super().on_change_checkout()

        if self.checkin_date and self.checkout_date:
            check_in = self.checkin_date
            check_out = self.checkout_date
            # delta = (check_out - check_in).total_seconds() / 86400
            # day_count1 = math.ceil(float("{:.2f}".format(delta)))
            for line in self.folio_id.reservation_id.reservation_line:
                if not line.skip_subtotal_compute and line.via == 'Member':
                    line.days_of_stay = self.product_uom_qty
                # if line.ultiqa_agent_booking_days < line.number_of_days:
                #     self.skip_subtotal_compute = True
                # else:
                #     self.skip_subtotal_compute


        return res

    def write(self, vals):
        check_in = self.checkin_date
        check_out = self.checkout_date
        if vals.get('product_uom_qty') and self.skip_subtotal_compute:
            vals = vals.copy()
            vals.pop('product_uom_qty', None)
        for line in self.folio_id.reservation_id.reservation_line:
            if not self.skip_subtotal_compute and self.ultiqa_via == 'Member' and self.product_uom_qty < line.ultiqa_agent_booking_days:
                vals['price_unit'] = 0.0
                vals['skip_subtotal_compute']=False
                self.folio_id.reservation_id.ultiqa_time_share_balance_update()
        return super().write(vals)

#     @api.onchange('checkout_date', 'checkin_date')
#     @api.depends('checkin_date', 'checkout_date', 'product_id', 'folio_id.shop_id')
#     def on_change_checkout(self):
#         if self._context.get('confirming_folio'):
#             return
#         # rest of the existing code
#
class HotelFolio(models.Model):
    _inherit = 'hotel.folio'

    def action_checkout(self):
        res = super(HotelFolio, self).action_checkout()
        for folio in self:
            if folio.reservation_id.member_id and folio.reservation_id.via == 'Member':
                folio.reservation_id._update_booking_history(folio)
        return res

    @api.model
    def write(self, vals):
        res = super(HotelFolio, self).write(vals)
        if 'state' in vals and vals['state'] == 'progress':
            for folio in self:
                pos_orders = folio.pos_order_ids.filtered(lambda o: o.state not in ['paid', 'invoiced'])
                if pos_orders:
                    pos_orders.write({'state': 'paid'})
        return res
