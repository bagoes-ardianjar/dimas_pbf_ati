# -*- coding: utf-8 -*-
{
    'name': 'Product (ATI)',
    'version': '1.0.4.6',
    'author': 'Ibad - Akselerasi Teknologi Investama',
    'category': 'Stock',
    'maintainer': 'Ibad - Akselerasi Teknologi Investama',
    'summary': """Product Management Module""",
    'description': """
        Product Management Module
    """,
    'website': 'https://akselerasiteknologi.id/',
    'license': 'LGPL-3',
    'support': 'Ahmad.Ibad@akselerasiteknologi.id',
    'depends': [
        'base',
        'stock',
        'sale',
        # 'ati_pbf_sale',
        'product',
        'purchase',
        'ati_pbf_purchase',
        'account'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/product_template_security.xml',
        'data/sequence_product_sku.xml',
        'data/product_cron.xml',
        'views/product_template_views.xml',
        'views/product_product_views.xml',
        'views/purchase_order_views.xml',
        # 'views/sale_order_views.xml',
        'views/margin_view.xml',
        'views/product_pricelist_views.xml',
        'views/jenis_obat_views.xml',
        'views/pabrik_product_views.xml',
        'views/bentuk_sediaan_views.xml',
        # added 12/11/2022
        'views/company_sale_price_view.xml',
        'wizard/manage_company_sales_price_view.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}