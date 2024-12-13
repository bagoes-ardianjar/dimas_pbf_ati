from odoo import fields, models, api, _
from odoo.exceptions import UserError
import math

class WizardRekapPelanggan(models.TransientModel):
    _name = 'wizard.rekap.pelanggan'
    _description = 'Wizard Rekap Penjualan Per Pelanggan'

    name = fields.Char(string='Name', default='Laporan Rekap Penjualan Per Pelanggan')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    wizard_rekap_pelanggan_ids = fields.One2many('wizard.rekap.pelanggan.line', 'wizard_rekap_pelanggan_id', string='Wizard Rekap Pelanggan Ids')

    def func_print_profit_excel(self):
        vals_header = {
            "name": 'Laporan Rekap Penjualan Per Pelanggan',
            "start_date": self.start_date,
            "end_date": self.end_date
        }
        new_header = self.env['wizard.rekap.pelanggan'].sudo().create(vals_header)
        self._cr.execute("""(
            select
            z.code_customer as code_customer,
            z.customer_name as customer_name,
            sum(z.total_debit) as total_debit,
            sum(z.total_refund) as total_refund,
            sum(z.total_debit - z.total_refund) as total_penjualan
            from(
            select
            b.code_customer as code_customer,
            b.name as customer_name,
            case 
                when a.total_all_tax > 0 then
                coalesce((a.amount_untaxed - a.global_order_discount + a.total_all_tax),0)
                else coalesce((a.amount_untaxed - a.global_order_discount - a.total_all_tax),0)
            end as total_debit,
            coalesce((select sum(x.amount_untaxed+x.amount_tax) from account_move x where x.reversed_entry_id = a.id and x.state = 'posted' and x.move_type = 'out_refund' group by x.reversed_entry_id),0) as total_refund
            from account_move a
            join res_partner b on b.id = a.partner_id
            where a.state in ('draft','approval','posted')
            and date(a.invoice_date) >= '{_start_date}'
            and date(a.invoice_date) <= '{_end_date}'
            and a.move_type = 'out_invoice'
            and a.source_document is not null
            ) z
            group by z.code_customer,
            z.customer_name
        )""".format(_start_date=str(self.start_date),_end_date=str(self.end_date)))

        data_preview = self._cr.dictfetchall()
        if len(data_preview) > 0 :
            uid = self._uid
            for data in data_preview:
                ins_values = ",".join(["('{}','{}',{},{},{})".format(
                    data['code_customer'] or '',
                    data['customer_name'] or '',
                    round(data['total_penjualan'] or 0, 2),
                    uid,
                    new_header.id
                )])
                ins_query = "insert into wizard_rekap_pelanggan_line (code_customer," \
                            "customer_name,total_penjualan," \
                            "create_uid,wizard_rekap_pelanggan_id) values {_values}".format(_values=ins_values)
                self._cr.execute(ins_query)
                self._cr.commit()

        self._cr.execute("""(
                            select
                            z.customer_category as customer_category,
                            z.category_name as category_name,
                            sum(z.total_debit) as total_debit,
                            sum(z.total_refund) as total_refund,
                            sum(z.total_debit - z.total_refund) as total_penjualan_category
                            from(
                            select
                            d.id as customer_category,
                            case 
                                when d.id > 0 then
                                d.name
                                else 'CUSTOMER UMUM'
                            end as category_name,
                            case 
                                when a.total_all_tax > 0 then
                                coalesce((a.amount_untaxed - a.global_order_discount + a.total_all_tax),0)
                                else coalesce((a.amount_untaxed - a.global_order_discount - a.total_all_tax),0)
                            end as total_debit,
                            coalesce((select sum(x.amount_untaxed+x.amount_tax) from account_move x where x.reversed_entry_id = a.id and x.state = 'posted' and x.move_type = 'out_refund' group by x.reversed_entry_id),0) as total_refund
                            from account_move a
                            join res_partner b on b.id = a.partner_id
                            left join m_margin_res_partner_rel c on c.res_partner_id = b.id
                            left join m_margin d on d.id = c.m_margin_id
                            where a.state in ('draft','approval','posted') 
                            and date(a.invoice_date) >= '{_start_date}'
                            and date(a.invoice_date) <= '{_end_date}'
                            and a.move_type = 'out_invoice'
                            and a.source_document is not null
                            and a.is_pasien is not True
                            ) z
                            group by
                            z.customer_category,
                            z.category_name
                        )""".format(_start_date=str(self.start_date), _end_date=str(self.end_date)))
        data_category_customer = self._cr.dictfetchall()
        if len(data_category_customer) > 0:
            uid = self._uid
            for category in data_category_customer:
                ins_values = ",".join(["('{}',{},{},{})".format(
                    category['category_name'] or '',
                    round(category['total_penjualan_category'] or 0, 2),
                    uid,
                    new_header.id
                )])
                ins_query = "insert into wizard_rekap_pelanggan_line (category_name," \
                            "total_penjualan_category," \
                            "create_uid,wizard_rekap_pelanggan_id) values {_values}".format(_values=ins_values)
                self._cr.execute(ins_query)
                self._cr.commit()

        self._cr.execute("""(
            select
            z.customer_name as customer_panel_name,
            sum(z.total_debit) as total_debit_panel,
            sum(z.total_refund) as total_refund_panel,
            sum(z.total_debit - z.total_refund) as total_penjualan_panel
            from(
            select
            b.code_customer as code_customer,
            b.name as customer_name,
            case 
                when a.total_all_tax > 0 then
                coalesce((a.amount_untaxed - a.global_order_discount + a.total_all_tax),0)
                else coalesce((a.amount_untaxed - a.global_order_discount - a.total_all_tax),0)
            end as total_debit,
            coalesce((select sum(x.amount_untaxed+x.amount_tax) from account_move x where x.reversed_entry_id = a.id and x.state = 'posted' and x.move_type = 'out_refund' group by x.reversed_entry_id),0) as total_refund
            from account_move a
            join res_partner b on b.id = a.partner_id
            where a.state in ('draft','approval','posted') 
            and date(a.invoice_date) >= '{_start_date}'
            and date(a.invoice_date) <= '{_end_date}'
            and a.move_type = 'out_invoice'
            and a.source_document is not null
            and a.is_pasien = True
            ) z
            group by
            z.customer_name
        )""".format(_start_date=str(self.start_date),_end_date=str(self.end_date)))

        data_panel = self._cr.dictfetchall()
        if len(data_panel) > 0 :
            uid = self._uid
            for panel in data_panel:
                ins_values = ",".join(["('{}',{},{},{})".format(
                    panel['customer_panel_name'] or '',
                    round(panel['total_penjualan_panel'] or 0, 2),
                    uid,
                    new_header.id
                )])
                ins_query = "insert into wizard_rekap_pelanggan_line (customer_panel_name," \
                            "total_penjualan_panel," \
                            "create_uid,wizard_rekap_pelanggan_id) values {_values}".format(_values=ins_values)
                self._cr.execute(ins_query)
                self._cr.commit()

        return {
            'type': 'ir.actions.act_url',
            'url' : '/rekap_pelanggan_report/%s' % (new_header.id),
            'target' : 'new',
        }

class wizard_rekap_pelanggan_line(models.TransientModel):
    _name = 'wizard.rekap.pelanggan.line'

    wizard_rekap_pelanggan_id = fields.Many2one('wizard.rekap.pelanggan', string='Wizard Rekap Pelanggan Id')
    code_customer = fields.Char(string='Kode Pelanggan')
    customer_name = fields.Char(string='Nama Pelanggan')
    total_penjualan = fields.Float(string='Total Penjualan')
    customer_panel_name = fields.Char(string='Nama Pelanggan Panel')
    total_penjualan_panel = fields.Float(string='Total Penjualan Panel')
    category_name = fields.Char(string='Kategori Customer')
    total_penjualan_category = fields.Float(string='Total Penjualan Category')