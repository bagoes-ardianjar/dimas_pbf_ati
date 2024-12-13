# -*- coding: utf-8 -*-
{
    'name': "ATI Inventory Stock",
    'summary': """
        - Inventory
        - Stock
        """,
    'description': """
        Rename Fields & Add Prosses Inventory
    """,
    'author': "asop-source",
    'website': "http://www.yourcompany.com",
    'category': 'stock',
    'version': '0.1',
    'depends': ['base','stock'],
    'data': [
        'views/group.xml',
        # 'security/ir.model.access.csv',
        'views/stock.xml',
        'views/putaway.xml',
    ],

}
