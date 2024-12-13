# -*- coding: utf-8 -*-
{
	'name': "ATI Expense",
	'version': "1.3",
	'author': "ATI - Ahmad Mustafidul Ibad",
	'category': "Expense",
	'summary': "Custom Expense Module",
	'description': """
    	Custom Expense Module
    """,
	'data': [
		'views/hr_expense_view.xml',
		'views/hr_expense_sheet_view.xml',
		'report/hr_expense_report_inherit.xml',
	],
	'depends': [
		'hr_expense',
		'sale_expense'
	],
	'application': True,
}