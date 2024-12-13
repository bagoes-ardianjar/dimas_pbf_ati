# -*- coding: utf-8 -*-
{
    'name': "ati_pos_print",
    'summary': """Custom Receipt Point of Sale""",
    'description': """This module for custom receipt point of sale""",
    'author': "Doni Hadiansyah - Akselerasi Teknologi Investama",
    'website': "https://akselerasiteknologi.id",
    'category': 'Point of Sale',
    'version': '0.1',
    'depends': ['base','point_of_sale','tis_pos_dynamic_combo'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/pos_config_views.xml',
        'views/reset_loyalty_cron.xml'
    ],
    'assets': {
        'point_of_sale.assets': [
            'ati_pos_print/static/src/js/models.js',
            'ati_pos_print/static/src/js/CustomPosReceipt.js',
            'ati_pos_print/static/src/js/Screens/PickerScreen.js',
            'ati_pos_print/static/src/js/Screens/PickerReceiptScreen/PickerReceipt.js'
        ],
        'web.assets_qweb': [
            'ati_pos_print/static/src/xml/**/*'
        ],
    },
}
