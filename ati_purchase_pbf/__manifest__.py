# -*- coding: utf-8 -*-
{
    'name': "ATI Purchase",
    'version': "1.3",
    'author': "ATI",
    'category': "Purchase",
    'summary': "Custom Purchase Management Tools",
    'description': """
    Enhance Purchase Management Tools
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/inherit_purchase_order.xml',
        'wizard/wizard_report_purchase_daily.xml',
        'wizard/wizard_vendor_purchase_view.xml',
        'wizard/estimasi_pembelian_produk_view.xml',
        'reports/report_pesanan_prekusor.xml',
        'reports/report_pesanan_oot.xml',
        'reports/report_pesanan_standar.xml',
        'reports/report_pesanan_alkes.xml',
        'reports/purchase_daily_report.xml',
        'reports/vendor_purchase_report.xml',
    ],
    'depends': [
        'base',
        'purchase',
        'ati_pbf_product',
        'ati_contact_pbf',
        'report_xlsx'
    ],
    'application': True,
}