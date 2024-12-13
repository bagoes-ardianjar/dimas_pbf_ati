# -*- coding: utf-8 -*-
{
    'name': "ATI Invoice Payments",
    'summary': """
        - Invoice
        - Payments
        """,
    'description': """
        Rename Fields & Add Prosses Payments
    """,
    'author': "asop-source",
    'website': "http://www.yourcompany.com",
    'category': 'account',
    'version': '0.2',
    'depends': ['base','account','l10n_id_efaktur', 'ati_pbf_return'],
    'data': [
        'security/ir.model.access.csv',
        'views/invoice.xml',
        'views/payments.xml',
        'wizard/payments.xml',
        'wizard/wizard_vendor_payment_view.xml',
        'reports/payment_ttb_report.xml',
    ],

}
