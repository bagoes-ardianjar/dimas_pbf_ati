# -*- coding: utf-8 -*-
{
    'name': 'ATI PBF Account (ATI)',
    'version': '1.0.0.9',
    'author': 'Ibad - Akselerasi Teknologi Investama',
    'category': 'Invoice',
    'maintainer': 'Ibad - Akselerasi Teknologi Investama',
    'summary': """Invoice Management Module""",
    'description': """
        Invoice Management Module
    """,
    'website': 'https://akselerasiteknologi.id/',
    'license': 'LGPL-3',
    'support': 'Ahmad.Ibad@akselerasiteknologi.id',
    'depends': [
        'base',
        'account',
        'ati_invoice_payments',
        'discount_account_invoice'
    ],
    'data': [
        'reports/vendor_bill_ttb_report.xml',
        'reports/report_action_invoice.xml',
        'reports/report_invoice.xml',
        'views/account_move_view.xml',
        'views/account_payment_view.xml',
        'views/ati_invoice_date_cron.xml',
        'security/account_move_security.xml',
        'data/ir_cron.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}