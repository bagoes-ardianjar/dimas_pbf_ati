from odoo import fields, models, api, _
from odoo.exceptions import UserError

class WizardCustomerSale(models.TransientModel):
    _name = 'wizard.customer.sale'
    _description = 'Wizard Customer Sale Report'

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    partner_id = fields.Many2one('res.partner', 'Customer')
    is_pasien = fields.Boolean(string='Is Panel')

    def button_generate_excel(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'wizard.customer.sale'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        return self.env.ref('ati_pbf_sale.wizard_customer_sale_xlsx').report_action(self, data=datas)

    def button_generate_preview(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'is_pasien': self.is_pasien,
                'partner_id': self.partner_id.id if self.partner_id else None
            },
        }
        # data = {'start_date': self.start_date, 'end_date': self.end_date}
        return self.env.ref('ati_pbf_sale.wizard_customer_sale').report_action(self, data=data)
class customer_sale(models.AbstractModel):
    _name = 'report.ati_pbf_sale.customer_sale'

    def _get_report_values(self, docids, data=None):
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        partner_id = data['form']['partner_id']
        is_pasien = data['form']['is_pasien']
        docs = []

        data_all = {}
        list_partner = []
        total_penjualan_all = 0
        total_pajak_all = 0
        total_retur = 0
        total_retur_pajak = 0
        total_debit_all = 0
        total_all_tax = 0
        total_refund = 0
        currency_id = self.env['res.currency'].search([('name', '=', 'IDR')], limit=1)
        # sale_order_ids = self.env['sale.order'].sudo().search([('state', 'in', ['sale', 'done']), ('date_order', '>=', start_date), ('date_order', '<=', end_date)], order='date_order asc')

        if partner_id and is_pasien==True:
            self._cr.execute("""(
                   select a.id 
                   from account_move a
                       left join sale_order b on b.name = a.invoice_origin 
                   where a.state in ('draft', 'approval','posted') 
                       and date(a.invoice_date) >= '{_start_date}'
                       and date(a.invoice_date) <= '{_end_date}'
                       and a.move_type = 'out_invoice' 
                       and a.source_document is not Null
                       and b.is_pasien = True
                       and a.partner_id = {_partner_id}
                       order by date(a.invoice_date) asc
               )""".format(_start_date=str(start_date), _end_date=str(end_date), _partner_id=partner_id))
            move_id = self._cr.fetchall()
            sale_order_ids = self.env['account.move'].sudo().search([('id', 'in', move_id)], order='invoice_date asc')
            credit_note_ids = self.env['account.move'].sudo().search([('reversed_entry_id', 'in', move_id)])
        elif partner_id and is_pasien==False:
            self._cr.execute("""(
                   select a.id 
                   from account_move a
                       left join sale_order b on b.name = a.invoice_origin 
                   where a.state in ('draft', 'approval', 'posted')  
                       and date(a.invoice_date) >= '{_start_date}'
                       and date(a.invoice_date) <= '{_end_date}'
                       and a.move_type = 'out_invoice' 
                       and a.source_document is not Null
                       and b.is_pasien is not True
                       and a.partner_id = {_partner_id}
                       order by date(a.invoice_date) asc
               )""".format(_start_date=str(start_date), _end_date=str(end_date),_partner_id=partner_id))
            move_id = self._cr.fetchall()
            sale_order_ids = self.env['account.move'].sudo().search([('id', 'in', move_id)], order='invoice_date asc')
            credit_note_ids = self.env['account.move'].sudo().search([('reversed_entry_id', 'in', move_id)])
        elif not partner_id and is_pasien==True:
            self._cr.execute("""(
                select a.id 
                from account_move a
                    left join sale_order b on b.name = a.invoice_origin 
                where a.state in ('draft', 'approval', 'posted') 
                    and date(a.invoice_date) >= '{_start_date}'
                    and date(a.invoice_date) <= '{_end_date}'
                    and a.move_type = 'out_invoice' 
                    and a.source_document is not Null
                    and b.is_pasien = True
                    order by date(a.invoice_date) asc
            )""".format(_start_date=str(start_date),_end_date=str(end_date)))
            move_id = self._cr.fetchall()
            sale_order_ids = self.env['account.move'].sudo().search([('id', 'in', move_id)], order='invoice_date asc')
            credit_note_ids = self.env['account.move'].sudo().search([('reversed_entry_id', 'in', move_id)])
        elif not partner_id and is_pasien == False:
            self._cr.execute("""(
                            select a.id 
                            from account_move a
                                left join sale_order b on b.name = a.invoice_origin 
                            where a.state in ('draft', 'approval','posted') 
                                and date(a.invoice_date) >= '{_start_date}'
                                and date(a.invoice_date) <= '{_end_date}'
                                and a.move_type = 'out_invoice' 
                                and a.source_document is not Null
                                and b.is_pasien is not True
                                order by date(a.invoice_date) asc
                        )""".format(_start_date=str(start_date), _end_date=str(end_date)))
            move_id = self._cr.fetchall()
            sale_order_ids = self.env['account.move'].sudo().search([('id', 'in', move_id)], order='invoice_date asc')
            credit_note_ids = self.env['account.move'].sudo().search([('reversed_entry_id', 'in', move_id)])
        for order in sale_order_ids:
            if order.partner_id.id not in list_partner:
                list_partner.append(order.partner_id.id)
                data_all[order.partner_id.id] = {
                    'code': order.partner_id.code_customer,
                    'name': order.partner_id.name,
                    'is_pasien': order.is_pasien,
                    'pasien': order.pasien.name,
                    'penjualan': 0.0,
                    'pajak': 0.0,
                    'total': 0.0,
                    'debit': 0.0,
                    'retur': 0.0,
                    'retur_pajak': 0.0,
                    'refund': 0.0,
                    'currency_id': order.currency_id
                }
            if order.total_all_tax >= 0:
                total_all_tax = order.total_all_tax
            elif order.total_all_tax < 0:
                total_all_tax = order.total_all_tax
            data_all[order.partner_id.id]['penjualan'] += (order.amount_untaxed - order.global_order_discount)
            data_all[order.partner_id.id]['pajak'] += total_all_tax
            data_all[order.partner_id.id]['debit'] += ((order.amount_untaxed-order.global_order_discount)+total_all_tax)
            total_penjualan_all += (order.amount_untaxed - order.global_order_discount)
            total_pajak_all += total_all_tax
            total_debit_all += ((order.amount_untaxed-order.global_order_discount)+total_all_tax)

        # # credit_note_ids = self.env['account.move'].sudo().search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'), ('invoice_date', '>=', start_date), ('invoice_date', '<=', end_date)])
        # if partner_id and is_pasien == True:
        #     # credit_note_ids = self.env['account.move'].sudo().search([('move_type', '=', 'out_refund'), ('state', '=', 'posted'), ('invoice_date', '>=', start_date), ('invoice_date', '<=', end_date), ('partner_id', '=', partner_id)])
        #     self._cr.execute("""(
        #            select a.id
        #            from account_move a
        #                join sale_order b on b.name = a.invoice_origin
        #            where a.state in ('draft', 'posted')
        #                and date(a.invoice_date) >= '{_start_date}'
        #                and date(a.invoice_date) <= '{_end_date}'
        #                and a.move_type = 'out_refund'
        #                and b.is_pasien = True
        #                and a.partner_id = {_partner_id}
        #        )""".format(_start_date=str(start_date), _end_date=str(end_date), _partner_id=partner_id))
        #     move_id = self._cr.fetchall()
        #     credit_note_ids = self.env['account.move'].sudo().search([('id', 'in', move_id)])
        # elif partner_id and is_pasien == False:
        #     self._cr.execute("""(
        #           select a.id
        #           from account_move a
        #               join sale_order b on b.name = a.invoice_origin
        #           where a.state in ('draft', 'posted')
        #               and date(a.invoice_date) >= '{_start_date}'
        #               and date(a.invoice_date) <= '{_end_date}'
        #               and a.move_type = 'out_refund'
        #               and b.is_pasien = False
        #               and a.partner_id = {_partner_id}
        #       )""".format(_start_date=str(start_date), _end_date=str(end_date), _partner_id=partner_id))
        #     move_id = self._cr.fetchall()
        #     credit_note_ids = self.env['account.move'].sudo().search([('id', 'in', move_id)])
        # elif not partner_id and is_pasien == False:
        #     self._cr.execute("""(
        #           select a.id
        #           from account_move a
        #               join sale_order b on b.name = a.invoice_origin
        #           where a.state in ('draft', 'posted')
        #               and date(a.invoice_date) >= '{_start_date}'
        #               and date(a.invoice_date) <= '{_end_date}'
        #               and a.move_type = 'out_refund'
        #               and b.is_pasien = False
        #       )""".format(_start_date=str(start_date), _end_date=str(end_date)))
        #     move_id = self._cr.fetchall()
        #     credit_note_ids = self.env['account.move'].sudo().search([('id', 'in', move_id)])
        # elif not partner_id and is_pasien == True:
        #     self._cr.execute("""(
        #           select a.id
        #           from account_move a
        #               join sale_order b on b.name = a.invoice_origin
        #           where a.state in ('draft', 'posted')
        #               and date(a.invoice_date) >= '{_start_date}'
        #               and date(a.invoice_date) <= '{_end_date}'
        #               and a.move_type = 'out_refund'
        #               and b.is_pasien = True
        #       )""".format(_start_date=str(start_date), _end_date=str(end_date)))
        #     move_id = self._cr.fetchall()
        #     credit_note_ids = self.env['account.move'].sudo().search([('id', 'in', move_id)])
        for cn in credit_note_ids:
            if cn.partner_id.id not in list_partner:
                list_partner.append(cn.partner_id.id)
                data_all[cn.partner_id.id] = {
                    'code': cn.partner_id.code_customer,
                    'name': cn.partner_id.name,
                    'is_pasien': cn.is_pasien,
                    'pasien': cn.pasien.name,
                    'penjualan': 0.0,
                    'pajak': 0.0,
                    'total': 0.0,
                    'debit': 0.0,
                    'retur': 0.0,
                    'retur_pajak': 0.0,
                    'refund': 0.0,
                    'currency_id': cn.currency_id
                }
            data_all[cn.partner_id.id]['retur'] += cn.amount_untaxed
            data_all[cn.partner_id.id]['retur_pajak'] += cn.total_all_tax
            data_all[cn.partner_id.id]['refund'] += (cn.amount_untaxed + cn.total_all_tax)
            total_retur += cn.amount_untaxed
            total_retur_pajak += cn.total_all_tax
            total_refund += (cn.amount_untaxed + cn.total_all_tax)

        result = {
            # 'doc_ids': data['ids'],
            # 'doc_model': data['model'],
            'start_date': start_date,
            'end_date': end_date,
            'is_pasien': is_pasien,
            'docs': docs,
            'data_all': data_all,
            'list_partner': list_partner,
            'total_penjualan_all': total_penjualan_all,
            'total_pajak_all': total_pajak_all,
            'total_retur': total_retur,
            'total_retur_pajak': total_retur_pajak,
            'total_refund': total_refund,
            'total_debit_all': total_debit_all
        }
        return result

