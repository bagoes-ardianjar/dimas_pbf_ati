
from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import datetime
from datetime import timedelta

class x_product_minimum(models.TransientModel):
    _name ='x.minimum.product.wizard'

    x_name = fields.Char(string='Nama Produk')
    x_pabric_reference = fields.Char(string='Pabrik Alias')
    x_onhand = fields.Float(string='On Hand Quantity')
    x_min_stok = fields.Float(string='Min Stok')
    x_wh = fields.Char(string='Lokasi')
    x_minim_ids = fields.Many2many('product.template', string='Produk')

    def _send_email_notif(self):
        
        product_min = self.env['product.template'].sudo().search([('detailed_type', '=', 'product')])
        template_id = self.env.ref('ati_pbf_inventory_adjusment.x_mail_minimum_qty').id
        template = self.env['mail.template'].sudo().browse(template_id)

        body_html = """<p><b>Dear Purchasing Team,</b></p>"""
        body_html+= """<br/><p>Silahkan periksa list produk yang akan habis berikut:</p><br/>"""
        body_html += """ <table style="width:1120px !important;" class="font8px">
                    <tr>
                    <th
                        style="border:1px solid #dddddd; text-align: center; padding: 5px; font-size: 14px; width:80px !important;">
                        <b>Nama Produk</b></th>
                    <th
                        style="border:1px solid #dddddd; text-align: center; padding: 5px; font-size: 14px; width:80px !important;">
                        <b>Pabrik Alias</b></th>
                    <th
                        style="border:1px solid #dddddd; text-align: center; padding: 5px; font-size: 14px; width:130px !important;">
                        <b>Onhand Quantity</th>
                    <th
                        style="border:1px solid #dddddd; text-align: center; padding: 5px; font-size: 14px; width:80px !important;">
                        <b>Minimum Stok</b></th>
                    <th
                        style="border:1px solid #dddddd; text-align: center; padding: 5px; font-size: 14px; width:120px !important;">
                        <b>Lokasi</b></th>
                </tr> """

        for q in product_min:
            domain =['&',
                        ('product_id','=', q.id),
                        ('quantity', '>=', 0),
                ]
            onhnd_obj = self.env['stock.quant'].sudo().search(domain).filtered(lambda r: r.quantity < q.x_minimum_quant)
            # print(product_min, 'product.templt')
            if not onhnd_obj:
                continue

            is_send = False
            send_lowqtyprodct_ids = []
            no = 0

            for ti in onhnd_obj:
                send_lowqtyprodct_ids.append(ti.product_id.product_tmpl_id.id)
                is_send = True
                no += 1

                # print(ti, 'stok.quant')

                if ti.product_id.product_tmpl_id.name:
                    nama_produk = str(ti.product_id.product_tmpl_id.name)
                    # print(ti.product_id.product_tmpl_id.name)
                else:
                    nama_produk = "-"

                if ti.product_id.product_tmpl_id.pabrik_reference:
                    pabrik_alias = str(ti.product_id.product_tmpl_id.pabrik_reference)
                else:
                    pabrik_alias = "-" 

                if ti.quantity:
                    onhand_qty = str(ti.quantity)
                else:
                    onhand_qty = "-"

                if ti.product_id.product_tmpl_id.x_minimum_quant:
                    minim_qty = str(ti.product_id.product_tmpl_id.x_minimum_quant)
                else:
                    minim_qty = "-"

                if ti.location_id.complete_name:
                    lokasi = str(ti.location_id.complete_name)
                else:
                    lokasi = "-"

                body_html += """<tr style="text-align: left;">
                    <td style="border:1px solid #dddddd; text-align: left; padding: 5px; font-size: 14px;  width:80px !important;">"""+ nama_produk +"""</td>
                    <td style="border:1px solid #dddddd; text-align: left; padding: 5px; font-size: 14px;  width:80px !important;">"""+ pabrik_alias+"""</td>"""
        
                body_html += """<td style="border:1px solid #dddddd; text-align: left; padding: 5px; font-size: 14px;  width:130px !important;">"""+ onhand_qty +"""</td>"""
                body_html += """<td style="border:1px solid #dddddd; text-align: left; padding: 5px; font-size: 14px;  width:80px !important;">"""+ minim_qty +"""</td>"""
                body_html += """<td style="border:1px solid #dddddd; text-align: left; padding: 5px; font-size: 14px;  width:120px !important;">"""+ lokasi +"""</td>"""
                body_html += """</tr>"""
        email_values = {'body_html':body_html}

        # expiredticketreminder = self.create({'x_name': o.product_id.product_tmpl_id.name,
        #                                 'x_pabric_reference':o.product_id.product_tmpl_id.pabrik_reference,
        #                                 'x_onhand' : o.quantity,
        #                                 'x_wh':o.location_id.complete_name,
        #                                 'x_min_stok': o.product_id.product_tmpl_id.x_minimum_quant,                                           
        #                                 'x_minim_ids': list(set(send_lowqtyprodct_ids))})

        template.send_mail(self.id, force_send=True, email_values=email_values)

        # print(body_html)
#                     print('jalan')
                # return True