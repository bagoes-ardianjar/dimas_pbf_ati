{
    "name": "ATI PBF ACCOUNT REPORT",
    "version": "1.0",
    "author": "Alwy",
    "category": "Accounting",
    "summary": "",
    "description": """ 
        
    """,
    "depends": [
        'web',
        'account',
        'account_reports',
        'l10n_id_efaktur'
    ],
    "data": [
        'data/report_paperformat_data.xml',
        'views/account_report.xml',
        'report/report_invoice.xml',
        'report/report_template.xml'
    ],
    "qweb": [],
    "image": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}
