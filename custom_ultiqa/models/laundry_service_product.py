from odoo import fields, models, api

class laundry_service_product(models.Model):
    _inherit = 'laundry.service.product'
    _description = 'Laundry Service Product'

    def get_sales_value(self):
        for record in self:
            sale_subtotal = 0.0
            for line in record.laundry_service_product_line_ids:
                sale_subtotal += line.sale_subtotal
            record.sales_rate = sale_subtotal

    def get_sales_subtotal_values(self):
        if self._context is None:
            self._context = {}

        for line in self:
            subtotal = 0.00
            cur = line.laundry_service_id.pricelist_id.currency_id

            for product_line in line.laundry_service_product_line_ids:
                taxes = line.tax_id.compute_all(
                    product_line.sale_subtotal,
                    currency=cur,
                    quantity=1,
                    product=line.laundry_services_id.laundry_services_id
                )
                subtotal += taxes['total_excluded']

            line.sale_subtotal = cur.round(subtotal)

