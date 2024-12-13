# -*- coding: utf-8 -*-
{
    'name': 'Inherit PO (ATI)',
    'version': '1.0.0.0',
    'author': 'Adelia - Akselerasi Teknologi Investama',
    'category': 'Inventory',
    'maintainer': 'Adelia - Akselerasi Teknologi Investama',
    'summary': """Modul inherit PO""",
    'description': """
        Modul inherit PO
    """,
    'website': 'https://akselerasiteknologi.id/',
    'license': 'LGPL-3',
    'support': '',
    'depends': [
        'base',
        'stock',
        'purchase'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/price_history_line.xml',
        'views/report_xml_histori_perubahan_harga.xml',
        # 'views/inherit_stk_pckg.xml',
        # 'data/tmplt_mail_low_stok.xml',
        # 'data/cron.xml'
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}