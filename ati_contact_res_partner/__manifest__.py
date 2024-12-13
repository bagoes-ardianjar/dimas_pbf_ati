# -*- coding: utf-8 -*-
{
    'name': "ATI Contact",
    'version': "1.0",
    'author': "ATI",
    'category': "Contact",
    'summary': "Custom Contact Management Tools",
    'description': """
    Enhance Contact Management Tools
    """,
    'data': [
        'security/ir.model.access.csv',
        'views/inherit_res_partner.xml'

    ],
    'depends': [
        'base',
        'hr',
        'l10n_id_efaktur',
        'l10n_id',
        'sale',
        'product',
        'purchase',
        'account',
        'ati_contact_pbf'
    ],
    'application': True,
}