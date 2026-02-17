from odoo import api, fields, models

class UltiqaBookingHistory(models.Model):
    _name = 'ultiqa.booking_history'
    _description = 'Booking History'

    name = fields.Char(string='Name')
    partner_id = fields.Many2one('res.partner',string='Customer Name')
    member_id = fields.Many2one('res.partner',string='Member')
    checkin_date = fields.Datetime('Check In',related='reservation_line_id.checkin')
    checkout_date = fields.Datetime('Check Out',related='reservation_line_id.checkout')
    categ_id = fields.Many2one('product.category', string='Room Type')
    room_number = fields.Many2one('product.product', string='Room Number')
    number_of_days = fields.Integer(string="Membership Days Used")
    cost_price = fields.Float(string='Price')
    subtotal = fields.Float(string='Subtotal')
    order_date = fields.Date(string='Booking Date')
    status = fields.Selection([('draft', 'Draft'), ('confirm', 'Booked'), ('done', 'Checked-In'),('checked_out', 'Checked Out'), ('cancel', 'Cancel')],string='Status')
    reservation_id = fields.Many2one('hotel.reservation', string="Reservation")
    is_balance_used = fields.Boolean(string='Used Quantity', default=False)
    reservation_line_id = fields.Many2one('hotel.reservation.line', string="Reservation")
