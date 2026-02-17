# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": """FJ - E-invoicing""",
    "version": "1.03.00",
    'countries': ['in'],
    "category": "Accounting/Localizations/EDI",
    "depends": [
        "account_edi",
        "point_of_sale",
        "hr"
    ],
    "description": """
Indian - E-invoicing
====================
To submit invoicing through API to the government.
We use "Tera Software Limited" as GSP

Step 1: First you need to create an API username and password in the E-invoice portal.
Step 2: Switch to company related to that GST number
Step 3: Set that username and password in Odoo (Goto: Invoicing/Accounting -> Configuration -> Settings -> Customer Invoices or find "E-invoice" in search bar)
Step 4: Repeat steps 1,2,3 for all GSTIN you have in odoo. If you have a multi-company with the same GST number then perform step 1 for the first company only.

For the creation of API username and password please ref this document: <https://service.odoo.co.in/einvoice_create_api_user>
    """,
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/account_edi_data.xml",
        "data/sequnce.xml",
        "data/data.xml",
        # "views/res_config_settings_views.xml",
        "views/edi_pdf_report.xml",
        "views/account_move_views.xml",
        "views/vms_payment_type.xml",
        "views/hr_employee.xml",
        "views/account_tax.xml",
        "views/pos_order.xml",
        "views/pos_config_view.xml",
        "views/pos_payment_method.xml",
        "views/res_partner.xml"
    ],
    # "demo": [
    #     "demo/demo_company.xml",
    # ],
    'assets': {
        'point_of_sale._assets_pos': [
            'l10n_fj_edi_asc/static/src/js/ticket_screen.js',
            'l10n_fj_edi_asc/static/src/overrides/models/pos_order.js',
            'l10n_fj_edi_asc/static/src/xml/ticket_screen.xml',
            'l10n_fj_edi_asc/static/src/pos_reciept.xml'
        ],
    },


    "installable": True,
    "license": "LGPL-3",
}
