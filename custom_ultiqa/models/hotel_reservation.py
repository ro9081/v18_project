from datetime import timedelta, datetime, date
from odoo import fields, models, api

class HotelReservation(models.Model):
    _inherit = 'hotel.reservation'

    via = fields.Selection([('direct', 'Walk-In'), ('agent', 'Agent'), ('Member', 'Member')], "Via", default='direct')
    member_id = fields.Many2one('res.partner', string='Member')
    membership_days_used = fields.Float(string="Membership Days Used", compute='_compute_membership_days_used', store=False)

    def _auto_split_member_lines(self):
        used_days = 0.0
        for rec in self:
            if rec.reservation_line and len(rec.reservation_line) == 1:
                line = rec.reservation_line[0]
                if line.number_of_days > line.ultiqa_agent_booking_days and line.via == 'Member' and line.ultiqa_agent_booking_days > 0:
                    used_days = line.ultiqa_agent_booking_days or 0.0
                    extra_days = line.number_of_days - used_days
                    checkin = line.checkin
                    if isinstance(checkin, datetime):
                        checkin = checkin.date()
                    used_checkout = checkin + timedelta(days=used_days)
                    extra_checkout = checkin + timedelta(days=line.number_of_days)
                    rec.write({
                        'reservation_line': [
                            (1, line.id, {
                                'number_of_days': used_days,
                                'sub_total1': 0.0,
                                'skip_subtotal_compute': False,
                                'checkin': checkin,
                                'checkout': used_checkout,
                                'days_of_stay':line.ultiqa_agent_booking_days
                            }),
                            (0, 0, {
                                'checkin': checkin,
                                'checkout': extra_checkout,
                                'company_id': line.company_id.id,
                                'categ_id': line.categ_id.id,
                                'room_number': line.room_number.id,
                                'number_of_days': extra_days,
                                'days_of_stay': extra_days,
                                'ultiqa_agent_booking_days': line.ultiqa_agent_booking_days,
                                'via': 'Member',
                                'price': line.price,
                                'sub_total1': line.sub_total1,
                                'discount': line.discount,
                                'skip_subtotal_compute': True,
                            }),
                        ]
                    })
                else:
                    line.days_of_stay = line.number_of_days

    def _get_subtotal_amount(self):
        res = super()._get_subtotal_amount()
        for obj in self:
            total = 0.0
            if obj.id:
                for line in obj.reservation_line:
                    if line.skip_subtotal_compute and line.via == 'Member':
                        total += line.sub_total1
                obj.untaxed_amt = total
            else:
                obj.untaxed_amt = 0.0

        return res

    @api.model_create_multi
    def create(self, vals_list):
        new_records = super().create(vals_list)
        new_records._auto_split_member_lines()
        return new_records

    def write(self, vals):
        res = super().write(vals)
        self._auto_split_member_lines()
        if 'number_of_days' in vals:
            self.ultiqa_time_share_balance_update()
        return res

    def ultiqa_time_share_balance_update(self):
        """
        ADD Back Time
        share Balance
        """
        for reservation in self:
            for line in reservation.reservation_line:
                domain = [('reservation_id', '=', reservation.id), ('reservation_line_id', '=', line.id)]
                existing_history = self.env['ultiqa.booking_history'].search(domain, limit=1)
                if not line.skip_subtotal_compute and existing_history and reservation.member_id and reservation.via == 'Member' and line.ultiqa_agent_booking_days >= line.number_of_days:
                    existing_history.write({'number_of_days': line.days_of_stay})
                    reservation.member_id.ultiqa_time_share_balance = line.ultiqa_agent_booking_days - existing_history.number_of_days

    @api.depends('reservation_line.number_of_days', 'reservation_line.ultiqa_agent_booking_days')
    def _compute_membership_days_used(self):
        for reservation in self:
            total_used = 0
            if reservation.member_id and reservation.via == 'Member':
                available_balance = reservation.member_id.ultiqa_time_share_balance
                for line in reservation.reservation_line:
                    line_used = min(line.number_of_days, available_balance)
                    total_used += line_used
                    available_balance -= line_used
            reservation.membership_days_used = total_used

    @api.onchange('partner_id')
    def _onchange_partner_id_set_member(self):
        if self.partner_id and self.partner_id.ultiqa_contact_type == 'member':
            self.via = 'Member'
            self.member_id = self.partner_id
        else:
            self.via = 'direct'
            self.member_id = False

    def _update_ultiqa_time_share_balance(self):
        for reservation in self:
            if reservation.member_id and reservation.via == 'Member' and reservation.membership_days_used > 0:
                new_balance = max(reservation.member_id.ultiqa_time_share_balance - reservation.membership_days_used, 0.0)
                reservation.member_id.ultiqa_time_share_balance = new_balance

    def confirmed_reservation(self):
        res = super(HotelReservation, self).confirmed_reservation()
        for reservation in self:
            if reservation.member_id and reservation.via == 'Member':
                reservation._update_booking_history()
                reservation._update_ultiqa_time_share_balance()
        return res

    def done(self):
        res = super(HotelReservation, self).done()
        for reservation in self:
            if reservation.member_id and reservation.via == 'Member':
                reservation._update_booking_history()
        return res

    def _update_booking_history(self,folio=None):
        for reservation in self:
            if not (reservation.member_id and reservation.via == 'Member'):
                continue
            current_balance = reservation.member_id.ultiqa_time_share_balance
            for line in reservation.reservation_line:
                if current_balance >= line.number_of_days:
                    history_days = line.number_of_days
                    current_balance -= line.number_of_days
                else:
                    history_days = current_balance
                    current_balance = 0
                existing_history = self.env['ultiqa.booking_history'].search([('reservation_id', '=', reservation.id), ('reservation_line_id', '=', line.id)], limit=1)
                if existing_history:
                    valid_status_mapping = {
                        'check_out': 'checked_out',
                        'done': 'done',
                        'draft': 'draft',
                        'confirm': 'confirm',
                        'cancel': 'cancel'
                    }
                    folio_status = reservation.state
                    if folio:
                        folio_status = folio.state
                    combined_status = valid_status_mapping.get(folio_status, 'draft')

                    existing_history.write({
                        'status': combined_status
                    })
                else:
                    self.env['ultiqa.booking_history'].create({
                        'name': reservation.name,
                        'partner_id': reservation.partner_id.id,
                        'order_date': reservation.date_order,
                        'checkin_date': line.checkin,
                        'checkout_date': line.checkout,
                        'categ_id': line.categ_id.id,
                        'room_number': line.room_number.id,
                        'number_of_days': history_days,
                        'cost_price': line.price,
                        'subtotal': line.sub_total1,
                        'status': reservation.state,
                        'member_id': reservation.member_id.id,
                        'reservation_id': reservation.id,
                        'reservation_line_id': line.id,
                        'is_balance_used': history_days > 0
                    })

    def create_folio(self):
        for reservation in self:
            if reservation.via == 'Member' and any(line.ultiqa_agent_booking_days > 0 for line in reservation.reservation_line):
                folio = self.env['hotel.folio'].create({
                    'payment_move_ids': reservation.payment_move_ids.ids,
                    'date_order': reservation.date_order,
                    'shop_id': reservation.shop_id.id,
                    'partner_id': reservation.partner_id.id,
                    'pricelist_id': reservation.pricelist_id.id,
                    'partner_invoice_id': reservation.partner_id.id,
                    'partner_shipping_id': reservation.partner_id.id,
                    'reservation_id': reservation.id,
                    'note': reservation.note,
                })
                for line in reservation.reservation_line:
                    extra_days=0.0
                    if line.number_of_days > line.ultiqa_agent_booking_days:
                        extra_days = line.number_of_days - line.ultiqa_agent_booking_days
                    self.env["hotel_folio.line"].create({
                        'folio_id': folio.id,
                        'product_id': line.room_number.id,
                        'name': line.room_number.name,
                        'product_uom': line.room_number.uom_id.id,
                        'price_unit': 0.0 if not line.skip_subtotal_compute else line.price,
                        'product_uom_qty': extra_days if line.skip_subtotal_compute else line.number_of_days,
                        'checkin_date': line.checkin,
                        'checkout_date': line.checkout,
                        'discount': line.discount,
                        'tax_id': [(6, 0, line.taxes_id.ids)],
                        'categ_id': line.room_number.categ_id.id,
                        'hotel_reservation_line_id': line.id,
                        'ultiqa_via':'Member',
                        'skip_subtotal_compute': line.skip_subtotal_compute if line.skip_subtotal_compute else False
                    })
                reservation.id_line_ids.write({'folio_id': folio.id})
                for mv in reservation.account_move_ids:
                    self._cr.execute(
                        'INSERT INTO sale_account_move_rel(sale_id, move_id) VALUES (%s, %s)',
                        (folio.id, mv.id)
                    )
                reservation.reservation_line.write({'checkin': reservation.reservation_line[0].checkin})
                reservation.write({
                    'state': 'done',
                    'agent_comm': reservation.total_cost1
                })
            else:
                super(HotelReservation, self).create_folio()


