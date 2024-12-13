
from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import datetime
from datetime import timedelta
from odoo.http import request, Response

class x_inherit_stok_production_lot_wiz(models.TransientModel):
    _name ='x.lot.expired.wizard'

    x_name = fields.Char(string='Nama Produk')
    x_qty = fields.Char(string='Quantity')
    x_expired = fields.Float(string='Tgl Kadaluarsa')
    x_asal = fields.Float(string='Lokasi Awal')
    x_tujuan = fields.Char(string='Lokasi Tujuan')
    x_lot_ids = fields.Many2many('stock.production.lot', string='Batch')


    def _send_email_notif_expired(self):
        
        now = datetime.now() + relativedelta(hours=7)
        batch_obj= self.env['stock.production.lot'].sudo().search([])
        batch_obj.action_expired_ad()

        template_id = self.env.ref('ati_pbf_notif_expired.x_mail_batch_expired').id
        template = self.env['mail.template'].sudo().browse(template_id)

        last_p_obj= self.env['stock.picking'].sudo().search([])[-1]
        url = last_p_obj.get_full_url()

        body_html = """<p><b>Dear Warehouse Team.</b></p></br>"""
        body_html+= """<p>List barang dibawah ini akan expired <b>3 bulan</b> lagi dan mohon pindahkan ke <b>Gudang Karantina</b>. Silahkan periksa dan konfirmasi Nomor Internal Transfer (WH/INT). </p><br/>"""

        body_html += """ <table style="width:1120px !important;" class="font8px">
                    <tr>
                    <th
                        style="border:1px solid #dddddd; text-align: center; padding: 5px; font-size: 14px; width:80px !important;">
                        <b>Nama Produk</b></th>
                    <th
                        style="border:1px solid #dddddd; text-align: center; padding: 5px; font-size: 14px; width:80px !important;">
                        <b>Batch</b></th>
                    <th
                        style="border:1px solid #dddddd; text-align: center; padding: 5px; font-size: 14px; width:130px !important;">
                        <b>Quantity</th>
                    <th
                        style="border:1px solid #dddddd; text-align: center; padding: 5px; font-size: 14px; width:80px !important;">
                        <b>Tanggal Kadaluarsa</b></th>
                    <th
                        style="border:1px solid #dddddd; text-align: center; padding: 5px; font-size: 14px; width:120px !important;">
                        <b>Lokasi Asal</b></th>
                    <th
                        style="border:1px solid #dddddd; text-align: center; padding: 5px; font-size: 14px; width:120px !important;">
                        <b>Lokasi Tujuan</b></th>
                </tr> """

        for b in batch_obj:
            tgl_expired=b.expiration_date
            if tgl_expired:
                sisa_hari = (tgl_expired-now).days

                is_send = False
                send_expiredbatch_ids = []
                no = 0

                if sisa_hari != 90:
                    continue

                if sisa_hari == 90:
                    # print(url, 'url')
                    
                    send_expiredbatch_ids.append(b.product_id.product_tmpl_id.id)
                    # print(b)
                    is_send = True
                    no += 1

                    if b.product_id.product_tmpl_id.name:
                        nama_produk = str(b.product_id.product_tmpl_id.name)
                        # print(b.product_id.product_tmpl_id.name)
                    else:
                        nama_produk = "-"

                    if b.name:
                        batch = str(b.name)
                    else:
                        batch = "-"

                    if b.product_qty:
                        quantity = str(b.product_qty)
                    else:
                        quantity = "-" 

                    if b.expiration_date:
                        exp_date = str(b.expiration_date)
                    else:
                        exp_date = "-"
                    
                    lokasi = 'WH/STOCK'
                    lokasi_tujuan = 'WH/Karantina'

                    body_html += """<tr style="text-align: left;">
                    <td style="border:1px solid #dddddd; text-align: left; padding: 5px; font-size: 14px;  width:80px !important;">"""+ nama_produk +"""</td>
                    <td style="border:1px solid #dddddd; text-align: left; padding: 5px; font-size: 14px;  width:80px !important;">"""+ batch+"""</td>"""
        
                    body_html += """<td style="border:1px solid #dddddd; text-align: left; padding: 5px; font-size: 14px;  width:130px !important;">"""+ quantity +"""</td>"""
                    body_html += """<td style="border:1px solid #dddddd; text-align: left; padding: 5px; font-size: 14px;  width:80px !important;">"""+ exp_date +"""</td>"""
                    body_html += """<td style="border:1px solid #dddddd; text-align: left; padding: 5px; font-size: 14px;  width:120px !important;">"""+ lokasi +"""</td>"""
                    body_html += """<td style="border:1px solid #dddddd; text-align: left; padding: 5px; font-size: 14px;  width:120px !important;">"""+ lokasi_tujuan +"""</td>"""
                    body_html += """</tr>"""

        body_html += """<p>Please check this link for more details:
                    <b><a href="""+url+""">Click Here</a></b></p><br/>"""
        

        # print(body_html)

        email_values = {'body_html':body_html}
        template.send_mail(self.id, force_send=True, email_values=email_values)
            

    def _send_email_notif_expired_1bulan(self):
        
        now = datetime.now() + relativedelta(hours=7)
        batch_obj= self.env['stock.production.lot'].sudo().search([])

        template_id = self.env.ref('ati_pbf_notif_expired.x_mail_batch_expired').id
        template = self.env['mail.template'].sudo().browse(template_id)

        body_html = """<p><b>Dear Warehouse Team.</b></p></br>"""
        body_html+= """<p>List barang dibawah ini akan expired <b>1 bulan</b> lagi dan mohon pindahkan ke <b>Gudang Karantina</b>. Silahkan periksa dan konfirmasi Nomor Internal Transfer (WH/INT). </p><br/>"""

        body_html += """ <table style="width:1120px !important;" class="font8px">
                    <tr>
                    <th
                        style="border:1px solid #dddddd; text-align: center; padding: 5px; font-size: 14px; width:80px !important;">
                        <b>Nama Produk</b></th>
                    <th
                        style="border:1px solid #dddddd; text-align: center; padding: 5px; font-size: 14px; width:80px !important;">
                        <b>Batch</b></th>
                    <th
                        style="border:1px solid #dddddd; text-align: center; padding: 5px; font-size: 14px; width:130px !important;">
                        <b>Quantity</th>
                    <th
                        style="border:1px solid #dddddd; text-align: center; padding: 5px; font-size: 14px; width:80px !important;">
                        <b>Tanggal Kadaluarsa</b></th>
                    <th
                        style="border:1px solid #dddddd; text-align: center; padding: 5px; font-size: 14px; width:120px !important;">
                        <b>Lokasi Asal</b></th>
                    <th
                        style="border:1px solid #dddddd; text-align: center; padding: 5px; font-size: 14px; width:120px !important;">
                        <b>Lokasi Tujuan</b></th>
                </tr> """

        for b in batch_obj:
            tgl_expired=b.expiration_date
            if tgl_expired:
                sisa_hari = (tgl_expired-now).days

                is_send = False
                send_expiredbatch_ids = []
                no = 0

                if sisa_hari != 30:
                    continue

                if sisa_hari == 30:
                    
                    send_expiredbatch_ids.append(b.product_id.product_tmpl_id.id)
                    # print(b)
                    is_send = True
                    no += 1

                    if b.product_id.product_tmpl_id.name:
                        nama_produk = str(b.product_id.product_tmpl_id.name)
                        # print(b.product_id.product_tmpl_id.name)
                    else:
                        nama_produk = "-"

                    if b.name:
                        batch = str(b.name)
                    else:
                        batch = "-"

                    if b.product_qty:
                        quantity = str(b.product_qty)
                    else:
                        quantity = "-" 

                    if b.expiration_date:
                        exp_date = str(b.expiration_date)
                    else:
                        exp_date = "-"
                    
                    lokasi = 'WH/STOCK'
                    lokasi_tujuan = 'WH/Karantina'

                    body_html += """<tr style="text-align: left;">
                    <td style="border:1px solid #dddddd; text-align: left; padding: 5px; font-size: 14px;  width:80px !important;">"""+ nama_produk +"""</td>
                    <td style="border:1px solid #dddddd; text-align: left; padding: 5px; font-size: 14px;  width:80px !important;">"""+ batch+"""</td>"""
        
                    body_html += """<td style="border:1px solid #dddddd; text-align: left; padding: 5px; font-size: 14px;  width:130px !important;">"""+ quantity +"""</td>"""
                    body_html += """<td style="border:1px solid #dddddd; text-align: left; padding: 5px; font-size: 14px;  width:80px !important;">"""+ exp_date +"""</td>"""
                    body_html += """<td style="border:1px solid #dddddd; text-align: left; padding: 5px; font-size: 14px;  width:120px !important;">"""+ lokasi +"""</td>"""
                    body_html += """<td style="border:1px solid #dddddd; text-align: left; padding: 5px; font-size: 14px;  width:120px !important;">"""+ lokasi_tujuan +"""</td>"""
                    body_html += """</tr>"""

        # print(body_html)

        email_values = {'body_html':body_html}

        template.send_mail(self.id, force_send=True, email_values=email_values)