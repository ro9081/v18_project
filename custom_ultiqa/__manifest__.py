# -*- encoding: utf-8 -*-

{
    "name": "Ultiqa",
    "version": "1.8",
    "author": "ascensivetechnologies",
    'website': 'https://ascensivetechnologies.com/',
    "category": "Customization Ultiqa",
    "description": """
    Enhance Property of Contact module.
    """,
    "depends": ['base', 'point_of_sale', 'banquet_managment', 'sale', 'contacts', 'hotel','hotel_laundry'],
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_view.xml",
        "views/hotel_reservation.xml",
        "views/account_move.xml",
        "views/hotel_folio_line.xml",
        "views/product.xml",
        "reports/report_invoice.xml",
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'custom_ultiqa/static/src/xml/hotel_pos.xml',
        ],
        'pos_preparation_display.assets': [
            'custom_ultiqa/static/src/xml/order.xml',
        ],
    },

    "active": False,
    "installable": True,
    'license': 'OPL-1',
}
