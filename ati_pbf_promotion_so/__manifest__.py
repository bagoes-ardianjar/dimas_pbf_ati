# -*- coding: utf-8 -*-
{
    'name': "ati_pbf_promotion_so",

	'summary': """
		Custom Promotion in Sale Order """,

	'description': """
		Custom Promotion in Sale Order 
	""",

	'author': "ATI",

	# Categories can be used to filter modules in modules listing
	# Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
	# for the full list
	'category': 'Uncategorized',
	'version': '0.1',

	# any module necessary for this one to work correctly
	'depends': ['base', 'sale','sale_coupon', 'ati_pbf_sale'],

	# always loaded
	'data': [
		'views/akses_right_promotion_group.xml',
		'security/ir.model.access.csv',
		'views/views.xml',
		# 'views/templates.xml',
	],
	# only loaded in demonstration mode
	'demo': [
		# 'demo/demo.xml',
	],
}
