# -*- coding: utf-8 -*-
{
    'name': 'Contact (ATI)',
    'version': '1.0.0.7',
    'author': 'Ibad - Akselerasi Teknologi Investama',
    'category': 'CRM',
    'maintainer': 'Ibad - Akselerasi Teknologi Investama',
    'summary': """Centralize your address book""",
    'description': """
        Centralize your address book
    """,
    'website': 'https://akselerasiteknologi.id/',
    'license': 'LGPL-3',
    'support': 'Ahmad.Ibad@akselerasiteknologi.id',
    'depends': [
        'base',
        # 'ati_pbf_sale',
        'l10n_id_efaktur'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml'
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}