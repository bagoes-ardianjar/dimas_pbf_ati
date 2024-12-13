from odoo import fields, models, api, _
from odoo.exceptions import UserError

class WizardVendorPurchase(models.TransientModel):
    _name = 'wizard.vendor.purchase'
    _description = 'Wizard Vendor Purchase Report'

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    partner_id = fields.Many2one('res.partner', 'Supplier')

    def button_generate_excel(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'wizard.vendor.purchase'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        return self.env.ref('ati_purchase_pbf.wizard_vendor_purchase_xlsx').report_action(self, data=datas)

    def button_generate_preview(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'partner_id': self.partner_id.id if self.partner_id else None
            },
        }
        # data = {'start_date': self.start_date, 'end_date': self.end_date}
        return self.env.ref('ati_purchase_pbf.wizard_vendor_purchase').report_action(self, data=data)

class vendor_purchase(models.AbstractModel):
    _name = 'report.ati_purchase_pbf.vendor_purchase'

    def _get_report_values(self, docids, data=None):
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        partner_id = data['form']['partner_id']
        docs = []

        data_all = {}
        list_partner = []
        total_pembelian_all = 0
        total_pajak_all = 0
        total_retur = 0
        total_retur_pajak = 0
        total_kredit_all = 0
        total_refund = 0
        currency_id = self.env['res.currency'].search([('name', '=', 'IDR')], limit=1)
        # purchase_order_ids = self.env['purchase.order'].sudo().search([('state', 'in', ['purchase', 'done']), ('date_planned', '>=', start_date), ('date_planned', '<=', end_date)], order='date_planned asc')
        purchase_order_ids = self.env['account.move'].sudo().search([('state', 'in', ['draft','approval','posted']), ('invoice_date', '>=', start_date), ('invoice_date', '<=', end_date),('move_type','=','in_invoice'),('source_document','!=', False)], order='invoice_date asc')
        if partner_id:
            # purchase_order_ids = self.env['purchase.order'].sudo().search([('state', 'in', ['purchase', 'done']), ('date_planned', '>=', start_date), ('date_planned', '<=', end_date), ('partner_id', '=', partner_id)], order='date_planned asc')
            purchase_order_ids = self.env['account.move'].sudo().search([('state', 'in', ['draft','approval','posted']), ('invoice_date', '>=', start_date), ('invoice_date', '<=', end_date),('move_type','=','in_invoice'),('source_document','!=', False), ('partner_id', '=', partner_id)], order='invoice_date asc')

        for order in purchase_order_ids:
            if order.partner_id.id not in list_partner:
                list_partner.append(order.partner_id.id)
                data_all[order.partner_id.id] = {
                    'code': order.partner_id.code_customer,
                    'name': order.partner_id.name,
                    'pembelian': 0.0,
                    'pajak': 0.0,
                    'total': 0.0,
                    'kredit': 0.0,
                    'retur': 0.0,
                    'retur_pajak': 0.0,
                    'refund': 0.0,
                    'currency_id': order.currency_id
                }
            data_all[order.partner_id.id]['pembelian'] += (order.amount_untaxed - order.total_global_discount)
            # data_all[order.partner_id.id]['pajak'] += order.amount_tax
            data_all[order.partner_id.id]['pajak'] += order.total_all_tax
            # data_all[order.partner_id.id]['pajak'] += (order.amount_total - order.amount_untaxed - order.total_global_discount)
            # data_all[order.partner_id.id]['kredit'] += ((order.amount_untaxed-order.total_global_discount)+order.amount_tax)
            data_all[order.partner_id.id]['kredit'] += ((order.amount_untaxed - order.total_global_discount) + order.total_all_tax)
            # data_all[order.partner_id.id]['kredit'] += order.amount_total
            total_pembelian_all += (order.amount_untaxed - order.total_global_discount)
            # total_pajak_all += order.amount_tax
            total_pajak_all += order.total_all_tax
            # total_pajak_all += (order.amount_total - order.amount_untaxed - order.total_global_discount)
            # total_kredit_all += ((order.amount_untaxed-order.total_global_discount)+order.amount_tax)
            total_kredit_all += ((order.amount_untaxed - order.total_global_discount) + order.total_all_tax)
            # total_kredit_all += order.amount_total

        credit_note_ids = self.env['account.move'].sudo().search([('move_type', '=', 'in_refund'), ('state', 'in', ['draft','approval','posted']), ('invoice_date', '>=', start_date), ('invoice_date', '<=', end_date)])
        if partner_id:
            # credit_note_ids = self.env['account.move'].sudo().search([('move_type', '=', 'in_refund'), ('state', '=', 'posted'), ('payment_state', 'in', ['paid', 'in_payment', 'partial']), ('invoice_date', '>=', start_date), ('invoice_date', '<=', end_date), ('partner_id', '=', partner_id)])
            credit_note_ids = self.env['account.move'].sudo().search([('move_type', '=', 'in_refund'), ('state', 'in', ['draft','approval','posted']), ('invoice_date', '>=', start_date), ('invoice_date', '<=', end_date), ('partner_id', '=', partner_id)])
        for cn in credit_note_ids:
            if cn.partner_id.id not in list_partner:
                list_partner.append(cn.partner_id.id)
                data_all[cn.partner_id.id] = {
                    'code': cn.partner_id.code_customer,
                    'name': cn.partner_id.name,
                    'pembelian': 0.0,
                    'pajak': 0.0,
                    'total': 0.0,
                    'kredit': 0.0,
                    'retur': 0.0,
                    'retur_pajak': 0.0,
                    'refund': 0.0,
                    'currency_id': cn.currency_id
                }
            data_all[cn.partner_id.id]['retur'] += cn.amount_untaxed
            # cn_amount_tax = -1 * (cn.amount_tax)
            cn_amount_tax = -1 * (cn.total_all_tax)
            data_all[cn.partner_id.id]['retur_pajak'] += cn_amount_tax
            data_all[cn.partner_id.id]['refund'] += cn.amount_untaxed + cn_amount_tax
            total_retur += cn.amount_untaxed
            total_retur_pajak += cn_amount_tax
            total_refund += (cn.amount_untaxed + cn_amount_tax)

        result = {
            # 'doc_ids': data['ids'],
            # 'doc_model': data['model'],
            'start_date': start_date,
            'end_date': end_date,
            'docs': docs,
            'data_all': data_all,
            'list_partner': list_partner,
            'total_pembelian_all': total_pembelian_all,
            'total_pajak_all': total_pajak_all,
            'total_retur': total_retur,
            'total_retur_pajak': total_retur_pajak,
            'total_refund': total_refund,
            'total_kredit_all': total_kredit_all
        }
        return result
