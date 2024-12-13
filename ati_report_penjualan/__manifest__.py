# -*- coding: utf-8 -*-
{
    'name': 'Report Penjualan (ATI)',
    'version': '1.0.0.0',
    'author': 'Amalia - Akselerasi Teknologi Investama',
    'category': 'Sale',
    'maintainer': 'Amalia - Akselerasi Teknologi Investama',
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
        'ati_pbf_sale',
        'ati_report_sale',
        'ati_pbf_product',
        'hr'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/report_pdf_penjualan_perbarang.xml',
        'views/report_pdf_penjualan_perfaktur.xml',
        'views/report_penjualan.xml',
        'views/report_outstanding.xml',
        'views/report_alkes.xml',
        'reports/paper_format_report.xml',
        'reports/report_pdf.xml',
        'reports/penjualan_perbarang_report.xml',
        'reports/penjualan_perfaktur_report.xml',
        # 'data/cron.xml'
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}