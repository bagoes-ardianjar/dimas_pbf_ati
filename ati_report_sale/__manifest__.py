# -*- coding: utf-8 -*-
{
    'name': 'Inherit For Report BPOM Sale (ATI)',
    'version': '1.0.0.0',
    'author': 'Adelia - Akselerasi Teknologi Investama',
    'category': 'Sale',
    'maintainer': 'Adelia - Akselerasi Teknologi Investama',
    'summary': """Modul inherit for report on sale""",
    'description': """
        Modul inherit for report on sale
    """,
    'website': 'https://akselerasiteknologi.id/',
    'license': 'LGPL-3',
    'support': '',
    'depends': [
        'base',
        'sale',
        'purchase',
        'ati_pbf_purchase_order_line'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/report_xml_bpom.xml',
        'views/report_xml_return.xml',
        'views/report_pdf_so.xml',
        'views/report_pdf_po.xml',
        'reports/paper_format_report.xml',
        'reports/report_pdf.xml',
        'reports/koli_transfer_report.xml',
        'reports/so_peritem_report.xml',
        'reports/po_peritem_report.xml',
        'reports/so_peritem_o_report.xml',
        'data/sequence.xml'
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}