import time
from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError
import xml.etree.ElementTree as etree
from datetime import datetime,date
import base64
import requests
from datetime import datetime, timedelta,date
from dateutil import relativedelta
from dateutil.relativedelta import relativedelta


class MasterMargin(models.Model):
    _name = 'm.margin'

    def write(self, vals):
        res = super(MasterMargin, self).write(vals)
        if 'value' in vals:
            for this in self:
                check_partner = self.env['res.partner'].sudo().search([]).filtered(lambda x: this.id in x.margin_ids.ids)
                so_line = self.env['sale.order.line'].sudo().search([('order_id.partner_id', 'in', check_partner.ids)])
                for l in so_line:
                    if l.order_id.state == 'draft':
                        if l.is_lock_price != True:
                            if not l.order_id.partner_id.margin_ids or l.order_id.is_pasien == True:
                                if not l.product_id.margin:
                                    l.product_margin_percent = '0%'
                                else:
                                    l.product_margin_percent = str(l.product_id.margin.name) + '%'
                            else:
                                margin_from_customer = 0
                                for m_margin in l.order_id.partner_id.margin_ids:
                                    margin_from_customer += m_margin.value
                                    l.product_margin_percent = str(margin_from_customer) + '%'
                        else:
                            pass
                    else:
                        pass
                vals_historical = {
                    'name': this.name + ' | ' + self.env.user.name,
                    'm_margin_id': this.id,
                    'user_id': self.env.user.id,
                    'change_date': datetime.now(),
                    'value': vals['value'],
                    'note': 'Margin diisi' if vals['value'] != False else 'Margin tidak diisi'
                }
                new_historical = self.env['ati.historical.m.margin'].sudo().create(vals_historical)
        return res

    name = fields.Char('Name')
    value = fields.Float(string='Value (%)')
    historical_m_margin_ids = fields.One2many('ati.historical.m.margin', 'm_margin_id', string="Historical Margin")


class ati_historical_m_margin(models.Model):
    _name = 'ati.historical.m.margin'

    name = fields.Char(string="Name")
    m_margin_id = fields.Many2one('m.margin', string="Margin Id")
    user_id = fields.Many2one('res.users', string="User Id")
    change_date = fields.Datetime(string="Change Date")
    value = fields.Float(string="Value", default=0.0)
    note = fields.Char(string="Note")
    