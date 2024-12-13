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
import math

FK_HEAD_LIST = ['FK', 'KD_JENIS_TRANSAKSI', 'FG_PENGGANTI', 'NOMOR_FAKTUR', 'MASA_PAJAK', 'TAHUN_PAJAK', 'TANGGAL_FAKTUR', 'NPWP', 'NAMA', 'ALAMAT_LENGKAP', 'JUMLAH_DPP', 'JUMLAH_PPN', 'JUMLAH_PPNBM', 'ID_KETERANGAN_TAMBAHAN', 'FG_UANG_MUKA', 'UANG_MUKA_DPP', 'UANG_MUKA_PPN', 'UANG_MUKA_PPNBM', 'REFERENSI', 'KODE_DOKUMEN_PENDUKUNG']

LT_HEAD_LIST = ['LT', 'NPWP', 'NAMA', 'JALAN', 'BLOK', 'NOMOR', 'RT', 'RW', 'KECAMATAN', 'KELURAHAN', 'KABUPATEN', 'PROPINSI', 'KODE_POS', 'NOMOR_TELEPON']

OF_HEAD_LIST = ['OF', 'KODE_OBJEK', 'NAMA', 'HARGA_SATUAN', 'JUMLAH_BARANG', 'HARGA_TOTAL', 'DISKON', 'DPP', 'PPN', 'TARIF_PPNBM', 'PPNBM']


def _csv_row(data, delimiter=',', quote='"'):
    return quote + (quote + delimiter + quote).join([str(x).replace(quote, '\\' + quote) for x in data]) + quote + '\n'




class InheritAccountMove(models.Model):
    _inherit = 'account.move'

    def _compute_flag_readonly(self):
        for this in self:
            if this.partner_id.id != False:
                if this.partner_id.l10n_id_kode_transaksi == False or this.partner_id.l10n_id_kode_transaksi == '':
                    is_readonly = False
                else:
                    this.l10n_id_kode_transaksi = this.partner_id.l10n_id_kode_transaksi
                    is_readonly = True
            else:
                is_readonly = False
            this.flag_readonly = is_readonly

    @api.model
    def get_default_user(self):
        user=self.env.user
        return user.id

    @api.onchange('user_helper_id','partner_id')
    def func_onchange_user_id(self):
        self._compute_flag_readonly()

    # @api.onchange('l10n_id_tax_number')
    # def _onchange_l10n_id_tax_number(self):
    #     for record in self:
    #         if record.l10n_id_tax_number and record.move_type not in self.get_purchase_types():
    #             # raise UserError(_("You can only change the number manually for a Vendor Bills and Credit Notes"))
    #             pass

    # def write(self, vals):
    #     res = super(InheritAccountMove, self).write(vals)
    #     if 'partner_id' in vals:
    #         kode_transaksi = vals['partner_id.l10n_id_kode_transaksi']
    #         print("aaa", kode_transaksi)
    #         update_data = "update account_move set l10n_id_kode_transaksi = '{_number}' where id = {_id}".format(_number=kode_transaksi,_id=self.id)
    #         self._cr.execute(update_data)
    #     return res

    flag_readonly = fields.Boolean(compute=_compute_flag_readonly)
    user_helper_id=fields.Many2one('res.users', default=get_default_user)

    def _generate_efaktur_invoice(self, delimiter):
        """Generate E-Faktur for customer invoice."""
        # Invoice of Customer
        company_id = self.company_id
        dp_product_id = self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')

        output_head = '%s%s%s' % (
            _csv_row(FK_HEAD_LIST, delimiter),
            _csv_row(LT_HEAD_LIST, delimiter),
            _csv_row(OF_HEAD_LIST, delimiter),
        )
        total_ppn=0
        total_dpp=0
        ppn =0
        dpp=0
        for move in self.filtered(lambda m: m.state == 'posted'):
            # total_dpp = sum([int(line.price_subtotal) for line in move.line_ids.filtered(lambda l: not l.exclude_from_invoice_tab and not l.display_type)])
            eTax = move._prepare_etax()

            # free_tax_line_new = tax_line_new = bruto_total_new = total_discount_new = 0.0
            for line_new in move.line_ids.filtered(lambda l: not l.exclude_from_invoice_tab and not l.display_type):
                global_discount = move.global_order_discount
                global_discount_line = global_discount / len(move.line_ids.filtered(lambda l: not l.exclude_from_invoice_tab and not l.display_type))
                dpp = round((line_new.price_subtotal - global_discount_line),0)
                total_dpp += dpp
                ppn = round((dpp * 11 / 100),0)
                total_ppn += ppn
                # if line_new.price_subtotal < 0:
                #     for tax in line_new.tax_ids:
                #         total_ppn += int((line_new.price_subtotal * (tax.amount / 100.0)) * -1.0)
                #         # print('ppn1',(line_new.price_subtotal * (tax.amount / 100.0)) * -1.0)
                #
                # elif line_new.price_subtotal != 0.0:
                #     for tax in line_new.tax_ids:
                #         if tax.amount > 0:
                #             total_ppn += int(line_new.price_subtotal * (tax.amount / 100.0))
                #             # print('ppn',line_new.price_subtotal * (tax.amount / 100.0))

            # nik = str(move.partner_id.l10n_id_nik) if not move.partner_id.vat elif move.partner_id.l10n_id_nik
            nik = str(move.partner_id.l10n_id_nik) or ''
            number_ref = str(move.name) + " - " + str(nik)

            # if move.l10n_id_replace_invoice_id:
            #     number_ref = str(move.l10n_id_replace_invoice_id.name) + " replaced by " + str(move.name) + " " + nik
            # else:
            #     number_ref = str(move.name) + " " + nik

            street = ', '.join([x for x in (move.partner_id.street, move.partner_id.street2) if x])

            invoice_npwp = ''
            if move.partner_id.vat and len(move.partner_id.vat) > 0:
                invoice_npwp = move.partner_id.vat
            elif (not move.partner_id.vat or len(move.partner_id.vat) < 1) and move.partner_id.l10n_id_nik:
                invoice_npwp = move.partner_id.l10n_id_nik
            invoice_npwp = invoice_npwp.replace('.', '').replace('-', '')

            nomor_faktur = move.l10n_id_tax_number[3:]
            if len(nomor_faktur) > 13:
                index = len(nomor_faktur) - 13
            else:
                index = 0
            new_nomor_faktur = nomor_faktur[index:]

            # Here all fields or columns based on eTax Invoice Third Party
            eTax['KD_JENIS_TRANSAKSI'] = move.l10n_id_tax_number[0:2] or 0
            eTax['FG_PENGGANTI'] = move.l10n_id_tax_number[2:3] or 0
            eTax['NOMOR_FAKTUR'] = new_nomor_faktur or 0
            # eTax['NOMOR_FAKTUR'] = move.l10n_id_tax_number[3:] or 0
            eTax['MASA_PAJAK'] = move.invoice_date.month
            eTax['TAHUN_PAJAK'] = move.invoice_date.year
            eTax['TANGGAL_FAKTUR'] = '{0}/{1}/{2}'.format(move.invoice_date.day, move.invoice_date.month, move.invoice_date.year)
            eTax['NPWP'] = invoice_npwp
            # eTax['NAMA'] = invoice_npwp+'#'+'NIK'+'#'+'NAMA'+'#'+new_name
            eTax['NAMA'] = move.partner_id.name if eTax['NPWP'] == '000000000000000' else move.partner_id.l10n_id_tax_name or move.partner_id.name
            eTax['ALAMAT_LENGKAP'] = move.partner_id.contact_address.replace('\n', '') if eTax['NPWP'] == '000000000000000' else move.partner_id.l10n_id_tax_address or street
            eTax['JUMLAH_DPP'] = int(total_dpp)
            # eTax['JUMLAH_DPP'] = int(round(move.amount_untaxed, 0))# currency rounded to the unit
            # eTax['JUMLAH_PPN'] = int(round(move.amount_tax, 0))
            eTax['JUMLAH_PPN'] = int(total_ppn)
            eTax['ID_KETERANGAN_TAMBAHAN'] = '1' if move.l10n_id_kode_transaksi == '07' else ''
            eTax['REFERENSI'] = number_ref
            eTax['KODE_DOKUMEN_PENDUKUNG'] = '0'

            lines = move.line_ids.filtered(lambda x: x.product_id.id == int(dp_product_id) and x.price_unit < 0 and not x.display_type)
            eTax['FG_UANG_MUKA'] = 0
            eTax['UANG_MUKA_DPP'] = int(abs(sum(lines.mapped('price_subtotal'))))
            eTax['UANG_MUKA_PPN'] = int(abs(sum(lines.mapped(lambda l: l.price_total - l.price_subtotal))))

            company_npwp = company_id.partner_id.vat or '000000000000000'

            fk_values_list = ['FK'] + [eTax[f] for f in FK_HEAD_LIST[1:]]
            eTax['JALAN'] = company_id.partner_id.l10n_id_tax_address or company_id.partner_id.street
            eTax['NOMOR_TELEPON'] = company_id.phone or ''

            lt_values_list = ['FAPR', company_npwp, company_id.name] + [eTax[f] for f in LT_HEAD_LIST[3:]]

            # HOW TO ADD 2 line to 1 line for free product
            free, sales = [], []

            for line in move.line_ids.filtered(lambda l: not l.exclude_from_invoice_tab and not l.display_type):
                # *invoice_line_unit_price is price unit use for harga_satuan's column
                # *invoice_line_quantity is quantity use for jumlah_barang's column
                # *invoice_line_total_price is bruto price use for harga_total's column
                # *invoice_line_discount_m2m is discount price use for diskon's column
                # *line.price_subtotal is subtotal price use for dpp's column
                # *tax_line or free_tax_line is tax price use for ppn's column
                free_tax_line = tax_line = bruto_total = total_discount = 0.0

                for tax in line.tax_ids:
                    if tax.amount > 0:
                        tax_line += line.price_subtotal * (tax.amount / 100.0)

                # invoice_line_unit_price = line.price_unit
                invoice_line_unit_price = line.ati_price_unit + line.product_margin_amount
                pecahan = invoice_line_unit_price % 1
                satuan = invoice_line_unit_price - pecahan

                if pecahan > 0 or satuan > 0:
                    harga_satuan_baru = math.ceil(invoice_line_unit_price / 50) * 50
                    ati_harga_satuan_baru = harga_satuan_baru
                else:
                    harga_satuan_baru = invoice_line_unit_price
                    ati_harga_satuan_baru = harga_satuan_baru

                invoice_line_total_price = ati_harga_satuan_baru * line.quantity
                global_discount = move.global_order_discount
                global_discount_line = global_discount/len(move.line_ids.filtered(lambda l: not l.exclude_from_invoice_tab and not l.display_type))
                dpp = line.price_subtotal - global_discount_line
                ppn = dpp * 11 / 100



                line_dict = {
                    'KODE_OBJEK': line.product_id.default_code or '',
                    # 'NAMA': line.product_id.product_tmpl_id.display_name or '',
                    # 'NAMA': '['+str(line.product_id.default_code)+'] '+line.product_id.name,
                    'NAMA': line.product_id.name,
                    'HARGA_SATUAN': int(ati_harga_satuan_baru),
                    'JUMLAH_BARANG': line.quantity,
                    'HARGA_TOTAL': int(line.price_subtotal),
                    # 'DPP': int(line.price_subtotal),
                    'DPP': int(round(dpp,0)),
                    'product_id': line.product_id.id,
                }

                if line.price_subtotal < 0:
                    for tax in line.tax_ids:
                        free_tax_line += (line.price_subtotal * (tax.amount / 100.0)) * -1.0

                    line_dict.update({
                        # 'DISKON': int(invoice_line_total_price - line.price_subtotal),
                        # 'DISKON': int((invoice_line_total_price - line.price_subtotal) + global_discount_line),
                        'DISKON': int((line.discount_amount * line.quantity) + global_discount_line),
                        # 'PPN': int(free_tax_line),
                        'PPN': int(round(ppn,0)),
                    })
                    free.append(line_dict)
                elif line.price_subtotal != 0.0:
                    # invoice_line_discount_m2m = (invoice_line_total_price - line.price_subtotal)
                    # invoice_line_discount_m2m = int((invoice_line_total_price - line.price_subtotal)+ global_discount_line)
                    invoice_line_discount_m2m = int((line.discount_amount * line.quantity) + global_discount_line)
                    line_dict.update({
                        'DISKON': int(invoice_line_discount_m2m),
                        # 'PPN': int(tax_line),
                        'PPN': int(round(ppn,0)),
                    })
                    sales.append(line_dict)

            sub_total_before_adjustment = sub_total_ppn_before_adjustment = 0.0

            # We are finding the product that has affected
            # by free product to adjustment the calculation
            # of discount and subtotal.
            # - the price total of free product will be
            # included as a discount to related of product.
            for sale in sales:
                for f in free:
                    if f['product_id'] == sale['product_id']:
                        sale['DISKON'] = sale['DISKON'] - f['DISKON'] + f['PPN']
                        sale['DPP'] = sale['DPP'] + f['DPP']

                        tax_line = 0

                        for tax in line.tax_ids:
                            if tax.amount > 0:
                                tax_line += sale['DPP'] * (tax.amount / 100.0)

                        sale['PPN'] = int(tax_line)

                        free.remove(f)

                sub_total_before_adjustment += sale['DPP']
                sub_total_ppn_before_adjustment += sale['PPN']
                bruto_total += sale['DISKON']
                total_discount += round(sale['DISKON'], 2)

            output_head += _csv_row(fk_values_list, delimiter)
            output_head += _csv_row(lt_values_list, delimiter)
            for sale in sales:
                of_values_list = ['OF'] + [str(sale[f]) for f in OF_HEAD_LIST[1:-2]] + ['0', '0']
                output_head += _csv_row(of_values_list, delimiter)

        return output_head



    