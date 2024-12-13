# -*- coding: utf-8 -*-
{
    'name': 'ATI PBF Inventory Report',
    'version': '1.0.0.7',
    'author': 'Bagoes - Akselerasi Teknologi Investama',
    'category': 'Inventory',
    'maintainer': 'Bagoes - Akselerasi Teknologi Investama',
    'summary': """Stock Report""",
    'description': """
        Stock Report
    """,
    'website': 'https://akselerasiteknologi.id/',
    'license': 'LGPL-3',
    'support': '',
    'depends': [
        'base',
        'stock',
        'product',
        'account',
        'ati_pbf_product',
        'report_xlsx',
        'sh_message',
        'mail',
        'stock_picking_batch',
        'product_expiry',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/ati_pbf_inventory_report_view.xml',
        'views/ati_pbf_inventory_report_action.xml',
        'views/ati_pbf_inventory_report_menuitem.xml',
        'views/ati_pbf_adjustment_report.xml',
        'reports/report_pdf.xml',
        'reports/adjustment_report_template.xml'
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}