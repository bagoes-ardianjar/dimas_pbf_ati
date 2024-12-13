# -*- coding: utf-8 -*-
{
    'name': 'User (ATI)',
    'version': '1.0.0.0',
    'author': 'Ibad - Akselerasi Teknologi Investama',
    'category': 'User',
    'maintainer': 'Ibad - Akselerasi Teknologi Investama',
    'summary': """User""",
    'description': """
        User
    """,
    'website': 'https://akselerasiteknologi.id/',
    'license': 'LGPL-3',
    'support': 'Ahmad.Ibad@akselerasiteknologi.id',
    'depends': [
        'base',
        'sh_message',
        'ati_pbf_mail'
    ],
    'data': [
		'views/res_user_view.xml'
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}