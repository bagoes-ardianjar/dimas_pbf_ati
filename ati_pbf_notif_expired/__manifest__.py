# -*- coding: utf-8 -*-
{
    'name': 'Inherit Inventory for Notication Expired (ATI)',
    'version': '1.0.0.0',
    'author': 'Adelia - Akselerasi Teknologi Investama',
    'category': 'Inventory',
    'maintainer': 'Adelia - Akselerasi Teknologi Investama',
    'summary': """Modul inherit for notification expired""",
    'description': """
        Modul inherit for notification expired
    """,
    'website': 'https://akselerasiteknologi.id/',
    'license': 'LGPL-3',
    'support': '',
    'depends': [
        'base',
        'stock'
    ],
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/inherit_for_karantina.xml',
        'views/inherit_location_for_karantina.xml',
        # 'views/inherit_stk_pckg.xml',
        'data/tmplt_mail_batch_expired.xml',
        'data/cron.xml'
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}