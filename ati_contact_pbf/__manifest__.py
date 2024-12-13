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
        'data/cron.xml',
        'data/template_email.xml',
        'views/inherit_contact.xml',
        'views/res_company_view.xml',
        'views/supplier_type.xml',
        'views/type_product_supplied.xml',
        'views/customer_type.xml',
        'views/m_margin.xml'

    ],
    'depends': [
        'base',
        'hr',
        'l10n_id_efaktur',
        'l10n_id',
        'sale',
        'product',
        'purchase',
        'account'
    ],
    'application': True,
}