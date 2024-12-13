import time
from odoo import models, fields, api,_
from num2words import num2words
from odoo.exceptions import UserError, ValidationError
import xml.etree.ElementTree as etree
from datetime import datetime,date
import base64
import requests
from datetime import datetime, timedelta,date
from dateutil import relativedelta
from dateutil.relativedelta import relativedelta


class InheritPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    type_po = fields.Selection([ ('prekusor', 'Prekusor'), ('oot', 'OOT'), ('standar', 'Standar'), ('alkes', 'Alkes')],
                             string='Type PO')

    number_form = fields.Char('No Form')
    purchase_person = fields.Many2one('hr.employee', string='Purchase Person (*)', index=True, tracking=1)
    new_purchase_person = fields.Many2one('hr.employee', string='Purchase Person (*)', index=True, tracking=1)

    def button_print_report_pesanan_prekursor(self):
        return self.env.ref('ati_purchase_pbf.action_report_pesanan_prekursor_custom').report_action(self)

    def button_print_report_pesanan_oot(self):
        return self.env.ref('ati_purchase_pbf.action_report_pesanan_oot_custom').report_action(self)

    def button_print_report_pesanan_standar(self):
        return self.env.ref('ati_purchase_pbf.action_report_pesanan_standar_custom').report_action(self)

    def button_print_report_pesanan_alkes(self):
        return self.env.ref('ati_purchase_pbf.action_report_pesanan_alkes_custom').report_action(self)


    def init(self):
        company_ids = self.env['res.company'].search([])
        for comp in company_ids:
            seq_ids = self.env['ir.sequence'].search([('code', '=', 'purchase.order'), ('company_id', 'in', [comp.id, False])], order='company_id')

            if not seq_ids:
                self.env['ir.sequence'].create({
                    'name': 'Purchase Order',
                    'code': 'purchase.order',
                    'prefix': 'PO/%(month)s%(y)s',
                    'padding': 5,
                    'company_id': comp.id
                })

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _num_word_qty(self):
        for rec in self:
            rec.word_num_quantity = ''
            if rec.product_qty:
                word_num_quantity = str(num2words(int(rec.product_qty), lang='id'))
                rec.word_num_quantity = word_num_quantity.capitalize()

    word_num_quantity = fields.Char(string="Quantity In Words:", compute='_num_word_qty', readonly=False)