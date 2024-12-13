# -*- coding: utf-8 -*-
{
    'name': 'Report Pembelian (ATI)',
    'version': '1.0.0.0',
    'author': 'Amalia - Akselerasi Teknologi Investama',
    'category': 'Purchases',
    'maintainer': 'Amalia - Akselerasi Teknologi Investama',
    'summary': """Modul inherit for report on purchase""",
    'description': """
        Modul inherit for report on purchase
    """,
    'website': 'https://akselerasiteknologi.id/',
    'license': 'LGPL-3',
    'support': '',
    'depends': [
        'base',
        'purchase',
        'l10n_id_efaktur',
        'ati_purchase_pbf',
        'ati_report_sale',
        'ati_pbf_product'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/report_pdf_pembelian_perbarang.xml',
        'views/report_pdf_pembelian_perfaktur.xml',
        'views/report_pembelian.xml',
        'views/report_outstanding.xml',
        'views/report_pdf_pembelian_ppn.xml',
        'views/report_pdf_pembelian_nonppn.xml',
        'reports/paper_format_report.xml',
        'reports/report_pdf.xml',
        'reports/pembelian_perbarang_report.xml',
        'reports/pembelian_perfaktur_report.xml',
        'reports/pembelian_ppn_report.xml',
        'reports/pembelian_nonppn_report.xml',
        # 'data/cron.xml'
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}