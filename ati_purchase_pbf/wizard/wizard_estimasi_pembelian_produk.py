from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta, date

class WizardEstimasiPembelianProduk(models.TransientModel):
    _name = 'wizard.estimasi.pembelian.produk'
    _description = 'Report Estimasi Pembelian Produk'

    lead_time = fields.Selection([
        ("1","1"), ("2","2"), ("3","3"), ("4","4"),
        ("5","5"), ("6","6"), ("7","7"), ("8","8"),
        ("9","9"), ("10","10"),
    ], string='Lead Time', default="1")
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    purchase_category_id = fields.Many2one('ati.purchase.category', string="Purchase Category")

    def button_generate_excel(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'wizard.estimasi.pembelian.produk'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        return self.env.ref('ati_purchase_pbf.wizard_estimasi_pembelian_produk_xlsx').report_action(self, data=datas)
