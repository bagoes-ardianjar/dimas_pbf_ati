from odoo import models, fields, api, exceptions, _

from datetime import datetime

header_title = ['Nomor Ref', 'Tanggal', 'Kode PLU', 'Nama Barang', 'Qty','Customer','Sales Person', 'Batch/S.N/IMEI', 'Exp. Date', 'Satuan', 'Harga Jual', 'Jumlah Diskon Per Line','Global Diskon', 'Jumlah Penjualan Inc PPN']
 
class x_report_penjualan_so(models.TransientModel):
    _name = 'x.report.penjualan.so'
 
 
    # so_id = fields.Many2many('sale.order', string='Sale Order')
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    company_id = fields.Many2one('res.company', 'Company')
    product_id = fields.Many2one('product.product', 'Product')
    partner_id = fields.Many2one('res.partner', 'Customer')
    sales_person = fields.Many2one('hr.employee', string='Sales Person')
 
 
    def action_print_report(self):
        data = {'start_date': self.start_date, 'end_date': self.end_date, 'company_id':self.company_id.id, 'product_id':self.product_id.id, 'partner_id':self.partner_id.id,'sales_person':self.sales_person.id}
        if self.product_id.id == False and self.partner_id.id == False and self.sales_person.id == False:
            return self.env.ref('ati_report_sale.action_report_so_peritem').report_action(self, data=data)
        else:
            return self.env.ref('ati_report_sale.action_report_so_peritem').report_action(self, data=data)

    def action_print_report_xlsx(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'x.report.penjualan.so'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        return self.env.ref('ati_report_sale.action_report_so_peritem_xlsx').report_action(self, data=datas)

class x_report_penjualan_so_pdf(models.AbstractModel):
    _name = 'report.ati_report_sale.so_peritem_pdf_template'

    def _get_report_values(self, docids, data=None):
        domain = [('state', '=', 'sale')]
        if data.get('start_date'):
            domain.append(('create_date', '>=', data.get('start_date')))
        if data.get('end_date'):
            domain.append(('create_date', '<=', data.get('end_date')))
        if data.get('company_id'):
            domain.append(('company_id', '=', data.get('company_id')))
        if data.get('product_id'):
            domain.append(('product_id', '=', data.get('product_id')))
        if data.get('partner_id'):
            domain.append(('partner_id', '=', data.get('partner_id')))
        if data.get('sales_person'):
            domain.append(('sales_person', '=', data.get('sales_person')))

        start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()


        if data.get('product_id') == False and data.get('partner_id') == False and data.get('sales_person') == False:

            self._cr.execute("""(
                        select
                            a.id as sml_id,
                            d.name as sales_reference,
                            date(g.invoice_date) as tanggal,
                            i.sku as kode_plu,
                            i.name as product_name,
                            a.qty_done as qty_done,
                            (select name from res_partner where id= d.partner_id) as customer,
                            (select name from hr_employee where id = d.sales_person) as sales_person,
                            (select name from stock_production_lot where id = a.lot_id) as lot_name,
                            (select date(expiration_date) from stock_production_lot where id = a.lot_id) as expiration_date,
                            (select name from uom_uom where id = a.product_uom_id) as uom,
                            coalesce(c.discount_amount,0) as diskon,
                            coalesce(f.harga_satuan,0) as harga_satuan,
                            case
                                when (select count(z.id) from stock_move_line z where z.picking_id = j.id) > 0 and c.price_unit > 0 then coalesce(d.global_discount/(select count(z.id) from stock_move_line z where z.picking_id = j.id),0)
                                else 0
                            end as global_diskon_perline,
                            coalesce(l.amount,0) as tax
                        from stock_move_line a
                            join stock_move b on b.id = a.move_id
                            join sale_order_line c on c.id = b.sale_line_id
                            join sale_order d on d.id = c.order_id
                            join sale_order_line_invoice_rel e on e.order_line_id = c.id
                            join account_move_line f on f.id = e.invoice_line_id
                            join account_move g on g.id = f.move_id
                            join product_product h on h.id = a.product_id
                            join product_template i on i.id = h.product_tmpl_id
                            join stock_picking j on a.picking_id = j.id
                            left join account_tax_sale_order_line_rel k on k.sale_order_line_id = c.id
                            left join account_tax l on l.id = k.account_tax_id
                        where date(g.invoice_date) >= '{_start_date}'
                            and date(g.invoice_date) <= '{_end_date}'
                            and g.company_id = {_company_id}
                            and g.state in ('draft','approval','posted')
                            and g.move_type = 'out_invoice'
                            and j.picking_type_id_name = 'Delivery Orders'
                            and j.state = 'done'
                            and g.source_document is not null
                        )""".format(_start_date=str(data.get('start_date')),
                                    _end_date=str(data.get('end_date')), _company_id=data.get('company_id')))

            res_penjualan = self._cr.dictfetchall()

            if data.get('company_id'):
                domain_c = [('id', '=', data.get('company_id'))]
                company_obj = self.env['res.company'].search(domain_c)

            # if res_penjualan :
            data = []
            amoun_untaxed = 0
            amount_tax = 0
            total_qty = 0
            total_penjualan = 0
            docs = data
            for rec in res_penjualan:
                sml_id = rec.get('sml_id')
                sml = self.env['stock.move.line'].sudo().search([('id', '=', sml_id)])
                tanggal = rec.get('tanggal').strftime('%Y-%m-%d') if rec.get('tanggal') else '-'
                if rec.get('harga_satuan') > 0:
                    amount_untaxed = ((rec.get('harga_satuan') - rec.get('diskon')) * rec.get('qty_done')) - rec.get(
                        'global_diskon_perline')
                else:
                    amount_untaxed = 0
                if rec.get('tax') > 0:
                    # amount_tax = amount_untaxed * rec.get('tax') / 100
                    amount_tax = rec.get('tax')
                else:
                    amount_tax = 0
                # jumlah_penjualan = amount_untaxed + amount_tax
                jumlah_penjualan = sml.price_subtotal - sml.global_diskon_line + sml.total_tax
                expiration_date = rec.get('expiration_date').strftime('%Y-%m-%d') if rec.get('expiration_date') else '-'
                data.append({
                    'sales_reference': rec.get('sales_reference'),
                    'tanggal': tanggal,
                    'kode_plu': rec.get('kode_plu'),
                    'product_name': rec.get('product_name'),
                    'qty_done': rec.get('qty_done'),
                    'customer': rec.get('customer'),
                    'sales_person': rec.get('sales_person'),
                    'lot_name': rec.get('lot_name'),
                    'expiration_date': expiration_date,
                    'uom': rec.get('uom'),
                    'harga_satuan': rec.get('harga_satuan'),
                    'diskon': rec.get('diskon'),
                    'global_diskon_perline': sml.global_diskon_line,
                    'jumlah_penjualan': jumlah_penjualan
                })

                total_qty += rec.get('qty_done')
                total_penjualan += jumlah_penjualan
            if data:
                docs = data

            result = {
                'start_date': start_date,
                'end_date': end_date,
                'docs': docs,
                'cmp': company_obj,
                'total_qty': total_qty,
                'total_penjualan': total_penjualan
            }
            return result

        elif data.get('product_id') != False and data.get('partner_id') != False and data.get('sales_person') != False:
            self._cr.execute("""(
                        select
                            a.id as sml_id,
                            d.name as sales_reference,
                            date(g.invoice_date) as tanggal,
                            i.sku as kode_plu,
                            i.name as product_name,
                            a.qty_done as qty_done,
                            (select name from res_partner where id= d.partner_id) as customer,
                            (select name from hr_employee where id = d.sales_person) as sales_person,
                            (select name from stock_production_lot where id = a.lot_id) as lot_name,
                            (select date(expiration_date) from stock_production_lot where id = a.lot_id) as expiration_date,
                            (select name from uom_uom where id = a.product_uom_id) as uom,
                            coalesce(c.discount_amount,0) as diskon,
                            coalesce(f.harga_satuan,0) as harga_satuan,
                            case
                                when (select count(z.id) from stock_move_line z where z.picking_id = j.id) > 0 and c.price_unit > 0 then coalesce(d.global_discount/(select count(z.id) from stock_move_line z where z.picking_id = j.id),0)
                                else 0
                            end as global_diskon_perline,
                            coalesce(l.amount,0) as tax
                        from stock_move_line a
                            join stock_move b on b.id = a.move_id
                            join sale_order_line c on c.id = b.sale_line_id
                            join sale_order d on d.id = c.order_id
                            join sale_order_line_invoice_rel e on e.order_line_id = c.id
                            join account_move_line f on f.id = e.invoice_line_id
                            join account_move g on g.id = f.move_id
                            join product_product h on h.id = a.product_id
                            join product_template i on i.id = h.product_tmpl_id
                            join stock_picking j on a.picking_id = j.id
                            left join account_tax_sale_order_line_rel k on k.sale_order_line_id = c.id
                            left join account_tax l on l.id = k.account_tax_id
                        where date(g.invoice_date) >= '{_start_date}'
                            and date(g.invoice_date) <= '{_end_date}'
                            and g.company_id = {_company_id}
                            and g.state in ('draft','approval','posted')
                            and a.product_id = {_product_id}
                            and d.sales_person = {_sales_person}
                            and d.partner_id = {_partner_id}
                            and g.move_type = 'out_invoice'
                            and j.picking_type_id_name = 'Delivery Orders'
                            and j.state = 'done'
                            and g.source_document is not null
                        )""".format(_sales_person=data.get('sales_person'),_start_date=str(data.get('start_date')),
                                    _end_date=str(data.get('end_date')),_product_id=data.get('product_id'),
                                    _partner_id=data.get('partner_id'),_company_id=data.get('company_id')))

            res_penjualan = self._cr.dictfetchall()

            if data.get('company_id'):
                domain_c = [('id', '=', data.get('company_id'))]
                company_obj = self.env['res.company'].search(domain_c)

            # if res_penjualan :
            data = []
            amoun_untaxed = 0
            amount_tax = 0
            total_qty = 0
            total_penjualan = 0
            docs = data
            for rec in res_penjualan:
                sml_id = rec.get('sml_id')
                sml = self.env['stock.move.line'].sudo().search([('id', '=', sml_id)])
                tanggal = rec.get('tanggal').strftime('%Y-%m-%d') if rec.get('tanggal') else '-'
                if rec.get('harga_satuan') > 0:
                    amount_untaxed = ((rec.get('harga_satuan') - rec.get('diskon')) * rec.get('qty_done')) - rec.get(
                        'global_diskon_perline')
                else:
                    amount_untaxed = 0
                if rec.get('tax') > 0:
                    # amount_tax = amount_untaxed * rec.get('tax') / 100
                    amount_tax = rec.get('tax')
                else:
                    amount_tax = 0
                # jumlah_penjualan = amount_untaxed + amount_tax
                jumlah_penjualan = sml.price_subtotal - sml.global_diskon_line + sml.total_tax
                expiration_date = rec.get('expiration_date').strftime('%Y-%m-%d') if rec.get('expiration_date') else '-'
                data.append({
                    'sales_reference': rec.get('sales_reference'),
                    'tanggal': tanggal,
                    'kode_plu': rec.get('kode_plu'),
                    'product_name': rec.get('product_name'),
                    'qty_done': rec.get('qty_done'),
                    'customer': rec.get('customer'),
                    'sales_person': rec.get('sales_person'),
                    'lot_name': rec.get('lot_name'),
                    'expiration_date': expiration_date,
                    'uom': rec.get('uom'),
                    'harga_satuan': rec.get('harga_satuan'),
                    'diskon': rec.get('diskon'),
                    'global_diskon_perline': sml.global_diskon_line,
                    'jumlah_penjualan': jumlah_penjualan
                })

                total_qty += rec.get('qty_done')
                total_penjualan += jumlah_penjualan
            if data:
                docs = data

            result = {
                'start_date': start_date,
                'end_date': end_date,
                'docs': docs,
                'cmp': company_obj,
                'total_qty': total_qty,
                'total_penjualan': total_penjualan
            }
            return result
        elif data.get('product_id') != False and data.get('partner_id') == False and data.get('sales_person') == False:

            self._cr.execute("""(
                select
                            a.id as sml_id,
                            d.name as sales_reference,
                            date(g.invoice_date) as tanggal,
                            i.sku as kode_plu,
                            i.name as product_name,
                            a.qty_done as qty_done,
                            (select name from res_partner where id= d.partner_id) as customer,
                            (select name from hr_employee where id = d.sales_person) as sales_person,
                            (select name from stock_production_lot where id = a.lot_id) as lot_name,
                            (select date(expiration_date) from stock_production_lot where id = a.lot_id) as expiration_date,
                            (select name from uom_uom where id = a.product_uom_id) as uom,
                            coalesce(c.discount_amount,0) as diskon,
                            coalesce(f.harga_satuan,0) as harga_satuan,
                            case
                                when (select count(z.id) from stock_move_line z where z.picking_id = j.id) > 0 and c.price_unit > 0 then coalesce(d.global_discount/(select count(z.id) from stock_move_line z where z.picking_id = j.id),0)
                                else 0
                            end as global_diskon_perline,
                            coalesce(l.amount,0) as tax
                        from stock_move_line a
                            join stock_move b on b.id = a.move_id
                            join sale_order_line c on c.id = b.sale_line_id
                            join sale_order d on d.id = c.order_id
                            join sale_order_line_invoice_rel e on e.order_line_id = c.id
                            join account_move_line f on f.id = e.invoice_line_id
                            join account_move g on g.id = f.move_id
                            join product_product h on h.id = a.product_id
                            join product_template i on i.id = h.product_tmpl_id
                            join stock_picking j on a.picking_id = j.id
                            left join account_tax_sale_order_line_rel k on k.sale_order_line_id = c.id
                            left join account_tax l on l.id = k.account_tax_id
                        where date(g.invoice_date) >= '{_start_date}'
                            and date(g.invoice_date) <= '{_end_date}'
                            and g.company_id = {_company_id}
                            and g.state in ('draft','approval','posted')
                            and a.product_id = {_product_id}
                            and g.move_type = 'out_invoice'
                            and j.picking_type_id_name = 'Delivery Orders'
                            and j.state = 'done'
                            and g.source_document is not null
                )""".format(_start_date=str(data.get('start_date')),_end_date=str(data.get('end_date')),
                            _product_id=data.get('product_id'),_company_id=data.get('company_id')))
            res_penjualan = self._cr.dictfetchall()

            if data.get('company_id'):
                domain_c = [('id', '=', data.get('company_id'))]
                company_obj = self.env['res.company'].search(domain_c)

            # if res_penjualan :
            data = []
            amoun_untaxed = 0
            amount_tax = 0
            total_qty = 0
            total_penjualan = 0
            docs = data
            for rec in res_penjualan:
                sml_id = rec.get('sml_id')
                sml = self.env['stock.move.line'].sudo().search([('id', '=', sml_id)])
                tanggal = rec.get('tanggal').strftime('%Y-%m-%d') if rec.get('tanggal') else '-'
                if rec.get('harga_satuan') > 0:
                    amount_untaxed = ((rec.get('harga_satuan') - rec.get('diskon')) * rec.get('qty_done')) - rec.get(
                        'global_diskon_perline')
                else:
                    amount_untaxed = 0
                if rec.get('tax') > 0:
                    # amount_tax = amount_untaxed * rec.get('tax') / 100
                    amount_tax = rec.get('tax')
                else:
                    amount_tax = 0
                # jumlah_penjualan = amount_untaxed + amount_tax
                jumlah_penjualan = sml.price_subtotal - sml.global_diskon_line + sml.total_tax
                expiration_date = rec.get('expiration_date').strftime('%Y-%m-%d') if rec.get('expiration_date') else '-'
                data.append({
                    'sales_reference': rec.get('sales_reference'),
                    'tanggal': tanggal,
                    'kode_plu': rec.get('kode_plu'),
                    'product_name': rec.get('product_name'),
                    'qty_done': rec.get('qty_done'),
                    'customer': rec.get('customer'),
                    'sales_person': rec.get('sales_person'),
                    'lot_name': rec.get('lot_name'),
                    'expiration_date': expiration_date,
                    'uom': rec.get('uom'),
                    'harga_satuan': rec.get('harga_satuan'),
                    'diskon': rec.get('diskon'),
                    'global_diskon_perline': sml.global_diskon_line,
                    'jumlah_penjualan': jumlah_penjualan
                })

                total_qty += rec.get('qty_done')
                total_penjualan += jumlah_penjualan
            if data:
                docs = data

            result = {
                'start_date': start_date,
                'end_date': end_date,
                'docs': docs,
                'cmp': company_obj,
                'total_qty': total_qty,
                'total_penjualan': total_penjualan
            }
            return result
        if data.get('product_id') != False and data.get('partner_id') != False and data.get('sales_person') == False:
            self._cr.execute("""(
                select
                    a.id as sml_id,
                    d.name as sales_reference,
                    date(g.invoice_date) as tanggal,
                    i.sku as kode_plu,
                    i.name as product_name,
                    a.qty_done as qty_done,
                    (select name from res_partner where id= d.partner_id) as customer,
                    (select name from hr_employee where id = d.sales_person) as sales_person,
                    (select name from stock_production_lot where id = a.lot_id) as lot_name,
                    (select date(expiration_date) from stock_production_lot where id = a.lot_id) as expiration_date,
                    (select name from uom_uom where id = a.product_uom_id) as uom,
                    coalesce(c.discount_amount,0) as diskon,
                    coalesce(f.harga_satuan,0) as harga_satuan,
                    case
                        when (select count(z.id) from stock_move_line z where z.picking_id = j.id) > 0 and c.price_unit > 0 then coalesce(d.global_discount/(select count(z.id) from stock_move_line z where z.picking_id = j.id),0)
                        else 0
                    end as global_diskon_perline,
                    coalesce(l.amount,0) as tax
                from stock_move_line a
                    join stock_move b on b.id = a.move_id
                    join sale_order_line c on c.id = b.sale_line_id
                    join sale_order d on d.id = c.order_id
                    join sale_order_line_invoice_rel e on e.order_line_id = c.id
                    join account_move_line f on f.id = e.invoice_line_id
                    join account_move g on g.id = f.move_id
                    join product_product h on h.id = a.product_id
                    join product_template i on i.id = h.product_tmpl_id
                    join stock_picking j on a.picking_id = j.id
                    left join account_tax_sale_order_line_rel k on k.sale_order_line_id = c.id
                    left join account_tax l on l.id = k.account_tax_id
                where date(g.invoice_date) >= '{_start_date}'
                    and date(g.invoice_date) <= '{_end_date}'
                    and g.company_id = {_company_id}
                    and g.state in ('draft','approval','posted')
                    and a.product_id = {_product_id}
                    and d.partner_id = {_partner_id}
                    and g.move_type = 'out_invoice'
                    and j.picking_type_id_name = 'Delivery Orders'
                    and j.state = 'done'
                    and g.source_document is not null
                )""".format(_start_date=str(data.get('start_date')),_end_date=str(data.get('end_date')),
                            _product_id=data.get('product_id'),_partner_id=data.get('partner_id'),
                            _company_id=data.get('company_id')))
            res_penjualan = self._cr.dictfetchall()

            if data.get('company_id'):
                domain_c = [('id', '=', data.get('company_id'))]
                company_obj = self.env['res.company'].search(domain_c)

            # if res_penjualan :
            data = []
            amoun_untaxed = 0
            amount_tax = 0
            total_qty = 0
            total_penjualan = 0
            docs = data
            for rec in res_penjualan:
                sml_id = rec.get('sml_id')
                sml = self.env['stock.move.line'].sudo().search([('id', '=', sml_id)])
                tanggal = rec.get('tanggal').strftime('%Y-%m-%d') if rec.get('tanggal') else '-'
                if rec.get('harga_satuan') > 0:
                    amount_untaxed = ((rec.get('harga_satuan') - rec.get('diskon')) * rec.get('qty_done')) - rec.get(
                        'global_diskon_perline')
                else:
                    amount_untaxed = 0
                if rec.get('tax') > 0:
                    # amount_tax = amount_untaxed * rec.get('tax') / 100
                    amount_tax = rec.get('tax')
                else:
                    amount_tax = 0
                # jumlah_penjualan = amount_untaxed + amount_tax
                jumlah_penjualan = sml.price_subtotal - sml.global_diskon_line + sml.total_tax
                expiration_date = rec.get('expiration_date').strftime('%Y-%m-%d') if rec.get('expiration_date') else '-'
                data.append({
                    'sales_reference': rec.get('sales_reference'),
                    'tanggal': tanggal,
                    'kode_plu': rec.get('kode_plu'),
                    'product_name': rec.get('product_name'),
                    'qty_done': rec.get('qty_done'),
                    'customer': rec.get('customer'),
                    'sales_person': rec.get('sales_person'),
                    'lot_name': rec.get('lot_name'),
                    'expiration_date': expiration_date,
                    'uom': rec.get('uom'),
                    'harga_satuan': rec.get('harga_satuan'),
                    'diskon': rec.get('diskon'),
                    'global_diskon_perline': sml.global_diskon_line,
                    'jumlah_penjualan': jumlah_penjualan
                })

                total_qty += rec.get('qty_done')
                total_penjualan += jumlah_penjualan
            if data:
                docs = data

            result = {
                'start_date': start_date,
                'end_date': end_date,
                'docs': docs,
                'cmp': company_obj,
                'total_qty': total_qty,
                'total_penjualan': total_penjualan
            }
            return result

        if data.get('product_id') != False and data.get('partner_id') == False and data.get('sales_person') != False:
            self._cr.execute("""(
                 select
                    a.id as sml_id,
                    d.name as sales_reference,
                    date(g.invoice_date) as tanggal,
                    i.sku as kode_plu,
                    i.name as product_name,
                    a.qty_done as qty_done,
                    (select name from res_partner where id= d.partner_id) as customer,
                    (select name from hr_employee where id = d.sales_person) as sales_person,
                    (select name from stock_production_lot where id = a.lot_id) as lot_name,
                    (select date(expiration_date) from stock_production_lot where id = a.lot_id) as expiration_date,
                    (select name from uom_uom where id = a.product_uom_id) as uom,
                    coalesce(c.discount_amount,0) as diskon,
                    coalesce(f.harga_satuan,0) as harga_satuan,
                    case
                        when (select count(z.id) from stock_move_line z where z.picking_id = j.id) > 0 and c.price_unit > 0 then coalesce(d.global_discount/(select count(z.id) from stock_move_line z where z.picking_id = j.id),0)
                        else 0
                    end as global_diskon_perline,
                    coalesce(l.amount,0) as tax
                from stock_move_line a
                    join stock_move b on b.id = a.move_id
                    join sale_order_line c on c.id = b.sale_line_id
                    join sale_order d on d.id = c.order_id
                    join sale_order_line_invoice_rel e on e.order_line_id = c.id
                    join account_move_line f on f.id = e.invoice_line_id
                    join account_move g on g.id = f.move_id
                    join product_product h on h.id = a.product_id
                    join product_template i on i.id = h.product_tmpl_id
                    join stock_picking j on a.picking_id = j.id
                    left join account_tax_sale_order_line_rel k on k.sale_order_line_id = c.id
                    left join account_tax l on l.id = k.account_tax_id
                where date(g.invoice_date) >= '{_start_date}'
                    and date(g.invoice_date) <= '{_end_date}'
                    and g.company_id = {_company_id}
                    and g.state in ('draft','approval','posted')
                    and a.product_id = {_product_id}
                    and d.sales_person = {_sales_person}
                    and g.move_type = 'out_invoice'
                    and j.picking_type_id_name = 'Delivery Orders'
                    and j.state = 'done'
                    and g.source_document is not null
                )""".format(_sales_person=data.get('sales_person'),_start_date=str(data.get('start_date')),
                            _end_date=str(data.get('end_date')),_product_id=data.get('product_id'),
                            _company_id=data.get('company_id')))
            res_penjualan = self._cr.dictfetchall()

            if data.get('company_id'):
                domain_c = [('id', '=', data.get('company_id'))]
                company_obj = self.env['res.company'].search(domain_c)

            # if res_penjualan :
            data = []
            amoun_untaxed = 0
            amount_tax = 0
            total_qty = 0
            total_penjualan = 0
            docs = data
            for rec in res_penjualan:
                sml_id = rec.get('sml_id')
                sml = self.env['stock.move.line'].sudo().search([('id', '=', sml_id)])
                tanggal = rec.get('tanggal').strftime('%Y-%m-%d') if rec.get('tanggal') else '-'
                if rec.get('harga_satuan') > 0:
                    amount_untaxed = ((rec.get('harga_satuan') - rec.get('diskon')) * rec.get('qty_done')) - rec.get(
                        'global_diskon_perline')
                else:
                    amount_untaxed = 0
                if rec.get('tax') > 0:
                    # amount_tax = amount_untaxed * rec.get('tax') / 100
                    amount_tax = rec.get('tax')
                else:
                    amount_tax = 0
                # jumlah_penjualan = amount_untaxed + amount_tax
                jumlah_penjualan = sml.price_subtotal - sml.global_diskon_line + sml.total_tax
                expiration_date = rec.get('expiration_date').strftime('%Y-%m-%d') if rec.get('expiration_date') else '-'
                data.append({
                    'sales_reference': rec.get('sales_reference'),
                    'tanggal': tanggal,
                    'kode_plu': rec.get('kode_plu'),
                    'product_name': rec.get('product_name'),
                    'qty_done': rec.get('qty_done'),
                    'customer': rec.get('customer'),
                    'sales_person': rec.get('sales_person'),
                    'lot_name': rec.get('lot_name'),
                    'expiration_date': expiration_date,
                    'uom': rec.get('uom'),
                    'harga_satuan': rec.get('harga_satuan'),
                    'diskon': rec.get('diskon'),
                    'global_diskon_perline': sml.global_diskon_line,
                    'jumlah_penjualan': jumlah_penjualan
                })

                total_qty += rec.get('qty_done')
                total_penjualan += jumlah_penjualan
            if data:
                docs = data

            result = {
                'start_date': start_date,
                'end_date': end_date,
                'docs': docs,
                'cmp': company_obj,
                'total_qty': total_qty,
                'total_penjualan': total_penjualan
            }
            return result

        elif data.get('product_id') == False and data.get('partner_id') != False and data.get('sales_person') != False:
            self._cr.execute("""(
                         select
                            a.id as sml_id,
                            d.name as sales_reference,
                            date(g.invoice_date) as tanggal,
                            i.sku as kode_plu,
                            i.name as product_name,
                            a.qty_done as qty_done,
                            (select name from res_partner where id= d.partner_id) as customer,
                            (select name from hr_employee where id = d.sales_person) as sales_person,
                            (select name from stock_production_lot where id = a.lot_id) as lot_name,
                            (select date(expiration_date) from stock_production_lot where id = a.lot_id) as expiration_date,
                            (select name from uom_uom where id = a.product_uom_id) as uom,
                            coalesce(c.discount_amount,0) as diskon,
                            coalesce(f.harga_satuan,0) as harga_satuan,
                            case
                                when (select count(z.id) from stock_move_line z where z.picking_id = j.id) > 0 and c.price_unit > 0 then coalesce(d.global_discount/(select count(z.id) from stock_move_line z where z.picking_id = j.id),0)
                                else 0
                            end as global_diskon_perline,
                            coalesce(l.amount,0) as tax
                        from stock_move_line a
                            join stock_move b on b.id = a.move_id
                            join sale_order_line c on c.id = b.sale_line_id
                            join sale_order d on d.id = c.order_id
                            join sale_order_line_invoice_rel e on e.order_line_id = c.id
                            join account_move_line f on f.id = e.invoice_line_id
                            join account_move g on g.id = f.move_id
                            join product_product h on h.id = a.product_id
                            join product_template i on i.id = h.product_tmpl_id
                            join stock_picking j on a.picking_id = j.id
                            left join account_tax_sale_order_line_rel k on k.sale_order_line_id = c.id
                            left join account_tax l on l.id = k.account_tax_id
                        where date(g.invoice_date) >= '{_start_date}'
                            and date(g.invoice_date) <= '{_end_date}'
                            and g.company_id = {_company_id}
                            and g.state in ('draft','approval','posted')
                            and d.sales_person = {_sales_person}
                            and d.partner_id = {_partner_id}
                            and g.move_type = 'out_invoice'
                            and j.picking_type_id_name = 'Delivery Orders'
                            and j.state = 'done'
                            and g.source_document is not null
                        )""".format(_sales_person=data.get('sales_person'), _start_date=str(data.get('start_date')),
                                    _end_date=str(data.get('end_date')),
                                    _partner_id=data.get('partner_id'), _company_id=data.get('company_id')))
            res_penjualan = self._cr.dictfetchall()

            if data.get('company_id'):
                domain_c = [('id', '=', data.get('company_id'))]
                company_obj = self.env['res.company'].search(domain_c)

            # if res_penjualan :
            data = []
            amoun_untaxed = 0
            amount_tax = 0
            total_qty = 0
            total_penjualan = 0
            docs = data
            for rec in res_penjualan:
                sml_id = rec.get('sml_id')
                sml = self.env['stock.move.line'].sudo().search([('id', '=', sml_id)])
                tanggal = rec.get('tanggal').strftime('%Y-%m-%d') if rec.get('tanggal') else '-'
                if rec.get('harga_satuan') > 0:
                    amount_untaxed = ((rec.get('harga_satuan') - rec.get('diskon')) * rec.get('qty_done')) - rec.get(
                        'global_diskon_perline')
                else:
                    amount_untaxed = 0
                if rec.get('tax') > 0:
                    # amount_tax = amount_untaxed * rec.get('tax') / 100
                    amount_tax = rec.get('tax')
                else:
                    amount_tax = 0
                # jumlah_penjualan = amount_untaxed + amount_tax
                jumlah_penjualan = sml.price_subtotal - sml.global_diskon_line + sml.total_tax
                expiration_date = rec.get('expiration_date').strftime('%Y-%m-%d') if rec.get('expiration_date') else '-'
                data.append({
                    'sales_reference': rec.get('sales_reference'),
                    'tanggal': tanggal,
                    'kode_plu': rec.get('kode_plu'),
                    'product_name': rec.get('product_name'),
                    'qty_done': rec.get('qty_done'),
                    'customer': rec.get('customer'),
                    'sales_person': rec.get('sales_person'),
                    'lot_name': rec.get('lot_name'),
                    'expiration_date': expiration_date,
                    'uom': rec.get('uom'),
                    'harga_satuan': rec.get('harga_satuan'),
                    'diskon': rec.get('diskon'),
                    'global_diskon_perline': sml.global_diskon_line,
                    'jumlah_penjualan': jumlah_penjualan
                })

                total_qty += rec.get('qty_done')
                total_penjualan += jumlah_penjualan
            if data:
                docs = data

            result = {
                'start_date': start_date,
                'end_date': end_date,
                'docs': docs,
                'cmp': company_obj,
                'total_qty': total_qty,
                'total_penjualan': total_penjualan
            }
            return result

        elif data.get('product_id') == False and data.get('partner_id') == False and data.get('sales_person') != False:
            self._cr.execute("""(
                         select
                            a.id as sml_id,
                            d.name as sales_reference,
                            date(g.invoice_date) as tanggal,
                            i.sku as kode_plu,
                            i.name as product_name,
                            a.qty_done as qty_done,
                            (select name from res_partner where id= d.partner_id) as customer,
                            (select name from hr_employee where id = d.sales_person) as sales_person,
                            (select name from stock_production_lot where id = a.lot_id) as lot_name,
                            (select date(expiration_date) from stock_production_lot where id = a.lot_id) as expiration_date,
                            (select name from uom_uom where id = a.product_uom_id) as uom,
                            coalesce(c.discount_amount,0) as diskon,
                            coalesce(f.harga_satuan,0) as harga_satuan,
                            case
                                when (select count(z.id) from stock_move_line z where z.picking_id = j.id) > 0 and c.price_unit > 0 then coalesce(d.global_discount/(select count(z.id) from stock_move_line z where z.picking_id = j.id),0)
                                else 0
                            end as global_diskon_perline,
                            coalesce(l.amount,0) as tax
                        from stock_move_line a
                            join stock_move b on b.id = a.move_id
                            join sale_order_line c on c.id = b.sale_line_id
                            join sale_order d on d.id = c.order_id
                            join sale_order_line_invoice_rel e on e.order_line_id = c.id
                            join account_move_line f on f.id = e.invoice_line_id
                            join account_move g on g.id = f.move_id
                            join product_product h on h.id = a.product_id
                            join product_template i on i.id = h.product_tmpl_id
                            join stock_picking j on a.picking_id = j.id
                            left join account_tax_sale_order_line_rel k on k.sale_order_line_id = c.id
                            left join account_tax l on l.id = k.account_tax_id
                        where date(g.invoice_date) >= '{_start_date}'
                            and date(g.invoice_date) <= '{_end_date}'
                            and g.company_id = {_company_id}
                            and g.state in ('draft','approval','posted')
                            and d.sales_person = {_sales_person}
                            and g.move_type = 'out_invoice'
                            and j.picking_type_id_name = 'Delivery Orders'
                            and j.state = 'done'
                            and g.source_document is not null
                        )""".format(_sales_person=data.get('sales_person'), _start_date=str(data.get('start_date')),
                                    _end_date=str(data.get('end_date')),_company_id=data.get('company_id')))
            res_penjualan = self._cr.dictfetchall()

            if data.get('company_id'):
                domain_c = [('id', '=', data.get('company_id'))]
                company_obj = self.env['res.company'].search(domain_c)

            # if res_penjualan :
            data = []
            amoun_untaxed = 0
            amount_tax = 0
            total_qty = 0
            total_penjualan = 0
            docs = data
            for rec in res_penjualan:
                sml_id = rec.get('sml_id')
                sml = self.env['stock.move.line'].sudo().search([('id', '=', sml_id)])
                tanggal = rec.get('tanggal').strftime('%Y-%m-%d') if rec.get('tanggal') else '-'
                if rec.get('harga_satuan') > 0:
                    amount_untaxed = ((rec.get('harga_satuan') - rec.get('diskon')) * rec.get('qty_done')) - rec.get(
                        'global_diskon_perline')
                else:
                    amount_untaxed = 0
                if rec.get('tax') > 0:
                    # amount_tax = amount_untaxed * rec.get('tax') / 100
                    amount_tax = rec.get('tax')
                else:
                    amount_tax = 0
                # jumlah_penjualan = amount_untaxed + amount_tax
                jumlah_penjualan = sml.price_subtotal - sml.global_diskon_line + sml.total_tax
                expiration_date = rec.get('expiration_date').strftime('%Y-%m-%d') if rec.get('expiration_date') else '-'
                data.append({
                    'sales_reference': rec.get('sales_reference'),
                    'tanggal': tanggal,
                    'kode_plu': rec.get('kode_plu'),
                    'product_name': rec.get('product_name'),
                    'qty_done': rec.get('qty_done'),
                    'customer': rec.get('customer'),
                    'sales_person': rec.get('sales_person'),
                    'lot_name': rec.get('lot_name'),
                    'expiration_date': expiration_date,
                    'uom': rec.get('uom'),
                    'harga_satuan': rec.get('harga_satuan'),
                    'diskon': rec.get('diskon'),
                    'global_diskon_perline': sml.global_diskon_line,
                    'jumlah_penjualan': jumlah_penjualan
                })

                total_qty += rec.get('qty_done')
                total_penjualan += jumlah_penjualan
            if data:
                docs = data

            result = {
                'start_date': start_date,
                'end_date': end_date,
                'docs': docs,
                'cmp': company_obj,
                'total_qty': total_qty,
                'total_penjualan': total_penjualan
            }
            return result
        elif data.get('product_id') == False and data.get('partner_id') != False and data.get('sales_person') == False:
            self._cr.execute("""(
                         select
                            a.id as sml_id,
                            d.name as sales_reference,
                            date(g.invoice_date) as tanggal,
                            i.sku as kode_plu,
                            i.name as product_name,
                            a.qty_done as qty_done,
                            (select name from res_partner where id= d.partner_id) as customer,
                            (select name from hr_employee where id = d.sales_person) as sales_person,
                            (select name from stock_production_lot where id = a.lot_id) as lot_name,
                            (select date(expiration_date) from stock_production_lot where id = a.lot_id) as expiration_date,
                            (select name from uom_uom where id = a.product_uom_id) as uom,
                            coalesce(c.discount_amount,0) as diskon,
                            coalesce(f.harga_satuan,0) as harga_satuan,
                            case
                                when (select count(z.id) from stock_move_line z where z.picking_id = j.id) > 0 and c.price_unit > 0 then coalesce(d.global_discount/(select count(z.id) from stock_move_line z where z.picking_id = j.id),0)
                                else 0
                            end as global_diskon_perline,
                            coalesce(l.amount,0) as tax
                        from stock_move_line a
                            join stock_move b on b.id = a.move_id
                            join sale_order_line c on c.id = b.sale_line_id
                            join sale_order d on d.id = c.order_id
                            join sale_order_line_invoice_rel e on e.order_line_id = c.id
                            join account_move_line f on f.id = e.invoice_line_id
                            join account_move g on g.id = f.move_id
                            join product_product h on h.id = a.product_id
                            join product_template i on i.id = h.product_tmpl_id
                            join stock_picking j on a.picking_id = j.id
                            left join account_tax_sale_order_line_rel k on k.sale_order_line_id = c.id
                            left join account_tax l on l.id = k.account_tax_id
                        where date(g.invoice_date) >= '{_start_date}'
                            and date(g.invoice_date) <= '{_end_date}'
                            and g.company_id = {_company_id}
                            and g.state in ('draft','approval','posted')
                            and d.partner_id = {_partner_id}
                            and g.move_type = 'out_invoice'
                            and j.picking_type_id_name = 'Delivery Orders'
                            and j.state = 'done'
                            and g.source_document is not null
                        )""".format(_start_date=str(data.get('start_date')),
                                    _end_date=str(data.get('end_date')),
                                    _partner_id=data.get('partner_id'), _company_id=data.get('company_id')))
            res_penjualan = self._cr.dictfetchall()

            if data.get('company_id'):
                domain_c = [('id', '=', data.get('company_id'))]
                company_obj = self.env['res.company'].search(domain_c)

            # if res_penjualan :
            data = []
            amoun_untaxed = 0
            amount_tax = 0
            total_qty = 0
            total_penjualan = 0
            docs = data
            for rec in res_penjualan:
                sml_id = rec.get('sml_id')
                sml = self.env['stock.move.line'].sudo().search([('id', '=', sml_id)])
                tanggal = rec.get('tanggal').strftime('%Y-%m-%d') if rec.get('tanggal') else '-'
                if rec.get('harga_satuan') > 0 :
                    amount_untaxed = ((rec.get('harga_satuan') - rec.get('diskon')) * rec.get('qty_done')) - rec.get('global_diskon_perline')
                else:
                    amount_untaxed = 0
                if rec.get('tax') > 0:
                    # amount_tax = amount_untaxed * rec.get('tax') / 100
                    amount_tax = rec.get('tax')
                else:
                    amount_tax = 0
                # jumlah_penjualan = amount_untaxed + amount_tax
                jumlah_penjualan = sml.price_subtotal - sml.global_diskon_line + sml.total_tax
                expiration_date = rec.get('expiration_date').strftime('%Y-%m-%d') if rec.get('expiration_date') else '-'
                data.append({
                    'sales_reference': rec.get('sales_reference'),
                    'tanggal': tanggal,
                    'kode_plu': rec.get('kode_plu'),
                    'product_name': rec.get('product_name'),
                    'qty_done': rec.get('qty_done'),
                    'customer': rec.get('customer'),
                    'sales_person': rec.get('sales_person'),
                    'lot_name': rec.get('lot_name'),
                    'expiration_date': expiration_date,
                    'uom': rec.get('uom'),
                    'harga_satuan': rec.get('harga_satuan'),
                    'diskon': rec.get('diskon'),
                    'global_diskon_perline': sml.global_diskon_line,
                    'jumlah_penjualan': jumlah_penjualan
                })

                total_qty += rec.get('qty_done')
                total_penjualan += jumlah_penjualan
            if data:
                docs = data

            result = {
                'start_date': start_date,
                'end_date': end_date,
                'docs': docs,
                'cmp': company_obj,
                'total_qty': total_qty,
                'total_penjualan': total_penjualan
            }
            return result

class x_report_pembelian_so_xlsx(models.AbstractModel):
    _name = 'report.ati_report_sale.so_peritem_xlsx_template'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objs):

        # FORMAT TABLE #
        formatHeaderCompany = workbook.add_format({'font_size': 14, 'valign':'vcenter', 'align': 'center', 'bold': True})
        formatSubHeaderCompanyBold = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center', 'bold': True})
        formatSubHeaderCompany = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'center'})
        formatHeaderTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'bold': True, 'bg_color':'#4ead2f', 'color':'white', 'text_wrap': True, 'border': 1})
        formatHeaderCurrencyTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'bold': True, 'bg_color':'#4ead2f', 'color':'white', 'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-', 'text_wrap': True, 'border': 1})
        formatDetailTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre','text_wrap': True, 'border': 1})
        formatDetailCurrencyTable = workbook.add_format({'font_size': 11, 'valign':'vcenter', 'align': 'centre', 'num_format': '_-"Rp"* #,##0.00_-;-"Rp"* #,##0.00_-;_-"Rp"* "-"_-;_-@_-', 'text_wrap': True, 'border': 1})

        title = 'Laporan Rekap Penjualan Per Item'
        sheet = workbook.add_worksheet(title)

        sheet.set_column(0, 0, 15)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 20)
        sheet.set_column(3, 3, 20)
        sheet.set_column(4, 4, 15)
        sheet.set_column(5, 5, 20)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 20)
        sheet.set_column(8, 8, 20)
        sheet.set_column(9, 9, 20)
        sheet.set_column(10, 10, 20)
        sheet.set_column(11, 11, 20)
        sheet.set_column(12, 12, 20)
        sheet.set_column(13, 13, 20)
        # sheet.set_column(14, 14, 20)

        start_date = datetime.strptime(data['form']['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['form']['end_date'], '%Y-%m-%d').date()
        periode = start_date.strftime("%d %B %Y") if start_date == end_date else f'{start_date.strftime("%d %B %Y")} - {end_date.strftime("%d %B %Y")}'

        sheet.merge_range(1, 0, 1, 10, 'Laporan Rekap Penjualan Per Item', formatHeaderCompany)
        sheet.merge_range(2, 0, 2, 10, f'Periode {periode}', formatSubHeaderCompanyBold)
        sheet.merge_range(3, 0, 3, 10, '(Dalam Rupiah)', formatSubHeaderCompany)

        row =  5
        column = 0
        for header in header_title:
            sheet.write(row, column, header, formatHeaderTable)
            column += 1


        #### DATA REPORT ####
        domain = [('state', '=', 'sale')]
        if data['form']['start_date']:
            domain.append(('create_date', '>=', data['form']['start_date']))
        if data['form']['end_date']:
            domain.append(('create_date', '<=', data['form']['end_date']))
        if data['form']['company_id']:
            domain.append(('company_id', '=', data['form']['company_id']))
        if data['form']['product_id']:
            domain.append(('product_id', '=', data['form']['product_id']))
        if data['form']['partner_id']:
            domain.append(('partner_id', '=', data['form']['partner_id']))
        if data['form']['sales_person']:
            domain.append(('sales_person', '=', data['form']['sales_person']))

        total_qty = 0
        total_penjualan = 0
        row = row + 1
        if data['form']['product_id'] == False and data['form']['partner_id'] == False and data['form']['sales_person'] == False:
            self._cr.execute("""(
                            select
                                a.id as sml_id,
                                d.name as sales_reference,
                                date(g.invoice_date) as tanggal,
                                i.sku as kode_plu,
                                i.name as product_name,
                                a.qty_done as qty_done,
                                (select name from res_partner where id= d.partner_id) as customer,
                                (select name from hr_employee where id = d.sales_person) as sales_person,
                                (select name from stock_production_lot where id = a.lot_id) as lot_name,
                                (select date(expiration_date) from stock_production_lot where id = a.lot_id) as expiration_date,
                                (select name from uom_uom where id = a.product_uom_id) as uom,
                                coalesce(c.discount_amount,0) as diskon,
                                coalesce(f.harga_satuan,0) as harga_satuan,
                                case
                                    when (select count(z.id) from stock_move_line z where z.picking_id = j.id) > 0 and c.price_unit > 0 then coalesce(d.global_discount/(select count(z.id) from stock_move_line z where z.picking_id = j.id),0)
                                    else 0
                                end as global_diskon_perline,
                                coalesce(l.amount,0) as tax
                            from stock_move_line a
                                join stock_move b on b.id = a.move_id
                                join sale_order_line c on c.id = b.sale_line_id
                                join sale_order d on d.id = c.order_id
                                join sale_order_line_invoice_rel e on e.order_line_id = c.id
                                join account_move_line f on f.id = e.invoice_line_id
                                join account_move g on g.id = f.move_id
                                join product_product h on h.id = a.product_id
                                join product_template i on i.id = h.product_tmpl_id
                                join stock_picking j on a.picking_id = j.id
                                left join account_tax_sale_order_line_rel k on k.sale_order_line_id = c.id
                                left join account_tax l on l.id = k.account_tax_id
                            where date(g.invoice_date) >= '{_start_date}'
                                and date(g.invoice_date) <= '{_end_date}'
                                and g.company_id = {_company_id}
                                and g.state in ('draft','approval','posted')
                                and g.move_type = 'out_invoice'
                                and j.picking_type_id_name = 'Delivery Orders'
                                and j.state = 'done'
                                and g.source_document is not null
                            )""".format(_start_date=str(data['form']['start_date']),
                                        _end_date=str(data['form']['end_date']), _company_id=data['form']['company_id']))
            res_penjualan = self._cr.dictfetchall()

            if data.get('company_id'):
                domain_c = [('id', '=', data.get('company_id'))]
                company_obj = self.env['res.company'].search(domain_c)

            if res_penjualan:
                data = []
                amoun_untaxed = 0
                amount_tax = 0
                total_qty = 0
                total_penjualan = 0
                for rec in res_penjualan:
                    sml_id = rec.get('sml_id')
                    sml = self.env['stock.move.line'].sudo().search([('id', '=',sml_id)])
                    tanggal = rec.get('tanggal').strftime('%Y-%m-%d') if rec.get('tanggal') else '-'
                    if rec.get('harga_satuan') > 0:
                        amount_untaxed = ((rec.get('harga_satuan') - rec.get('diskon')) * rec.get(
                            'qty_done')) - rec.get('global_diskon_perline')
                    else:
                        amount_untaxed = 0
                    if rec.get('tax') > 0:
                        # amount_tax = amount_untaxed * rec.get('tax') / 100
                        amount_tax = rec.get('tax')
                    else:
                        amount_tax = 0
                    # jumlah_penjualan = amount_untaxed + amount_tax
                    jumlah_penjualan = sml.price_subtotal - sml.global_diskon_line + sml.total_tax
                    expiration_date = rec.get('expiration_date').strftime('%Y-%m-%d') if rec.get('expiration_date') else '-'
                    total_qty += rec.get('qty_done')
                    total_penjualan += jumlah_penjualan

                    #### WRITE DATA ####
                    sheet.write(row, 0, rec.get('sales_reference'), formatDetailTable)
                    sheet.write(row, 1, tanggal, formatDetailTable)
                    sheet.write(row, 2, rec.get('kode_plu') or '-', formatDetailTable)
                    sheet.write(row, 3, rec.get('product_name') or '-', formatDetailTable)
                    sheet.write(row, 4, rec.get('qty_done') or '-', formatDetailTable)
                    sheet.write(row, 5, rec.get('customer') or '-', formatDetailTable)
                    sheet.write(row, 6, rec.get('sales_person') or '-', formatDetailTable)
                    sheet.write(row, 7, rec.get('lot_name') or '-', formatDetailCurrencyTable)
                    sheet.write(row, 8, expiration_date or '-', formatDetailTable)
                    sheet.write(row, 9, rec.get('uom') or '-', formatDetailTable)

                    #### WRITE DATA ####
                    # price_unit_ati = round(line.move_id.sale_line_id.price_unit + line.move_id.sale_line_id.product_margin_amount,2)
                    # subtotal = (price_unit_ati - line.move_id.sale_line_id.discount_amount)*line.qty_done
                    # jml_pembelian += subtotal
                    # print("subtotal", line.product_id.sku, line.product_id.name, price_unit_ati, line.qty_done, subtotal)
                    sheet.write(row, 10, rec.get('harga_satuan') or '-', formatDetailCurrencyTable)
                    sheet.write(row, 11, rec.get('diskon') or '-', formatDetailCurrencyTable)
                    # sheet.write(row, 12, rec.get('global_diskon_perline') or '-', formatDetailCurrencyTable)
                    sheet.write(row, 12, sml.global_diskon_line or '-', formatDetailCurrencyTable)
                    # sheet.write(row, 13, jumlah, formatDetailCurrencyTable)
                    sheet.write(row, 13, jumlah_penjualan, formatDetailCurrencyTable)
                    row += 1
        elif data['form']['product_id'] != False and data['form']['partner_id'] != False and data['form']['sales_person'] != False:
            self._cr.execute("""(
                select
                    a.id as sml_id,
                    d.name as sales_reference,
                    date(g.invoice_date) as tanggal,
                    i.sku as kode_plu,
                    i.name as product_name,
                    a.qty_done as qty_done,
                    (select name from res_partner where id= d.partner_id) as customer,
                    (select name from hr_employee where id = d.sales_person) as sales_person,
                    (select name from stock_production_lot where id = a.lot_id) as lot_name,
                    (select date(expiration_date) from stock_production_lot where id = a.lot_id) as expiration_date,
                    (select name from uom_uom where id = a.product_uom_id) as uom,
                    coalesce(c.discount_amount,0) as diskon,
                    coalesce(f.harga_satuan,0) as harga_satuan,
                    case
                        when (select count(z.id) from stock_move_line z where z.picking_id = j.id) > 0 and c.price_unit > 0 then coalesce(d.global_discount/(select count(z.id) from stock_move_line z where z.picking_id = j.id),0)
                        else 0
                    end as global_diskon_perline,
                    coalesce(l.amount,0) as tax
                from stock_move_line a
                    join stock_move b on b.id = a.move_id
                    join sale_order_line c on c.id = b.sale_line_id
                    join sale_order d on d.id = c.order_id
                    join sale_order_line_invoice_rel e on e.order_line_id = c.id
                    join account_move_line f on f.id = e.invoice_line_id
                    join account_move g on g.id = f.move_id
                    join product_product h on h.id = a.product_id
                    join product_template i on i.id = h.product_tmpl_id
                    join stock_picking j on a.picking_id = j.id
                    left join account_tax_sale_order_line_rel k on k.sale_order_line_id = c.id
                    left join account_tax l on l.id = k.account_tax_id
                where date(g.invoice_date) >= '{_start_date}'
                    and date(g.invoice_date) <= '{_end_date}'
                    and g.company_id = {_company_id}
                    and g.state in ('draft','approval','posted')
                    and a.product_id = {_product_id}
                    and d.sales_person = {_sales_person}
                    and d.partner_id = {_partner_id}
                    and g.move_type = 'out_invoice'
                    and j.picking_type_id_name = 'Delivery Orders'
                    and j.state = 'done'
                    and g.source_document is not null
                )""".format(_sales_person=data['form']['sales_person'], _start_date=str(data['form']['start_date']),
                            _end_date=str(data['form']['end_date']), _product_id=data['form']['product_id'],
                            _partner_id=data['form']['partner_id'], _company_id=data['form']['company_id']))
            res_penjualan = self._cr.dictfetchall()

            if data.get('company_id'):
                domain_c = [('id', '=', data.get('company_id'))]
                company_obj = self.env['res.company'].search(domain_c)

            if res_penjualan:
                data = []
                amoun_untaxed = 0
                amount_tax = 0
                total_qty = 0
                total_penjualan = 0
                for rec in res_penjualan:
                    sml_id = rec.get('sml_id')
                    sml = self.env['stock.move.line'].sudo().search([('id', '=', sml_id)])
                    tanggal = rec.get('tanggal').strftime('%Y-%m-%d') if rec.get('tanggal') else '-'
                    if rec.get('harga_satuan') > 0:
                        amount_untaxed = ((rec.get('harga_satuan') - rec.get('diskon')) * rec.get(
                            'qty_done')) - rec.get('global_diskon_perline')
                    else:
                        amount_untaxed = 0
                    if rec.get('tax') > 0:
                        # amount_tax = amount_untaxed * rec.get('tax') / 100
                        amount_tax = rec.get('tax')
                    else:
                        amount_tax = 0
                    # jumlah_penjualan = amount_untaxed + amount_tax
                    jumlah_penjualan = sml.price_subtotal - sml.global_diskon_line + sml.total_tax
                    expiration_date = rec.get('expiration_date').strftime('%Y-%m-%d') if rec.get(
                        'expiration_date') else '-'
                    total_qty += rec.get('qty_done')
                    total_penjualan += jumlah_penjualan

                    #### WRITE DATA ####
                    sheet.write(row, 0, rec.get('sales_reference'), formatDetailTable)
                    sheet.write(row, 1, tanggal, formatDetailTable)
                    sheet.write(row, 2, rec.get('kode_plu') or '-', formatDetailTable)
                    sheet.write(row, 3, rec.get('product_name') or '-', formatDetailTable)
                    sheet.write(row, 4, rec.get('qty_done') or '-', formatDetailTable)
                    sheet.write(row, 5, rec.get('customer') or '-', formatDetailTable)
                    sheet.write(row, 6, rec.get('sales_person') or '-', formatDetailTable)
                    sheet.write(row, 7, rec.get('lot_name') or '-', formatDetailCurrencyTable)
                    sheet.write(row, 8, expiration_date or '-', formatDetailTable)
                    sheet.write(row, 9, rec.get('uom') or '-', formatDetailTable)

                    #### WRITE DATA ####
                    # price_unit_ati = round(line.move_id.sale_line_id.price_unit + line.move_id.sale_line_id.product_margin_amount,2)
                    # subtotal = (price_unit_ati - line.move_id.sale_line_id.discount_amount)*line.qty_done
                    # jml_pembelian += subtotal
                    # print("subtotal", line.product_id.sku, line.product_id.name, price_unit_ati, line.qty_done, subtotal)
                    sheet.write(row, 10, rec.get('harga_satuan') or '-', formatDetailCurrencyTable)
                    sheet.write(row, 11, rec.get('diskon') or '-', formatDetailCurrencyTable)
                    # sheet.write(row, 12, rec.get('global_diskon_perline') or '-', formatDetailCurrencyTable)
                    sheet.write(row, 12, sml.global_diskon_line or '-', formatDetailCurrencyTable)
                    # sheet.write(row, 13, jumlah, formatDetailCurrencyTable)
                    sheet.write(row, 13, jumlah_penjualan, formatDetailCurrencyTable)
                    row += 1
        elif data['form']['product_id'] != False and data['form']['partner_id'] == False and data['form']['sales_person'] == False:
            self._cr.execute("""(
                        select
                            a.id as sml_id,
                            d.name as sales_reference,
                            date(g.invoice_date) as tanggal,
                            i.sku as kode_plu,
                            i.name as product_name,
                            a.qty_done as qty_done,
                            (select name from res_partner where id= d.partner_id) as customer,
                            (select name from hr_employee where id = d.sales_person) as sales_person,
                            (select name from stock_production_lot where id = a.lot_id) as lot_name,
                            (select date(expiration_date) from stock_production_lot where id = a.lot_id) as expiration_date,
                            (select name from uom_uom where id = a.product_uom_id) as uom,
                            coalesce(c.discount_amount,0) as diskon,
                            coalesce(f.harga_satuan,0) as harga_satuan,
                            case
                                when (select count(z.id) from stock_move_line z where z.picking_id = j.id) > 0 and c.price_unit > 0 then coalesce(d.global_discount/(select count(z.id) from stock_move_line z where z.picking_id = j.id),0)
                                else 0
                            end as global_diskon_perline,
                            coalesce(l.amount,0) as tax
                        from stock_move_line a
                            join stock_move b on b.id = a.move_id
                            join sale_order_line c on c.id = b.sale_line_id
                            join sale_order d on d.id = c.order_id
                            join sale_order_line_invoice_rel e on e.order_line_id = c.id
                            join account_move_line f on f.id = e.invoice_line_id
                            join account_move g on g.id = f.move_id
                            join product_product h on h.id = a.product_id
                            join product_template i on i.id = h.product_tmpl_id
                            join stock_picking j on a.picking_id = j.id
                            left join account_tax_sale_order_line_rel k on k.sale_order_line_id = c.id
                            left join account_tax l on l.id = k.account_tax_id
                        where date(g.invoice_date) >= '{_start_date}'
                            and date(g.invoice_date) <= '{_end_date}'
                            and g.company_id = {_company_id}
                            and g.state in ('draft','approval','posted')
                            and a.product_id = {_product_id}
                            and g.move_type = 'out_invoice'
                            and j.picking_type_id_name = 'Delivery Orders'
                            and j.state = 'done'
                            and g.source_document is not null
                            )""".format(_start_date=str(data['form']['start_date']),
                                        _end_date=str(data['form']['end_date']), _product_id=data['form']['product_id'],
                                        _company_id=data['form']['company_id']))
            res_penjualan = self._cr.dictfetchall()

            if data.get('company_id'):
                domain_c = [('id', '=', data.get('company_id'))]
                company_obj = self.env['res.company'].search(domain_c)

            if res_penjualan:
                data = []
                amoun_untaxed = 0
                amount_tax = 0
                total_qty = 0
                total_penjualan = 0
                for rec in res_penjualan:
                    sml_id = rec.get('sml_id')
                    sml = self.env['stock.move.line'].sudo().search([('id', '=', sml_id)])
                    tanggal = rec.get('tanggal').strftime('%Y-%m-%d') if rec.get('tanggal') else '-'
                    if rec.get('harga_satuan') > 0:
                        amount_untaxed = ((rec.get('harga_satuan') - rec.get('diskon')) * rec.get(
                            'qty_done')) - rec.get('global_diskon_perline')
                    else:
                        amount_untaxed = 0
                    if rec.get('tax') > 0:
                        # amount_tax = amount_untaxed * rec.get('tax') / 100
                        amount_tax = rec.get('tax')
                    else:
                        amount_tax = 0
                    # jumlah_penjualan = amount_untaxed + amount_tax
                    jumlah_penjualan = sml.price_subtotal - sml.global_diskon_line + sml.total_tax
                    expiration_date = rec.get('expiration_date').strftime('%Y-%m-%d') if rec.get(
                        'expiration_date') else '-'
                    total_qty += rec.get('qty_done')
                    total_penjualan += jumlah_penjualan

                    #### WRITE DATA ####
                    sheet.write(row, 0, rec.get('sales_reference'), formatDetailTable)
                    sheet.write(row, 1, tanggal, formatDetailTable)
                    sheet.write(row, 2, rec.get('kode_plu') or '-', formatDetailTable)
                    sheet.write(row, 3, rec.get('product_name') or '-', formatDetailTable)
                    sheet.write(row, 4, rec.get('qty_done') or '-', formatDetailTable)
                    sheet.write(row, 5, rec.get('customer') or '-', formatDetailTable)
                    sheet.write(row, 6, rec.get('sales_person') or '-', formatDetailTable)
                    sheet.write(row, 7, rec.get('lot_name') or '-', formatDetailCurrencyTable)
                    sheet.write(row, 8, expiration_date or '-', formatDetailTable)
                    sheet.write(row, 9, rec.get('uom') or '-', formatDetailTable)

                    #### WRITE DATA ####
                    # price_unit_ati = round(line.move_id.sale_line_id.price_unit + line.move_id.sale_line_id.product_margin_amount,2)
                    # subtotal = (price_unit_ati - line.move_id.sale_line_id.discount_amount)*line.qty_done
                    # jml_pembelian += subtotal
                    # print("subtotal", line.product_id.sku, line.product_id.name, price_unit_ati, line.qty_done, subtotal)
                    sheet.write(row, 10, rec.get('harga_satuan') or '-', formatDetailCurrencyTable)
                    sheet.write(row, 11, rec.get('diskon') or '-', formatDetailCurrencyTable)
                    # sheet.write(row, 12, rec.get('global_diskon_perline') or '-', formatDetailCurrencyTable)
                    sheet.write(row, 12, sml.global_diskon_line or '-', formatDetailCurrencyTable)
                    # sheet.write(row, 13, jumlah, formatDetailCurrencyTable)
                    sheet.write(row, 13, jumlah_penjualan, formatDetailCurrencyTable)
                    row += 1
        elif data['form']['product_id'] != False and data['form']['partner_id'] != False and data['form']['sales_person'] == False:
            self._cr.execute("""(
                        select
                            a.id as sml_id,
                            d.name as sales_reference,
                            date(g.invoice_date) as tanggal,
                            i.sku as kode_plu,
                            i.name as product_name,
                            a.qty_done as qty_done,
                            (select name from res_partner where id= d.partner_id) as customer,
                            (select name from hr_employee where id = d.sales_person) as sales_person,
                            (select name from stock_production_lot where id = a.lot_id) as lot_name,
                            (select date(expiration_date) from stock_production_lot where id = a.lot_id) as expiration_date,
                            (select name from uom_uom where id = a.product_uom_id) as uom,
                            coalesce(c.discount_amount,0) as diskon,
                            coalesce(f.harga_satuan,0) as harga_satuan,
                            case
                                when (select count(z.id) from stock_move_line z where z.picking_id = j.id) > 0 and c.price_unit > 0 then coalesce(d.global_discount/(select count(z.id) from stock_move_line z where z.picking_id = j.id),0)
                                else 0
                            end as global_diskon_perline,
                            coalesce(l.amount,0) as tax
                        from stock_move_line a
                            join stock_move b on b.id = a.move_id
                            join sale_order_line c on c.id = b.sale_line_id
                            join sale_order d on d.id = c.order_id
                            join sale_order_line_invoice_rel e on e.order_line_id = c.id
                            join account_move_line f on f.id = e.invoice_line_id
                            join account_move g on g.id = f.move_id
                            join product_product h on h.id = a.product_id
                            join product_template i on i.id = h.product_tmpl_id
                            join stock_picking j on a.picking_id = j.id
                            left join account_tax_sale_order_line_rel k on k.sale_order_line_id = c.id
                            left join account_tax l on l.id = k.account_tax_id
                        where date(g.invoice_date) >= '{_start_date}'
                            and date(g.invoice_date) <= '{_end_date}'
                            and g.company_id = {_company_id}
                            and g.state in ('draft','approval','posted')
                            and a.product_id = {_product_id}
                            and d.partner_id = {_partner_id}
                            and g.move_type = 'out_invoice'
                            and j.picking_type_id_name = 'Delivery Orders'
                            and j.state = 'done'
                            and g.source_document is not null
                            )""".format(_start_date=str(data['form']['start_date']),
                                        _end_date=str(data['form']['end_date']), _product_id=data['form']['product_id'],
                                        _partner_id=data['form']['partner_id'], _company_id=data['form']['company_id']))
            res_penjualan = self._cr.dictfetchall()

            if data.get('company_id'):
                domain_c = [('id', '=', data.get('company_id'))]
                company_obj = self.env['res.company'].search(domain_c)

            if res_penjualan:
                data = []
                amoun_untaxed = 0
                amount_tax = 0
                total_qty = 0
                total_penjualan = 0
                for rec in res_penjualan:
                    sml_id = rec.get('sml_id')
                    sml = self.env['stock.move.line'].sudo().search([('id', '=', sml_id)])
                    tanggal = rec.get('tanggal').strftime('%Y-%m-%d') if rec.get('tanggal') else '-'
                    if rec.get('harga_satuan') > 0:
                        amount_untaxed = ((rec.get('harga_satuan') - rec.get('diskon')) * rec.get(
                            'qty_done')) - rec.get('global_diskon_perline')
                    else:
                        amount_untaxed = 0
                    if rec.get('tax') > 0:
                        # amount_tax = amount_untaxed * rec.get('tax') / 100
                        amount_tax = rec.get('tax')
                    else:
                        amount_tax = 0
                    # jumlah_penjualan = amount_untaxed + amount_tax
                    jumlah_penjualan = sml.price_subtotal - sml.global_diskon_line + sml.total_tax
                    expiration_date = rec.get('expiration_date').strftime('%Y-%m-%d') if rec.get(
                        'expiration_date') else '-'
                    total_qty += rec.get('qty_done')
                    total_penjualan += jumlah_penjualan

                    #### WRITE DATA ####
                    sheet.write(row, 0, rec.get('sales_reference'), formatDetailTable)
                    sheet.write(row, 1, tanggal, formatDetailTable)
                    sheet.write(row, 2, rec.get('kode_plu') or '-', formatDetailTable)
                    sheet.write(row, 3, rec.get('product_name') or '-', formatDetailTable)
                    sheet.write(row, 4, rec.get('qty_done') or '-', formatDetailTable)
                    sheet.write(row, 5, rec.get('customer') or '-', formatDetailTable)
                    sheet.write(row, 6, rec.get('sales_person') or '-', formatDetailTable)
                    sheet.write(row, 7, rec.get('lot_name') or '-', formatDetailCurrencyTable)
                    sheet.write(row, 8, expiration_date or '-', formatDetailTable)
                    sheet.write(row, 9, rec.get('uom') or '-', formatDetailTable)

                    #### WRITE DATA ####
                    # price_unit_ati = round(line.move_id.sale_line_id.price_unit + line.move_id.sale_line_id.product_margin_amount,2)
                    # subtotal = (price_unit_ati - line.move_id.sale_line_id.discount_amount)*line.qty_done
                    # jml_pembelian += subtotal
                    # print("subtotal", line.product_id.sku, line.product_id.name, price_unit_ati, line.qty_done, subtotal)
                    sheet.write(row, 10, rec.get('harga_satuan') or '-', formatDetailCurrencyTable)
                    sheet.write(row, 11, rec.get('diskon') or '-', formatDetailCurrencyTable)
                    # sheet.write(row, 12, rec.get('global_diskon_perline') or '-', formatDetailCurrencyTable)
                    sheet.write(row, 12, sml.global_diskon_line or '-', formatDetailCurrencyTable)
                    # sheet.write(row, 13, jumlah, formatDetailCurrencyTable)
                    sheet.write(row, 13, jumlah_penjualan, formatDetailCurrencyTable)
                    row += 1
        elif data['form']['product_id'] != False and data['form']['partner_id'] == False and data['form']['sales_person'] != False:
            self._cr.execute("""(
                            select
                                a.id as sml_id,
                                d.name as sales_reference,
                                date(g.invoice_date) as tanggal,
                                i.sku as kode_plu,
                                i.name as product_name,
                                a.qty_done as qty_done,
                                (select name from res_partner where id= d.partner_id) as customer,
                                (select name from hr_employee where id = d.sales_person) as sales_person,
                                (select name from stock_production_lot where id = a.lot_id) as lot_name,
                                (select date(expiration_date) from stock_production_lot where id = a.lot_id) as expiration_date,
                                (select name from uom_uom where id = a.product_uom_id) as uom,
                                coalesce(c.discount_amount,0) as diskon,
                                coalesce(f.harga_satuan,0) as harga_satuan,
                                case
                                    when (select count(z.id) from stock_move_line z where z.picking_id = j.id) > 0 and c.price_unit > 0 then coalesce(d.global_discount/(select count(z.id) from stock_move_line z where z.picking_id = j.id),0)
                                    else 0
                                end as global_diskon_perline,
                                coalesce(l.amount,0) as tax
                            from stock_move_line a
                                join stock_move b on b.id = a.move_id
                                join sale_order_line c on c.id = b.sale_line_id
                                join sale_order d on d.id = c.order_id
                                join sale_order_line_invoice_rel e on e.order_line_id = c.id
                                join account_move_line f on f.id = e.invoice_line_id
                                join account_move g on g.id = f.move_id
                                join product_product h on h.id = a.product_id
                                join product_template i on i.id = h.product_tmpl_id
                                join stock_picking j on a.picking_id = j.id
                                left join account_tax_sale_order_line_rel k on k.sale_order_line_id = c.id
                                left join account_tax l on l.id = k.account_tax_id
                            where date(g.invoice_date) >= '{_start_date}'
                                and date(g.invoice_date) <= '{_end_date}'
                                and g.company_id = {_company_id}
                                and g.state in ('draft','approval','posted')
                                and a.product_id = {_product_id}
                                and d.sales_person = {_sales_person}
                                and g.move_type = 'out_invoice'
                                and j.picking_type_id_name = 'Delivery Orders'
                                and j.state = 'done'
                                and g.source_document is not null
                            )""".format(_sales_person=data['form']['sales_person'],
                                        _start_date=str(data['form']['start_date']),
                                        _end_date=str(data['form']['end_date']), _product_id=data['form']['product_id'],
                                        _company_id=data['form']['company_id']))
            res_penjualan = self._cr.dictfetchall()

            if data.get('company_id'):
                domain_c = [('id', '=', data.get('company_id'))]
                company_obj = self.env['res.company'].search(domain_c)

            if res_penjualan:
                data = []
                amoun_untaxed = 0
                amount_tax = 0
                total_qty = 0
                total_penjualan = 0
                for rec in res_penjualan:
                    sml_id = rec.get('sml_id')
                    sml = self.env['stock.move.line'].sudo().search([('id', '=', sml_id)])
                    tanggal = rec.get('tanggal').strftime('%Y-%m-%d') if rec.get('tanggal') else '-'
                    if rec.get('harga_satuan') > 0:
                        amount_untaxed = ((rec.get('harga_satuan') - rec.get('diskon')) * rec.get(
                            'qty_done')) - rec.get('global_diskon_perline')
                    else:
                        amount_untaxed = 0
                    if rec.get('tax') > 0:
                        # amount_tax = amount_untaxed * rec.get('tax') / 100
                        amount_tax = rec.get('tax')
                    else:
                        amount_tax = 0
                    # jumlah_penjualan = amount_untaxed + amount_tax
                    jumlah_penjualan = sml.price_subtotal - sml.global_diskon_line + sml.total_tax
                    expiration_date = rec.get('expiration_date').strftime('%Y-%m-%d') if rec.get(
                        'expiration_date') else '-'
                    total_qty += rec.get('qty_done')
                    total_penjualan += jumlah_penjualan

                    #### WRITE DATA ####
                    sheet.write(row, 0, rec.get('sales_reference'), formatDetailTable)
                    sheet.write(row, 1, tanggal, formatDetailTable)
                    sheet.write(row, 2, rec.get('kode_plu') or '-', formatDetailTable)
                    sheet.write(row, 3, rec.get('product_name') or '-', formatDetailTable)
                    sheet.write(row, 4, rec.get('qty_done') or '-', formatDetailTable)
                    sheet.write(row, 5, rec.get('customer') or '-', formatDetailTable)
                    sheet.write(row, 6, rec.get('sales_person') or '-', formatDetailTable)
                    sheet.write(row, 7, rec.get('lot_name') or '-', formatDetailCurrencyTable)
                    sheet.write(row, 8, expiration_date or '-', formatDetailTable)
                    sheet.write(row, 9, rec.get('uom') or '-', formatDetailTable)

                    #### WRITE DATA ####
                    # price_unit_ati = round(line.move_id.sale_line_id.price_unit + line.move_id.sale_line_id.product_margin_amount,2)
                    # subtotal = (price_unit_ati - line.move_id.sale_line_id.discount_amount)*line.qty_done
                    # jml_pembelian += subtotal
                    # print("subtotal", line.product_id.sku, line.product_id.name, price_unit_ati, line.qty_done, subtotal)
                    sheet.write(row, 10, rec.get('harga_satuan') or '-', formatDetailCurrencyTable)
                    sheet.write(row, 11, rec.get('diskon') or '-', formatDetailCurrencyTable)
                    # sheet.write(row, 12, rec.get('global_diskon_perline') or '-', formatDetailCurrencyTable)
                    sheet.write(row, 12, sml.global_diskon_line or '-', formatDetailCurrencyTable)
                    # sheet.write(row, 13, jumlah, formatDetailCurrencyTable)
                    sheet.write(row, 13, jumlah_penjualan, formatDetailCurrencyTable)
                    row += 1
        elif data['form']['product_id'] == False and data['form']['partner_id'] != False and data['form']['sales_person'] != False:
            self._cr.execute("""(
                            select
                                a.id as sml_id,
                                d.name as sales_reference,
                                date(g.invoice_date) as tanggal,
                                i.sku as kode_plu,
                                i.name as product_name,
                                a.qty_done as qty_done,
                                (select name from res_partner where id= d.partner_id) as customer,
                                (select name from hr_employee where id = d.sales_person) as sales_person,
                                (select name from stock_production_lot where id = a.lot_id) as lot_name,
                                (select date(expiration_date) from stock_production_lot where id = a.lot_id) as expiration_date,
                                (select name from uom_uom where id = a.product_uom_id) as uom,
                                coalesce(c.discount_amount,0) as diskon,
                                coalesce(f.harga_satuan,0) as harga_satuan,
                                case
                                    when (select count(z.id) from stock_move_line z where z.picking_id = j.id) > 0 and c.price_unit > 0 then coalesce(d.global_discount/(select count(z.id) from stock_move_line z where z.picking_id = j.id),0)
                                    else 0
                                end as global_diskon_perline,
                                coalesce(l.amount,0) as tax
                            from stock_move_line a
                                join stock_move b on b.id = a.move_id
                                join sale_order_line c on c.id = b.sale_line_id
                                join sale_order d on d.id = c.order_id
                                join sale_order_line_invoice_rel e on e.order_line_id = c.id
                                join account_move_line f on f.id = e.invoice_line_id
                                join account_move g on g.id = f.move_id
                                join product_product h on h.id = a.product_id
                                join product_template i on i.id = h.product_tmpl_id
                                join stock_picking j on a.picking_id = j.id
                                left join account_tax_sale_order_line_rel k on k.sale_order_line_id = c.id
                                left join account_tax l on l.id = k.account_tax_id
                            where date(g.invoice_date) >= '{_start_date}'
                                and date(g.invoice_date) <= '{_end_date}'
                                and g.company_id = {_company_id}
                                and g.state in ('draft','approval','posted')
                                and d.sales_person = {_sales_person}
                                and d.partner_id = {_partner_id}
                                and g.move_type = 'out_invoice'
                                and j.picking_type_id_name = 'Delivery Orders'
                                and j.state = 'done'
                                and g.source_document is not null
                            )""".format(_sales_person=data['form']['sales_person'],
                                        _start_date=str(data['form']['start_date']),
                                        _end_date=str(data['form']['end_date']),
                                        _partner_id=data['form']['partner_id'], _company_id=data['form']['company_id']))
            res_penjualan = self._cr.dictfetchall()

            if data.get('company_id'):
                domain_c = [('id', '=', data.get('company_id'))]
                company_obj = self.env['res.company'].search(domain_c)

            if res_penjualan:
                data = []
                amoun_untaxed = 0
                amount_tax = 0
                total_qty = 0
                total_penjualan = 0
                for rec in res_penjualan:
                    sml_id = rec.get('sml_id')
                    sml = self.env['stock.move.line'].sudo().search([('id', '=', sml_id)])
                    tanggal = rec.get('tanggal').strftime('%Y-%m-%d') if rec.get('tanggal') else '-'
                    if rec.get('harga_satuan') > 0:
                        amount_untaxed = ((rec.get('harga_satuan') - rec.get('diskon')) * rec.get(
                            'qty_done')) - rec.get('global_diskon_perline')
                    else:
                        amount_untaxed = 0
                    if rec.get('tax') > 0:
                        # amount_tax = amount_untaxed * rec.get('tax') / 100
                        amount_tax = rec.get('tax')
                    else:
                        amount_tax = 0
                    # jumlah_penjualan = amount_untaxed + amount_tax
                    jumlah_penjualan = sml.price_subtotal - sml.global_diskon_line + sml.total_tax
                    expiration_date = rec.get('expiration_date').strftime('%Y-%m-%d') if rec.get(
                        'expiration_date') else '-'
                    total_qty += rec.get('qty_done')
                    total_penjualan += jumlah_penjualan

                    #### WRITE DATA ####
                    sheet.write(row, 0, rec.get('sales_reference'), formatDetailTable)
                    sheet.write(row, 1, tanggal, formatDetailTable)
                    sheet.write(row, 2, rec.get('kode_plu') or '-', formatDetailTable)
                    sheet.write(row, 3, rec.get('product_name') or '-', formatDetailTable)
                    sheet.write(row, 4, rec.get('qty_done') or '-', formatDetailTable)
                    sheet.write(row, 5, rec.get('customer') or '-', formatDetailTable)
                    sheet.write(row, 6, rec.get('sales_person') or '-', formatDetailTable)
                    sheet.write(row, 7, rec.get('lot_name') or '-', formatDetailCurrencyTable)
                    sheet.write(row, 8, expiration_date or '-', formatDetailTable)
                    sheet.write(row, 9, rec.get('uom') or '-', formatDetailTable)

                    #### WRITE DATA ####
                    # price_unit_ati = round(line.move_id.sale_line_id.price_unit + line.move_id.sale_line_id.product_margin_amount,2)
                    # subtotal = (price_unit_ati - line.move_id.sale_line_id.discount_amount)*line.qty_done
                    # jml_pembelian += subtotal
                    # print("subtotal", line.product_id.sku, line.product_id.name, price_unit_ati, line.qty_done, subtotal)
                    sheet.write(row, 10, rec.get('harga_satuan') or '-', formatDetailCurrencyTable)
                    sheet.write(row, 11, rec.get('diskon') or '-', formatDetailCurrencyTable)
                    # sheet.write(row, 12, rec.get('global_diskon_perline') or '-', formatDetailCurrencyTable)
                    sheet.write(row, 12, sml.global_diskon_line or '-', formatDetailCurrencyTable)
                    # sheet.write(row, 13, jumlah, formatDetailCurrencyTable)
                    sheet.write(row, 13, jumlah_penjualan, formatDetailCurrencyTable)
                    row += 1
        elif data['form']['product_id'] == False and data['form']['partner_id']== False and data['form']['sales_person'] != False:
            self._cr.execute("""(
                            select
                                a.id as sml_id,
                                d.name as sales_reference,
                                date(g.invoice_date) as tanggal,
                                i.sku as kode_plu,
                                i.name as product_name,
                                a.qty_done as qty_done,
                                (select name from res_partner where id= d.partner_id) as customer,
                                (select name from hr_employee where id = d.sales_person) as sales_person,
                                (select name from stock_production_lot where id = a.lot_id) as lot_name,
                                (select date(expiration_date) from stock_production_lot where id = a.lot_id) as expiration_date,
                                (select name from uom_uom where id = a.product_uom_id) as uom,
                                coalesce(c.discount_amount,0) as diskon,
                                coalesce(f.harga_satuan,0) as harga_satuan,
                                case
                                    when (select count(z.id) from stock_move_line z where z.picking_id = j.id) > 0 and c.price_unit > 0 then coalesce(d.global_discount/(select count(z.id) from stock_move_line z where z.picking_id = j.id),0)
                                    else 0
                                end as global_diskon_perline,
                                coalesce(l.amount,0) as tax
                            from stock_move_line a
                                join stock_move b on b.id = a.move_id
                                join sale_order_line c on c.id = b.sale_line_id
                                join sale_order d on d.id = c.order_id
                                join sale_order_line_invoice_rel e on e.order_line_id = c.id
                                join account_move_line f on f.id = e.invoice_line_id
                                join account_move g on g.id = f.move_id
                                join product_product h on h.id = a.product_id
                                join product_template i on i.id = h.product_tmpl_id
                                join stock_picking j on a.picking_id = j.id
                                left join account_tax_sale_order_line_rel k on k.sale_order_line_id = c.id
                                left join account_tax l on l.id = k.account_tax_id
                            where date(g.invoice_date) >= '{_start_date}'
                                and date(g.invoice_date) <= '{_end_date}'
                                and g.company_id = {_company_id}
                                and g.state in ('draft','approval','posted')
                                and d.sales_person = {_sales_person}
                                and g.move_type = 'out_invoice'
                                and j.picking_type_id_name = 'Delivery Orders'
                                and j.state = 'done'
                                and g.source_document is not null
                            )""".format(_sales_person=data['form']['sales_person'],
                                        _start_date=str(data['form']['start_date']),
                                        _end_date=str(data['form']['end_date']),
                                        _company_id=data['form']['company_id']))
            res_penjualan = self._cr.dictfetchall()

            if data.get('company_id'):
                domain_c = [('id', '=', data.get('company_id'))]
                company_obj = self.env['res.company'].search(domain_c)

            if res_penjualan:
                data = []
                amoun_untaxed = 0
                amount_tax = 0
                total_qty = 0
                total_penjualan = 0
                for rec in res_penjualan:
                    sml_id = rec.get('sml_id')
                    sml = self.env['stock.move.line'].sudo().search([('id', '=', sml_id)])
                    tanggal = rec.get('tanggal').strftime('%Y-%m-%d') if rec.get('tanggal') else '-'
                    if rec.get('harga_satuan') > 0:
                        amount_untaxed = ((rec.get('harga_satuan') - rec.get('diskon')) * rec.get(
                            'qty_done')) - rec.get('global_diskon_perline')
                    else:
                        amount_untaxed = 0
                    if rec.get('tax') > 0:
                        # amount_tax = amount_untaxed * rec.get('tax') / 100
                        amount_tax = rec.get('tax')
                    else:
                        amount_tax = 0
                    # jumlah_penjualan = amount_untaxed + amount_tax
                    jumlah_penjualan = sml.price_subtotal - sml.global_diskon_line + sml.total_tax
                    expiration_date = rec.get('expiration_date').strftime('%Y-%m-%d') if rec.get(
                        'expiration_date') else '-'
                    total_qty += rec.get('qty_done')
                    total_penjualan += jumlah_penjualan

                    #### WRITE DATA ####
                    sheet.write(row, 0, rec.get('sales_reference'), formatDetailTable)
                    sheet.write(row, 1, tanggal, formatDetailTable)
                    sheet.write(row, 2, rec.get('kode_plu') or '-', formatDetailTable)
                    sheet.write(row, 3, rec.get('product_name') or '-', formatDetailTable)
                    sheet.write(row, 4, rec.get('qty_done') or '-', formatDetailTable)
                    sheet.write(row, 5, rec.get('customer') or '-', formatDetailTable)
                    sheet.write(row, 6, rec.get('sales_person') or '-', formatDetailTable)
                    sheet.write(row, 7, rec.get('lot_name') or '-', formatDetailCurrencyTable)
                    sheet.write(row, 8, expiration_date or '-', formatDetailTable)
                    sheet.write(row, 9, rec.get('uom') or '-', formatDetailTable)

                    #### WRITE DATA ####
                    # price_unit_ati = round(line.move_id.sale_line_id.price_unit + line.move_id.sale_line_id.product_margin_amount,2)
                    # subtotal = (price_unit_ati - line.move_id.sale_line_id.discount_amount)*line.qty_done
                    # jml_pembelian += subtotal
                    # print("subtotal", line.product_id.sku, line.product_id.name, price_unit_ati, line.qty_done, subtotal)
                    sheet.write(row, 10, rec.get('harga_satuan') or '-', formatDetailCurrencyTable)
                    sheet.write(row, 11, rec.get('diskon') or '-', formatDetailCurrencyTable)
                    # sheet.write(row, 12, rec.get('global_diskon_perline') or '-', formatDetailCurrencyTable)
                    sheet.write(row, 12, sml.global_diskon_line or '-', formatDetailCurrencyTable)
                    # sheet.write(row, 13, jumlah, formatDetailCurrencyTable)
                    sheet.write(row, 13, jumlah_penjualan, formatDetailCurrencyTable)
                    row += 1
        elif data['form']['product_id'] == False and data['form']['partner_id'] != False and data['form']['sales_person'] == False:
            self._cr.execute("""(
                            select
                                a.id as sml_id,
                                d.name as sales_reference,
                                date(g.invoice_date) as tanggal,
                                i.sku as kode_plu,
                                i.name as product_name,
                                a.qty_done as qty_done,
                                (select name from res_partner where id= d.partner_id) as customer,
                                (select name from hr_employee where id = d.sales_person) as sales_person,
                                (select name from stock_production_lot where id = a.lot_id) as lot_name,
                                (select date(expiration_date) from stock_production_lot where id = a.lot_id) as expiration_date,
                                (select name from uom_uom where id = a.product_uom_id) as uom,
                                coalesce(c.discount_amount,0) as diskon,
                                coalesce(f.harga_satuan,0) as harga_satuan,
                                case
                                    when (select count(z.id) from stock_move_line z where z.picking_id = j.id) > 0 and c.price_unit > 0 then coalesce(d.global_discount/(select count(z.id) from stock_move_line z where z.picking_id = j.id),0)
                                    else 0
                                end as global_diskon_perline,
                                coalesce(l.amount,0) as tax
                            from stock_move_line a
                                join stock_move b on b.id = a.move_id
                                join sale_order_line c on c.id = b.sale_line_id
                                join sale_order d on d.id = c.order_id
                                join sale_order_line_invoice_rel e on e.order_line_id = c.id
                                join account_move_line f on f.id = e.invoice_line_id
                                join account_move g on g.id = f.move_id
                                join product_product h on h.id = a.product_id
                                join product_template i on i.id = h.product_tmpl_id
                                join stock_picking j on a.picking_id = j.id
                                left join account_tax_sale_order_line_rel k on k.sale_order_line_id = c.id
                                left join account_tax l on l.id = k.account_tax_id
                            where date(g.invoice_date) >= '{_start_date}'
                                and date(g.invoice_date) <= '{_end_date}'
                                and g.company_id = {_company_id}
                                and g.state in ('draft','approval','posted')
                                and d.partner_id = {_partner_id}
                                and g.move_type = 'out_invoice'
                                and j.picking_type_id_name = 'Delivery Orders'
                                and j.state = 'done'
                                and g.source_document is not null
                            )""".format(_start_date=str(data['form']['start_date']),
                                        _end_date=str(data['form']['end_date']),
                                        _partner_id=data['form']['partner_id'], _company_id=data['form']['company_id']))
            res_penjualan = self._cr.dictfetchall()

            if data.get('company_id'):
                domain_c = [('id', '=', data.get('company_id'))]
                company_obj = self.env['res.company'].search(domain_c)

            if res_penjualan:
                data = []
                amoun_untaxed = 0
                amount_tax = 0
                total_qty = 0
                total_penjualan = 0
                for rec in res_penjualan:
                    sml_id = rec.get('sml_id')
                    sml = self.env['stock.move.line'].sudo().search([('id', '=', sml_id)])
                    tanggal = rec.get('tanggal').strftime('%Y-%m-%d') if rec.get('tanggal') else '-'
                    if rec.get('harga_satuan') > 0:
                        amount_untaxed = ((rec.get('harga_satuan') - rec.get('diskon')) * rec.get(
                            'qty_done')) - rec.get('global_diskon_perline')
                    else:
                        amount_untaxed = 0
                    if rec.get('tax') > 0:
                        # amount_tax = amount_untaxed * rec.get('tax') / 100
                        amount_tax = rec.get('tax')
                    else:
                        amount_tax = 0
                    # jumlah_penjualan = amount_untaxed + amount_tax
                    jumlah_penjualan = sml.price_subtotal - sml.global_diskon_line + sml.total_tax
                    expiration_date = rec.get('expiration_date').strftime('%Y-%m-%d') if rec.get(
                        'expiration_date') else '-'
                    total_qty += rec.get('qty_done')
                    total_penjualan += jumlah_penjualan

                    #### WRITE DATA ####
                    sheet.write(row, 0, rec.get('sales_reference'), formatDetailTable)
                    sheet.write(row, 1, tanggal, formatDetailTable)
                    sheet.write(row, 2, rec.get('kode_plu') or '-', formatDetailTable)
                    sheet.write(row, 3, rec.get('product_name') or '-', formatDetailTable)
                    sheet.write(row, 4, rec.get('qty_done') or '-', formatDetailTable)
                    sheet.write(row, 5, rec.get('customer') or '-', formatDetailTable)
                    sheet.write(row, 6, rec.get('sales_person') or '-', formatDetailTable)
                    sheet.write(row, 7, rec.get('lot_name') or '-', formatDetailCurrencyTable)
                    sheet.write(row, 8, expiration_date or '-', formatDetailTable)
                    sheet.write(row, 9, rec.get('uom') or '-', formatDetailTable)

                    #### WRITE DATA ####
                    # price_unit_ati = round(line.move_id.sale_line_id.price_unit + line.move_id.sale_line_id.product_margin_amount,2)
                    # subtotal = (price_unit_ati - line.move_id.sale_line_id.discount_amount)*line.qty_done
                    # jml_pembelian += subtotal
                    # print("subtotal", line.product_id.sku, line.product_id.name, price_unit_ati, line.qty_done, subtotal)
                    sheet.write(row, 10, rec.get('harga_satuan') or '-', formatDetailCurrencyTable)
                    sheet.write(row, 11, rec.get('diskon') or '-', formatDetailCurrencyTable)
                    # sheet.write(row, 12, rec.get('global_diskon_perline') or '-', formatDetailCurrencyTable)
                    sheet.write(row, 12, sml.global_diskon_line or '-', formatDetailCurrencyTable)
                    # sheet.write(row, 13, jumlah, formatDetailCurrencyTable)
                    sheet.write(row, 13, jumlah_penjualan, formatDetailCurrencyTable)
                    row += 1

        row_end = row
        column_end = row_end + 1
        sheet.merge_range(row, 0, row, 3, 'Total', formatHeaderTable)
        sheet.write(row, 4, total_qty, formatHeaderTable)
        sheet.write(row, 5, '', formatHeaderTable)
        sheet.write(row, 6, '', formatHeaderTable)
        sheet.write(row, 7, '', formatHeaderTable)
        sheet.write(row, 8, '', formatHeaderTable)
        sheet.write(row, 9, '', formatHeaderTable)
        sheet.write(row, 10, '', formatHeaderTable)
        sheet.write(row, 11, '', formatHeaderTable)
        sheet.write(row, 12, '', formatHeaderTable)
        # sheet.write(row, 13, '', formatHeaderTable)
        sheet.write(row, 13, total_penjualan, formatHeaderCurrencyTable)


class new_report_picking_line_helper(models.Model):
    _name = 'new.report.picking.line.helper'
    _order = 'so_id asc'

    picking_id = fields.Many2one('stock.picking')
    product_id = fields.Many2one('product.product')
    so_id = fields.Many2one('sale.order')
    date = fields.Date('Date')
    sku = fields.Char('SKU')
    product_name = fields.Char('Nama Barang')
    qty = fields.Float('Qty')
    partner_id = fields.Many2one('res.partner')
    sales_person = fields.Many2one('hr.employee')
    lot_name = fields.Char('Lot Name')
    exp_date = fields.Date('Exp Date')
    satuan = fields.Many2one('uom.uom')
    price_unit = fields.Float('Harga Jual')
    diskon = fields.Float('Diskon Per Line')
    subtotal = fields.Float('Jumlah Penjualan Inc PPN')
    jml_penjualan = fields.Float('Jml Penjualan')
    global_diskon = fields.Float('Global Diskon')
    untax_amount = fields.Float('Jumlah Penjualans')


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    report_move_line_helper_ids = fields.One2many('new.report.picking.line.helper', 'picking_id')