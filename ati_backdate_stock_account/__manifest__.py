# -*- coding: utf-8 -*-
{
    'name': "ati_backdate_stock_account",
    'summary': """Backdate Inventory Accounting""",
    'description': """This module is for backdate inventory and accounting""",
    'author': "ATI / Doni Hadiansyah",
    'website': "https://akselerasiteknologi.id",
    'category': 'Inventory',
    'version': '0.2',
    'depends': ['base','stock'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/stock_picking_views.xml'
    ]
}
