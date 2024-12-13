# -*- coding: utf-8 -*-
{
    'name': 'ATI PBF Purchase (ATI)',
    'version': '1.0.1.2',
    'author': 'Ibad - Akselerasi Teknologi Investama',
    'category': 'Purchase',
    'maintainer': 'Ibad - Akselerasi Teknologi Investama',
    'summary': """Product Purchase Module""",
    'description': """
        Product Purchase Module
    """,
    'website': 'https://akselerasiteknologi.id/',
    'license': 'LGPL-3',
    'support': 'Ahmad.Ibad@akselerasiteknologi.id',
    'depends': [
        'base',
        'web',
        'product',
        'purchase',
        'ati_contact_pbf',
        'purchase_stock'
    ],
    'data': [
        'views/purchase_views.xml',
        'report/purchase_order_templates.xml'
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}