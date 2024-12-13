# -*- coding: utf-8 -*-
{
    'name': 'Inventory Report (ATI)',
    'version': '1.0.1.0',
    'author': 'Ibad - Akselerasi Teknologi Investama',
    'category': 'Inventory',
    'maintainer': 'Ibad - Akselerasi Teknologi Investama',
    'summary': """Stock Report""",
    'description': """
        Stock Report
    """,
    'website': 'https://akselerasiteknologi.id/',
    'license': 'LGPL-3',
    'support': 'Ahmad.Ibad@akselerasiteknologi.id',
    'depends': [
        'base',
        'stock',
        'product',
        'account',
        'ati_pbf_product',
        'report_xlsx',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/report_kartu_stock_view.xml',
        'reports/inventory_report_ati.xml',
        'reports/report_kartu_stock_template.xml'
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}