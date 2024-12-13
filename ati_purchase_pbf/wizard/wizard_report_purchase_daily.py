from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta

class WizardReportPurchaseDaily(models.TransientModel):
    _name = 'wizard.report.purchase.daily'
    _description = 'Purchase Daily Report'

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')

    def button_generate_excel(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'wizard.report.purchase.daily'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        return self.env.ref('ati_purchase_pbf.wizard_report_purchase_daily_xlsx').report_action(self, data=datas)

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
        return self.env.ref('ati_purchase_pbf.wizard_report_purchase_daily').report_action(self, data=data)

class purchase_daily(models.AbstractModel):
    _name = 'report.ati_purchase_pbf.purchase_daily'

    def _get_report_values(self, docids, data=None):
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        docs = []

        start_date = datetime.strptime(data['form']['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['form']['end_date'], '%Y-%m-%d').date()
        n_date = (end_date - start_date).days
        list_of_date = [start_date + timedelta(days=n) for n in range(n_date+1)]

        delivery_product = [delivery.product_id.id for delivery in self.env['delivery.carrier'].sudo().search([('active', '=', True)])]

        data = []
        total_pembelian = 0
        total_pajak = 0
        total_ongkir = 0
        total_retur = 0
        total_retur_pajak = 0
        total_tunai_all = 0
        total_debit_all = 0
        total_kredit = 0
        total_cod_all = 0
        total_tempo_all = 0
        for lod in list_of_date:
            pembelian = 0
            pajak = 0
            ongkir = 0
            retur = 0
            retur_pajak = 0
            total_tunai = 0
            total_kredit = 0
            kredit = 0
            # purchase_order_ids = self.env['purchase.order'].sudo().search([('state', 'in', ['purchase', 'done']), ('date_planned', '>=', lod), ('date_planned', '<=', lod)], order='date_planned asc')
            purchase_order_ids = self.env['account.move'].sudo().search([('state', 'in', ['draft','approval','posted']), ('invoice_date', '>=', lod), ('invoice_date', '<=', lod),('move_type','=','in_invoice'),('source_document','!=', False)], order='invoice_date asc')
            for order in purchase_order_ids:
                kredit += order.amount_total
                pembelian += ((order.amount_untaxed or 0) - (order.total_global_discount or 0))
                # pajak += order.amount_tax or 0
                pajak += order.total_all_tax or 0
                # pajak += (order.amount_total - round(order.amount_untaxed, 2) - order.total_global_discount) or 0
                total_kredit += (((order.amount_untaxed or 0) - (order.total_global_discount or 0)) + (order.amount_tax or 0))
                # if delivery_product and order.order_line and order.order_line.filtered(lambda x: x.product_id.id in delivery_product):
                #     ongkir += sum(ongkos.price_subtotal for ongkos in order.order_line.filtered(lambda x: x.product_id.id in delivery_product))
            # refund_ids = self.env['account.move'].sudo().search([('move_type', '=', 'in_refund'), ('state', '=', 'posted'), ('payment_state', 'in', ['paid', 'in_payment', 'partial']), ('invoice_date', '=', lod)])
            refund_ids = self.env['account.move'].sudo().search([('move_type', '=', 'in_refund'), ('state', '=', ['draft','approval','posted']), ('invoice_date', '>=', lod), ('invoice_date', '<=', lod)])
            for refund in refund_ids:
                retur += refund.amount_untaxed or 0
                # retur = refund.amount_untaxed or 0
                # refund_amount_tax = -1 * (refund.amount_tax)
                refund_amount_tax = -1 * (refund.total_all_tax)
                retur_pajak += refund_amount_tax or 0

            # total_kredit = (kredit) - (retur + retur_pajak)
            total_kredit = (pembelian + pajak) - (retur + retur_pajak)
            total_cod = 0
            total_tempo = 0
            for order in purchase_order_ids:
                if order.invoice_payment_term_id.is_cod != False:
                    total_cod = total_kredit
                    total_tempo = 0
                else:
                    total_cod = 0
                    total_tempo = total_kredit
            data.append({
                'tanggal': lod.strftime("%d-%m-%Y"),
                'pembelian': pembelian,
                'pajak': pajak,
                'ongkir': ongkir,
                'retur': retur,
                'retur_pajak': retur_pajak,
                'total_cod': total_cod,
                'total_tempo': total_tempo,
                'total_debit': total_kredit
            })

            total_pembelian += pembelian
            total_pajak += pajak
            total_ongkir += ongkir
            total_retur += retur
            total_retur_pajak += retur_pajak
            total_cod_all += total_cod
            total_tempo_all += total_tempo
            total_debit_all += total_kredit

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
