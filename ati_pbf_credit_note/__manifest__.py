{
    "name": "ATI PBF - CREDIT NOTE",
    "version": "15.0.1.4",
    "author": "Alwy",
    "category": "Invoice",
    "summary": "Customization Invoice, Sales",
    "description": """ 
        - Validation Approval Credit Note
        - Include Credit Note in Form Return
        - Hide Replace Invoice in Credit Note
        - SO Reference in Invoice
    """,
    "depends": [
        'account',
        'l10n_id_efaktur',
        'ati_pbf_account',
        'ati_pbf_return',
        'hr_expense',
    ],
    "data": [
        'security/res_groups.xml',
        'views/account_move.xml',
        'views/stock_picking.xml',
        'views/hr_expense_sheet.xml',
    ],
    "qweb": [],
    "image": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}
