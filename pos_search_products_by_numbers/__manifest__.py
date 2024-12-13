# -*- coding: utf-8 -*-
{
    'name': "pos search|pos search by numbers|pos search numbers|products search|pos products search|",

    'summary': """
        POS Search for products by numbers only
        """,

    'description': """
        Allow the user to search for products in Point of Sale by numbers only
    """,
    'images': ["static/description/main_banner.png"],
    'author': "Sayed Hassan",
    'version': '15.0',
    'license': "AGPL-3",
    'category': 'Point of Sale',
    'depends': ['point_of_sale'],
    'assets': {
        'point_of_sale.assets': [
            'pos_search_products_by_numbers/static/src/js/Screens/ProductScreen/ProductsWidgetControlPanel.js',
        ],
        'web.assets_qweb': [
            'pos_search_products_by_numbers/static/src/xml/ProductsSearch.xml',
        ],
    },

}
