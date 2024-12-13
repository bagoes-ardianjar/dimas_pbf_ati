# -*- coding: utf-8 -*-

{
    'name': 'PoS Payment Reference',
    'author': 'Odoo Bin',
    'company': 'Odoo Bin',
    'maintainer': 'Odoo Bin',
    'description': """ Payment Reference in Point of Sale | PoS Payment Reference | Payment Reference in PoS,
                        Point of Sale | PoS | PoS Payment""",
    'summary': """This module allow you to add payment reference in PoS Payment Line""",
    'version': '15.0',
    'license': 'OPL-1',
    'depends': ['point_of_sale'],
    'category': 'Point of Sale',
    'demo': [],
    'data': [
        'views/pos_payment_method_view.xml',
        'views/payment_ref_views.xml',
    ],
    'assets': {
            'point_of_sale.assets': [
                'ob_pos_payment_ref/static/src/js/models.js',
                'ob_pos_payment_ref/static/src/js/PaymentRefPopup.js',
                'ob_pos_payment_ref/static/src/js/payment_screen.js',
            ],
            'web.assets_qweb': [
                        'ob_pos_payment_ref/static/src/xml/**/*',
                    ],
    },
    'live_test_url': 'https://youtu.be/ZMbN9Prq6ZQ',
    'images': ['static/description/banner.png'],
    "price": 5,
    "currency": 'USD',
    'installable': True,
    'application': True,
    'auto_install': False,
}
