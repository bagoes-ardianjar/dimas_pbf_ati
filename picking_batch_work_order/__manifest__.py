# -*- coding: utf-8 -*-
{
    'name': "picking_batch_work_order",
    'summary': """Picking Batch Work Order""",
    'description': """This module is for picking batch work order""",
    'author': "ATI / Doni Hadiansyah",
    'website': "https://akselerasiteknologi.id",
    'category': 'Stock',
    'version': '0.1',
    'depends': ['base','stock','ati_pbf_stock'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/report_paper_format.xml',
        'views/stock_picking_wo_batch_views.xml',
        'wizard/stock_picking_to_batch_work_order_views.xml',
        'report/work_order_report.xml',
        'report/report_batch_delivery_order.xml'
    ],
}