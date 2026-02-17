

from odoo import models, fields, api
from datetime import datetime,date, timedelta
import pytz


class Hotel_dashboard(models.Model):
    _inherit = 'hotel.reservation'



    def search_reserve_room(self,room_id,cater_id,shop_id):


        room_id = int(room_id)
        cater_id = int(cater_id)
        shop_id = int(shop_id) if shop_id else False

        hotel_reservation_id = self.env['hotel.reservation'].search([('shop_id', '=', shop_id)],limit=1)

        customer_name = ''
        if hotel_reservation_id:
            customer_name = hotel_reservation_id.partner_id.name

        categ_id = self.env['hotel.room_type'].search([('id','=',cater_id)])
        cat_id = categ_id.cat_id.id
        rooms = self.env['hotel.room'].search([('id','=',room_id)])
        room_id = rooms.product_id.id
        res = self.env['hotel.reservation.line'].search([
                ('room_number', '=', room_id),
                ('categ_id', '=', cat_id),
            ])
        reservations = []
        for line in res:
            reservation = line.line_id
            customer_name = reservation.partner_id.name
            customer_namestr = str(reservation.partner_id.name)
            first_name = customer_namestr.split()[0]
            #space_index = customer_namestr.find(' ')
            #first_name = customer_namestr[:space_index]
            print("cccccccccccccccccccccccccccccccccccc",first_name)
            reservations.append({
                'checkin': line.checkin,
                'checkout': line.checkout,
                'status': reservation.state,
                'id': reservation.id,
                'ref_no': reservation.reservation_no,
                'customer_name': first_name,
            })

        return {'reservations': reservations}


    def search_folio(self,shop_id):
        shop_id = int(shop_id) if shop_id else False
        print("_____________________________________________________SHOP ID______________________________________",shop_id)
        fo = self.env['hotel_folio.line'].search([('folio_id.shop_id.id','=',shop_id)])
        folio = []
        for i in fo:
            customer_namestr = str(i.folio_id.reservation_id.partner_id.name)
            first_name = customer_namestr.split()[0]
            folio.append({
                'checkin': i.checkin_date,
                'customer_name': first_name,
                'checkout':i.checkout_date,
                'status':i.folio_id.state,
                'id':i.folio_id.id,
                'room_name':i.product_id.name,
                'fol_no':i.folio_id.reservation_id.reservation_no,
            })
        return folio

    def search_cleaning(self,shop_id):
        shop_id = int(shop_id) if shop_id else False
        clean = self.env['hotel.housekeeping'].search([('room_no.shop_id.id','=',shop_id)])
        cleans = []
        for i in clean:
            cleans.append({
                'room_no':i.room_no.name,
                'checkin':i.current_date,
                'checkout':i.end_date,
                'id':i.id,
                'status':i.state,
            })
        return cleans

    def search_repair(self,shop_id):
        shop_id = int(shop_id) if shop_id else False
        repair = self.env['rr.housekeeping'].search([('shop_id','=',shop_id)])
        repairs = []
        for i in repair:
            repairs.append({
                'room_no':i.room_no.name,
                'date':i.date,
                'id':i.id,
                'type':i.activity,
                'status':i.state,
            })
        return repairs

    def create_detail(self,room_type,room,checkin,checkout):
        date_obj = datetime.strptime(checkin, "%Y-%m-%d")
        check_in = date_obj.date()
        now_time = datetime.now()
        user = self.env['res.users'].browse([self.env.user.id])
        tz = pytz.timezone(user.tz) or pytz.utc
        user_tz_date = pytz.utc.localize(now_time).astimezone(tz)
        user_hour_min = user_tz_date.strftime("%H:%M:%S")
        print(user_hour_min)
      

        date2_date = datetime.strptime(checkout, "%Y-%m-%d")
        check_out = date2_date.date()
       
        if check_in == check_out:
            check_out = check_out + timedelta(days=1)
        room_types = int(room_type)
        room = int(room)
        categ_id = self.env['hotel.room_type'].search([('id','=',room_types)])
        cat_id = categ_id.cat_id.id
        rooms = self.env['hotel.room'].search([('id','=',room)])
        price = rooms.list_price
        room_id = rooms.product_id.id
        detail=[{
            'room' :room_id,
            'cat_id' : cat_id,
            'price':price,
            'checkout':check_out,
            'user_hour_min':user_hour_min,
            
        }]
        return detail

    def reserve_room(self,id):
        id = int(id)
        reservation = self.env['hotel.reservation'].browse(id)
        res=[]
        res.append(
            {
                'res_no':reservation.reservation_no,
                'checkin':reservation.reservation_line[0].checkin,
                'checkout':reservation.reservation_line[0].checkout,
                'partner':reservation.partner_id.name,
                'state':reservation.state,
            }
        )
        return res

    def folio_detail(self,id):
        id = int(id)
        folio = self.env['hotel.folio'].browse(id)
        res=[]
        res.append(
            {
                'res_no':folio.reservation_id.reservation_no,
                'checkin':folio.room_lines[0].checkin_date,
                'checkout':folio.room_lines[0].checkout_date,
                'partner':folio.partner_id.name,
                'state':folio.state,
            }
        )
        return res

    def cleaning_detail(self,id):
        id = int(id)
        clean = self.env['hotel.housekeeping'].browse(id)
        res=[]
        res.append(
            {
                'name':'Unavilable/Under Cleaning',
                'start':clean.current_date,
                'end':clean.end_date,
                'inspector':clean.inspector.name,
                'state':clean.state,
            }
        )
        return res

    def repair_repace_detail(self,id):
        id = int(id)
        repair = self.env['rr.housekeeping'].browse(id)
        res=[]
        res.append(
            {
                'name':'Repair/Repacement',
                'date':repair.date,
                'activity':repair.activity,
                'request':repair.requested_by.name,
                'approved':repair.approved_by,
                'state':repair.state,
            }
        )
        return res

    
    def get_datas(self,shop):
        shop_ids = int(shop)
        if shop_ids:
            check_in = self.env['hotel.reservation'].search([('state', '=', 'confirm'), ('shop_id', '=', shop_ids)])
            check_out = self.env['hotel.folio'].search([('state', '=','check_out'), ('shop_id', '=', shop_ids)])
            roomid = []
            room_id = self.env['hotel.room'].search([('shop_id','=',shop_ids)])
            for i in room_id:
                roomid.append(i)
            for i in room_id:
                book_his = self.env['hotel.room.booking.history'].search(
                    [('history_id', '=', i.id),('state', '!=', 'done'),('history_id.shop_id', '=',shop_ids )])
                if book_his and i in roomid:
                    roomid.remove(i)
            for i in room_id:
                prod = i.product_id.id
                housekeep = self.env['hotel.housekeeping'].search([('room_no','=',prod),('state', '!=', 'done'),('room_no.shop_id','=',shop_ids)])
                if housekeep and i in roomid:
                    roomid.remove(i)
            for i in room_id:
                repair = self.env['rr.housekeeping'].search([('room_no','=',i.id),('state', '!=', 'done'),('shop_id', '=', shop_ids)])
                if repair and i in roomid:
                    roomid.remove(i)
            booked = self.env['hotel.reservation'].search([('state', '!=', 'cancel'),('shop_id', '=', shop_ids)])
            
            return {
                'check_in': len(check_in),
                'check_out': len(check_out),
                'total': len(roomid),
                'booked': len(booked),
            }
        else:
            return {
                'check_in': '',
                'check_out': '',
                'total': '',
                'booked': '',
            }

    def get_view_reserve(self):
        view_id = self.env.ref('hotel_management.view_hotel_reservation_form1').id
        return view_id




class RoomType(models.Model):
    _inherit = 'hotel.room_type'




    def list_room_type(self,shop_id):
        shop_id = int(shop_id) if shop_id else False
        types = self.search([])
        data=[]
        for i in types:
            check = self.list_room(i.id,shop_id)
            if check:
                data.append({
                    'name':i.name,
                    'id':i.id,
                    'sequence':i.sequence
                })
        sorted_data = sorted(data, key=lambda x: x['sequence'])
            
        return sorted_data

    def list_room(self,res,shop_id):
        shop_id = int(shop_id) if shop_id else False
        room_types =int(res)
        categ_id = self.env['hotel.room_type'].search([('id','=',room_types)])
        cat_id = categ_id.cat_id.id
        room = self.env['hotel.room'].search([('categ_id','=',cat_id),('shop_id','=',shop_id)])
        datas=[]
        for i in room:
            datas.append({
                'name':i.name,
                'id':i.id
            })
        return datas

    def list_shop(self):
        shop = self.env['sale.shop'].search([])
        res = []
        for i in shop:
            res.append({
                'name': i.name,
                'id':i.id
            })
        return res
        

class CheckoutConfiguration(models.Model):
    _inherit = 'checkout.configuration'

    def hotel_checkout_policy(self,shop_id):

        checkout_id = self.search([('shop_id','=',shop_id),('name','=','custom')])
        if checkout_id:
            return int(checkout_id.time)
        return False
