# -*- coding: utf-8 -*-
# Part of YoungWings Technologies.See the License file for full copyright and licensing details.

{
    # Product Information 
    'name': 'Cancel Stock Picking',
    'category': 'Sales',
    'version': '15.0.0.1',
    'license': 'OPL-1',
    'sequence': 1,
    'summary': 'The Cancel Stock Picking Module it helps you to Cancel Your Delivery Order (Incoming/Outgoing/Internal) Shipment.',
    'description': 'The Cancel Stock Picking Module it helps you to Cancel Your Delivery Order (Incoming/Outgoing/Internal) Shipment.',

    # Author
    'author': 'YoungWings Technologies',
    'maintainer': 'YoungWings Technologies',
    'website': 'https://www.youngwingstechnologies.in/',
    'support': 'youngwingstechnologies@gmail.com',

    # Dependencies
    'depends': ['sale_stock', 'stock', 'account'],

    # views
    "data": ['views/stock_picking_views.xml'],

    # Banner
    'images': ['static/description/banner.png'],

    # Technical
    'installable': True,
    'auto_install': False,
    'application': True,
    'price': 8.00,
    'currency': 'USD',

    # Tags
    'description': """The Cancel Stock Picking Module helps you to cancel your done delivery order (Incoming/Outgoing/Internal).
                    Sale Cancel, Picking Cancel, Order Cancel, Order Cancel, Cancel Delivery Order, Cancel Shipment Order,Cancel Bill
                    Stock Picking Cancel/Reverse/Revert Odoo
                    Stock Picking Cancel and Reset
                    Cancel Stock Picking (Delivery Order) & Reset to Draft
                    Cancel Inventory | Delete Stock Picking | Delete Inventory Adjustment | Delete Scrap Order | Delete Stock Moves
                    Reset Stock Move/Picking (Cancel/Reverse/Delete) in odoo
                    """

}
