from odoo import fields, models, api, _
from odoo.exceptions import UserError

from datetime import datetime as dt, timedelta

class ReportKartuStockBuffer(models.Model):
	_name = "report.kartu.stock.buffer"
	_description = "Report Kartu Stock Buffer"

	tanggal = fields.Datetime('Tanggal')
	ref_no = fields.Char('Nomor Ref')
	batch = fields.Char('Batch No')
	expiration_date = fields.Date('Exp Date of Batch')
	qty_awal = fields.Float('Qty Awal')
	qty_masuk = fields.Float('Qty Masuk')
	qty_keluar = fields.Float('Qty Keluar')
	qty_akhir = fields.Float('Qty Akhir')
	hpp = fields.Float('HPP Satuan')