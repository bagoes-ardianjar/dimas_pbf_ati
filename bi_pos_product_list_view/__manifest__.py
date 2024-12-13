# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    "name": "Advance POS View - POS Product Switch View and Sort View",
    "version": "15.0.0.1",
    "category": "Point of Sale",
    'summary': 'POS product advance view POS product switch view POS product list view pos product sorting point of dale product switch view point of sale product list view point of sale product sorting pos product sort view point of sale product sort pos advance view',
    "description": """

             POS Product Switch View and Sort in odoo,
             POS Product in Grid View,
             POS Product in List View,
             POS Product Sort by Name,
             POS Product Sort by Code,
             POS Product Sort by UOM,
             POS Product Sort by Sale Price,
             POS Product Sort by Avalilable Qty,

    """,
    "author": "BrowseInfo",
    "website": "https://www.browseinfo.in",
    "price": 15,
    "currency": 'EUR',
    "depends": ['point_of_sale'],
    "data": [
        'views/pos_config_view.xml',
    ],

    'assets': {
        'point_of_sale.assets': [
            'bi_pos_product_list_view/static/src/css/pos.css',
            'bi_pos_product_list_view/static/src/js/pos_product_list_view.js',
            'bi_pos_product_list_view/static/src/js/product_list.js',
        ],
        'web.assets_qweb': [
            'bi_pos_product_list_view/static/src/xml/**/*',
        ],
    },
    
    "license": "OPL-1",
    "auto_install": False,
    "installable": True,
    "live_test_url": 'https://youtu.be/cSu905abBrA',
    "images": ["static/description/Banner.png"],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
