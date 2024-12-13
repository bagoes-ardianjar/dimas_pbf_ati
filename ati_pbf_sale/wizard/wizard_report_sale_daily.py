from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta

class WizardReportSaleDaily(models.TransientModel):
    _name = 'wizard.report.sale.daily'
    _description = 'Sale Daily Report'

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')

    def button_generate_excel(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'wizard.report.sale.daily'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        return self.env.ref('ati_pbf_sale.wizard_report_sale_daily_xlsx').report_action(self, data=datas)

    def button_generate_preview(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'start_date': self.start_date,
                'end_date': self.end_date
            },
        }
        # data = {'start_date': self.start_date, 'end_date': self.end_date}
        return self.env.ref('ati_pbf_sale.wizard_report_sale_daily').report_action(self, data=data)

class sale_daily(models.AbstractModel):
    _name = 'report.ati_pbf_sale.sale_daily'

    def _get_report_values(self, docids, data=None):
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        docs = []

        start_date = datetime.strptime(data['form']['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['form']['end_date'], '%Y-%m-%d').date()
        n_date = (end_date - start_date).days
        list_of_date = [start_date + timedelta(days=n) for n in range(n_date+1)]
        self._cr.execute(
            """
                select
                    o.tanggal as tanggal,
                    coalesce(sum(o.penjualan),0) as penjualan,
                    coalesce(sum(o.pajak),0) as pajak,
                    coalesce(sum(o.retur),0) as retur,
                    coalesce(sum(o.retur_pajak),0) as retur_pajak,
                    coalesce(sum(o.total_cod_so),0) as total_cod_so,
                    coalesce(sum(o.total_tempo_so),0) as total_tempo_so,
                    coalesce(sum(o.total_cod_retur),0) as total_cod_retur,
                    coalesce(sum(o.total_tempo_retur),0) as total_tempo_retur
                    from(
                        select 
                            date(a.invoice_date) as tanggal,
                            case 
                                when a.total_global_discount >= 0 then 
                                coalesce((a.amount_untaxed - a.total_global_discount),0)
                                else coalesce((a.amount_untaxed + a.total_global_discount),0)
                            end as penjualan,
                            case 
                                when a.total_all_tax >= 0 then
                                coalesce((a.total_all_tax),0)
                                else coalesce((a.total_all_tax),0)
                            end as pajak,
                            coalesce((select sum(x.amount_untaxed) 
                                from account_move x 
                                where x.reversed_entry_id = a.id 
                                and x.state in ('draft','approval','posted') 
                                and x.move_type = 'out_refund' 
                                group by x.reversed_entry_id),0) as retur,
                            coalesce((select sum(x.total_all_tax) 
                                from account_move x 
                                where x.reversed_entry_id = a.id 
                                and x.state in ('draft','approval','posted') 
                                and x.move_type = 'out_refund' 
                                group by x.reversed_entry_id),0) as retur_pajak,
                            (select 
                                case 
                                    when y.total_all_tax > 0 then
                                    coalesce((y.amount_untaxed - y.global_order_discount + y.total_all_tax),0)
                                    else coalesce((y.amount_untaxed - y.global_order_discount + y.total_all_tax),0)
                                end
                            from account_move y
                                left join account_payment_term z on z.id = y.invoice_payment_term_id 
                            where y.id = a.id and
                                z.is_cod is True) as total_cod_so,
                            (select 
                                case 
                                    when y.total_all_tax > 0 then
                                    coalesce((y.amount_untaxed - y.global_order_discount + y.total_all_tax),0)
                                    else coalesce((y.amount_untaxed - y.global_order_discount + y.total_all_tax),0)
                                end
                            from account_move y
                                left join account_payment_term z on z.id = y.invoice_payment_term_id 
                            where y.id = a.id and
                                z.is_cod is not True) as total_tempo_so,
                            coalesce((select sum(m.amount_untaxed + m.total_all_tax) 
                                from account_move m 
                                left join account_payment_term n on n.id = m.invoice_payment_term_id
                                where m.reversed_entry_id = a.id 
                                and m.state in ('draft','approval','posted') 
                                and m.move_type = 'out_refund'
                                and n.is_cod is True
                                group by m.reversed_entry_id),0) as total_cod_retur,
                            coalesce((select sum(m.amount_untaxed + m.total_all_tax) 
                                from account_move m 
                                left join account_payment_term n on n.id = m.invoice_payment_term_id
                                where m.reversed_entry_id = a.id 
                                and m.state in ('draft','approval','posted') 
                                and m.move_type = 'out_refund'
                                and n.is_cod is not True
                                group by m.reversed_entry_id),0) as total_tempo_retur
                        from account_move a
                        where
                            DATE(a.invoice_date) >= '{_start_date}' 
                            and DATE(a.invoice_date) <= '{_end_date}'
                            and a.state in ('draft','approval','posted')
                            and a.source_document is not Null
                            and a.move_type = 'out_invoice' ) o
                    group by
                    o.tanggal
                    order by o.tanggal asc
            """.format(_start_date=start_date, _end_date=end_date))
        res_penjualan = self._cr.dictfetchall()

        if res_penjualan:
            total_cod = 0
            total_tempo = 0
            total_debit = 0
            total_pembelian = 0
            total_pajak =0
            total_ongkir = 0
            total_retur =0
            total_retur_pajak=0
            total_cod_all=0
            total_tempo_all=0
            total_debit_all=0
            data = []
            for rec in res_penjualan:
                tanggal = rec.get('tanggal').strftime('%Y-%m-%d') if rec.get('tanggal') else '-'
                total_cod = rec.get('total_cod_so') - rec.get('total_cod_retur')
                total_tempo = rec.get('total_tempo_so') - rec.get('total_tempo_retur')
                total_debit = (rec.get('penjualan') + rec.get('pajak')) - (rec.get('retur') + rec.get('retur_pajak'))
                data.append({
                    'tanggal': tanggal,
                    'pembelian': rec.get('penjualan'),
                    'pajak': rec.get('pajak'),
                    'ongkir': '',
                    'retur': rec.get('retur'),
                    'retur_pajak': rec.get('retur_pajak'),
                    'total_cod': total_cod,
                    'total_tempo': total_tempo,
                    'total_debit': total_debit
                })

                total_pembelian += rec.get('penjualan')
                total_pajak += rec.get('pajak')
                total_ongkir = ''
                total_retur += rec.get('retur')
                total_retur_pajak += rec.get('retur_pajak')
                total_cod_all += total_cod
                total_tempo_all += total_tempo
                total_debit_all += total_debit

            if data:
                docs = data

            result = {
                # 'doc_ids': data['ids'],
                # 'doc_model': data['model'],
                'start_date': start_date,
                'end_date': end_date,
                'docs': docs,
                'total_pembelian': total_pembelian,
                'total_pajak': total_pajak,
                'total_ongkir': total_ongkir,
                'total_retur': total_retur,
                'total_retur_pajak': total_retur_pajak,
                'total_cod_all': total_cod_all,
                'total_tempo_all': total_tempo_all,
                'total_debit_all': total_debit_all
            }
            return result

        # data = []
        # total_pembelian = 0
        # total_pajak = 0
        # total_ongkir = 0
        # total_retur = 0
        # total_retur_pajak = 0
        # total_tunai_all = 0
        # total_debit_all = 0
        # total_debit = 0
        # total_cod_all = 0
        # total_tempo_all = 0
        # for lod in list_of_date:
        #     pembelian = 0
        #     pajak = 0
        #     ongkir = 0
        #     retur = 0
        #     retur_pajak = 0
        #     total_tunai = 0
        #     total_debit = 0
        #     amount_tax = 0
        #     total_cod = 0
        #     total_tempo = 0
        #     total_cod_so = 0
        #     total_tempo_so = 0
        #     total_cod_return = 0
        #     total_tempo_return = 0
        #     # sale_order_ids = self.env['sale.order'].sudo().search([('state', 'in', ['sale', 'done']), ('date_order', '>=', lod), ('date_order', '<=', lod)], order='date_order asc')
        #     sale_order_ids = self.env['account.move'].sudo().search([('state', 'in', ['draft','posted']), ('invoice_date', '>=', lod), ('invoice_date', '<=', lod),('move_type','=','out_invoice')], order='invoice_date asc')
        #     for order in sale_order_ids:
        #         pembelian += ((order.amount_untaxed or 0) + (order.total_global_discount or 0))
        #         if order.amount_tax >= 0 :
        #             amount_tax = order.amount_tax
        #         elif order.amount_tax < 0 :
        #             amount_tax = -1 * order.amount_tax
        #
        #         if order.invoice_payment_term_id.is_cod != False:
        #             total_cod_so += ((order.amount_untaxed or 0) + (order.total_global_discount or 0)) + (amount_tax or 0)
        #         if order.invoice_payment_term_id.is_cod == False:
        #             total_tempo_so += ((order.amount_untaxed or 0) + (order.total_global_discount or 0)) + (amount_tax or 0)
        #         pajak += amount_tax or 0
        #         # total_debit += (((order.amount_untaxed or 0) + (order.total_global_discount or 0)) + (amount_tax or 0))
        #         # if order.carrier_id and order.order_line and order.order_line.filtered(lambda x: x.product_id == order.carrier_id.product_id):
        #         #     ongkir += sum(ongkos.price_subtotal for ongkos in order.order_line.filtered(lambda x: x.product_id == order.carrier_id.product_id))
        #     # credit_note_ids = self.env['account.move'].sudo().search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'), ('payment_state', 'in', ['paid', 'in_payment', 'partial']), ('invoice_date', '=', lod)])
        #     credit_note_ids = self.env['account.move'].sudo().search([('move_type', '=', 'out_refund'), ('state', 'in', ['draft','posted']), ('invoice_date', '=', lod)])
        #     for cn in credit_note_ids:
        #         retur += cn.amount_untaxed or 0
        #         retur_pajak += cn.amount_tax or 0
        #
        #         if cn.invoice_payment_term_id.is_cod != False:
        #             total_cod_return += (cn.amount_untaxed or 0) + (cn.amount_tax or 0)
        #         if cn.invoice_payment_term_id.is_cod == False:
        #             total_tempo_return += (cn.amount_untaxed or 0) + (cn.amount_tax or 0)
        #
        #     total_debit = (pembelian + pajak) - (retur + retur_pajak)
        #     total_cod = total_cod_so - total_cod_return
        #     total_tempo = total_tempo_so - total_tempo_return
        #
        #     # for order in sale_order_ids:
        #     #     if order.invoice_payment_term_id.is_cod != False:
        #     #         total_cod = total_debit
        #     #         total_tempo = 0
        #     #     else:
        #     #         total_cod = 0
        #     #         total_tempo = total_debit
        #     data.append({
        #         'tanggal': lod.strftime("%d-%m-%Y"),
        #         'pembelian': pembelian,
        #         'pajak': pajak,
        #         'ongkir': ongkir,
        #         'retur': retur,
        #         'retur_pajak': retur_pajak,
        #         'total_cod': total_cod,
        #         'total_tempo': total_tempo,
        #         'total_debit': total_debit
        #     })
        #
        #     total_pembelian += pembelian
        #     total_pajak += pajak
        #     total_ongkir += ongkir
        #     total_retur += retur
        #     total_retur_pajak += retur_pajak
        #     total_cod_all += total_cod
        #     total_tempo_all += total_tempo
        #     total_debit_all += total_debit
        #
        # if data:
        #     docs = data
        #
        #
        # result = {
        #     # 'doc_ids': data['ids'],
        #     # 'doc_model': data['model'],
        #     'start_date': start_date,
        #     'end_date': end_date,
        #     'docs': docs,
        #     'total_pembelian': total_pembelian,
        #     'total_pajak': total_pajak,
        #     'total_ongkir': total_ongkir,
        #     'total_retur': total_retur,
        #     'total_retur_pajak': total_retur_pajak,
        #     'total_cod_all': total_cod_all,
        #     'total_tempo_all': total_tempo_all,
        #     'total_debit_all': total_debit_all
        # }
        # return result

