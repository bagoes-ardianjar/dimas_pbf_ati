# -*- coding: utf-8 -*-
{
    'name': 'Inherit Inventory (ATI)',
    'version': '1.0.0.1',
    'author': 'Adelia - Akselerasi Teknologi Investama',
    'category': 'Inventory',
    'maintainer': 'Adelia - Akselerasi Teknologi Investama',
    'summary': """Modul inherit for inventory adjusment""",
    'description': """
        Modul inherit for inventory adjusment
    """,
    'website': 'https://akselerasiteknologi.id/',
    'license': 'LGPL-3',
    'support': '',
    'depends': [
        'base',
        'stock',
        'ati_pbf_notif_expired'
    ],
    'data': [
        # 'security/ir.model.access.csv',
        'views/inherit_stock_quant.xml',
        'views/inherit_prdc_tmplt.xml',
        'views/inherit_stk_pckg.xml',
        'data/tmplt_mail_low_stok.xml',
        'data/cron.xml'
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}