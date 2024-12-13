# -*- coding: utf-8 -*-
# Part of YoungWings Technologies.See the License file for full copyright and licensing details.

{
    # Product Information 
    'name': 'Cancel Purchase Order',
    'category': 'Purchase',
    'version': '15.0.0.1',
    'license': 'OPL-1',
    'sequence':1,
    'summary': 'The Cancel Purchase Order module helps you to cancel your done purchase order/incoming shipment/vendor bill.',
    
    
    # Author
    'author': 'YoungWings Technologies',
    'maintainer': 'YoungWings Technologies',
    'website':'https://www.youngwingstechnologies.in/',
    'support':'youngwingstechnologies@gmail.com',
    
    # Dependencies
    'depends': ['purchase', 'ywt_cancel_stock_picking'],
    
    # Views
    'data': [],
    
    # Banner
    'images': ['static/description/banner.png'],

    # Technical
    'installable': True,
    'auto_install': False,
    'application': True,
    'price': 0.00 ,
    'currency': 'USD',
}
