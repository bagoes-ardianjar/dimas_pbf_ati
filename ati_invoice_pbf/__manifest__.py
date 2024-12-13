# -*- coding: utf-8 -*-
{
    'name': "ATI Account",
    'version': "1.0",
    'author': "ATI",
    'category': "Account",
    'summary': "Custom Account Management Tools",
    'description': """
    Enhance Account Management Tools
    """,
    'data': ['views/inherit_invoice.xml',
             'views/inherit_res_partner.xml'
    ],
    'depends': ['account','l10n_id_efaktur','base'],
    'application': True,
}