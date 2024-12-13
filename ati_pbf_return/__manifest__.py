{
    "name": "ATI PBF - RETURN",
    "version": "15.0.1.2",
    "author": "Alwy",
    "category": "Stock",
    "summary": "Customization Picking",
    "description": """ 
        - Validation Approval Form Return
        - Set Delivery Status
    """,
    "depends": [
        'stock',
        'ati_pbf_stock',
        'ywt_cancel_stock_picking'
    ],
    "data": [
        'views/stock_picking.xml',
    ],
    "qweb": [],
    "image": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}
