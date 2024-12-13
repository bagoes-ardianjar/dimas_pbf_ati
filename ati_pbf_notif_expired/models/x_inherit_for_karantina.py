from calendar import month
from email.policy import default
from odoo.exceptions import UserError
from odoo import models, fields, _, api
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from odoo.http import request, Response

class inherit_stok_location_for_karantina(models.Model):
    _inherit = 'stock.location'
    _description = ''

    is_karantina= fields.Boolean(default=False, string="Is Karantina")
    is_wh = fields.Boolean(default=False, string="Is Warehouse")

class inherit_picking_ad(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def get_full_url(self):
        self.ensure_one()
        base_url = request.env['ir.config_parameter'].get_param('web.base.url')
        base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        message_body = base_url
        
        return message_body

class x_inherit_for_karantina(models.Model):
    _inherit = 'stock.production.lot'
    _description = ''

    expiration_date = fields.Datetime(string='Expiration Date',
        help='This is the date on which the goods with this Serial Number may become dangerous and must not be consumed.')
    alert_date = fields.Datetime(string='Alert Date', compute='_compute_alert_date',
        help='Date to determine the expired lots and serial numbers using the filter "Expiration Alerts".', readonly=False)
    # url_picking = fields.Char(default='', string='url picking')


    @api.depends('expiration_date')
    def _compute_alert_date(self):
        self.alert_date=False
        self.use_date= False
        self.removal_date = False
        for rec in self:
            if rec.expiration_date:
                rec.alert_date = rec.expiration_date - relativedelta(months=3)
                rec.use_date = rec.expiration_date - relativedelta(months=3)
                rec.removal_date = rec.expiration_date - relativedelta(months=3)

    def action_expired_ad(self):
        now = datetime.now() + relativedelta(hours=7)
        stok_picking_obj= False
        
        vals={}
        line_vals_list=[]
        for b in self:
            tgl_expired=b.expiration_date
            if tgl_expired:
                sisa_bulan = (tgl_expired-now).days
                # print(sisa_bulan, b.id)

                if sisa_bulan == 90:
                    # print(b)

                    domain_type =['&', '&',   
                                ('name','=', 'Internal Transfers'),
                                ('code','=', 'internal'),
                                ('warehouse_id.name','=', 'BMP Taman Tekno')
                            ]
                    domain_awal =[
                                ('is_wh','=',True),
                            ]
                    domain_tujuan =[
                                ('is_karantina','=',True),
                            ]
                    
                    picking_type_obj = self.env['stock.picking.type'].sudo().search(domain_type)
                    lokasi_awal_obj= self.env['stock.location'].sudo().search(domain_awal)
                    # print(lokasi_awal_obj)
                    lokasi_tujuan_obj= self.env['stock.location'].sudo().search(domain_tujuan)
                    # print(lokasi_tujuan_obj)

                    mv_vals_list=[]                    

                    move_dict={
                                'product_id': b.product_id.id,
                                'lot_ids': [(6,0, b)],
                                'quantity_done': b.product_qty,
                                'product_uom': b.product_uom_id.id
                    }

                    move_line_dict={
                                    'product_id': b.product_id.id,
                                    'location_id': lokasi_awal_obj.id,
                                    'location_dest_id': lokasi_tujuan_obj.id,
                                    'lot_id': b.id,
                                    'qty_done': b.product_qty,
                                    'product_uom_id': b.product_uom_id.id,
                                    'expiration_date': b.expiration_date
                                }
                    mv_vals_list.append(move_dict)
                    line_vals_list.append(move_line_dict)
                    
                    vals = {
                                    'picking_type_id': picking_type_obj.id,
                                    'location_id': lokasi_awal_obj.id,
                                    'location_dest_id': lokasi_tujuan_obj.id,
                                    'move_line_ids_without_package': [(0, 0, line_vals) for line_vals in line_vals_list],
                                    'state':'waiting',
                                }

        if vals:                    
            stok_picking_obj = self.env['stock.picking'].create(vals)
            stok_picking_obj.action_confirm()
        if not vals:
            pass

        # print(stok_picking_obj)