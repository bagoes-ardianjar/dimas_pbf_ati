from odoo import fields, models, api, _
from odoo.exceptions import UserError
import math

class WizardPnlSaleSales(models.TransientModel):
    _name = 'wizard.pnl.sale.sales'
    _description = 'Wizard PNL Sale sales'

    # sales_person = fields.Many2one('res.users', string='Sales Person (*)', index=True, tracking=1)
    name = fields.Char(string='Name', default='Laporan Laba/Rugi Penjualan Per Sales Produk')
    salesperson = fields.Many2one('hr.employee', string='Sales Person')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    wizard_pnl_sales_ids = fields.One2many('wizard.pnl.sale.sales.line', 'wizard_pnl_sales_id', string='Wizard Pnl Sales Ids')


    def func_insert_data_prewiew(self):
        vals_header = {
            "name": 'Laporan Laba/Rugi Penjualan Per Sales Produk',
            "start_date": self.start_date,
            "end_date": self.end_date,
            "sales": 'All Sales Person',
            "sales_person": self.salesperson.id
        }
        new_header = self.env['pnl.sales.report.preview'].sudo().create(vals_header)
        if self.salesperson :
            self._cr.execute("""(
                select
                    b.date_order as tanggal,
                    b.id as so_id,
                    a.id as sale_line_id,
                    b.name as no_penjualan,
                    b.partner_id as pelanggan,
                    e.name as sales_person,
                    g.product_id as product_id,
                    g.product_uom_id as uom_id,
                    g.quantity as qty,
                    d.hna as harga_beli,
                    (coalesce(d.hna*g.quantity,0)) as total_beli,
                    g.price_subtotal as total_jual,
                    g.harga_satuan as harga_jual
                    from sale_order_line a
                    join sale_order b on b.id = a.order_id
                    join product_product c on c.id = a.product_id
                    join product_template d on d.id = c.product_tmpl_id
                    join hr_employee e on e.id = b.sales_person
                    join sale_order_line_invoice_rel f on f.order_line_id = a.id
                    join account_move_line g on g.id = f.invoice_line_id
                    join account_move h on h.id = g.move_id
                    where b.sales_person = {_sales_person} and h.invoice_date::TIMESTAMP::DATE >= '{_start_date}' and
                    h.invoice_date::TIMESTAMP::DATE <= '{_end_date}' and h.state in ('draft','approval','posted')
            )""".format(_sales_person=self.salesperson.id,_start_date=str(self.start_date),_end_date=str(self.end_date)))

        else:
            self._cr.execute("""(
                            select
                                b.date_order as tanggal,
                                b.id as so_id,
                                a.id as sale_line_id,
                                b.name as no_penjualan,
                                b.partner_id as pelanggan,
                                e.name as sales_person,
                                g.product_id as product_id,
                                g.product_uom_id as uom_id,
                                g.quantity as qty,
                                d.hna as harga_beli,
                                (coalesce(d.hna*g.quantity,0)) as total_beli,
                                g.price_subtotal as total_jual,
                                g.harga_satuan as harga_jual
                                from sale_order_line a
                                join sale_order b on b.id = a.order_id
                                join product_product c on c.id = a.product_id
                                join product_template d on d.id = c.product_tmpl_id
                                join hr_employee e on e.id = b.sales_person
                                join sale_order_line_invoice_rel f on f.order_line_id = a.id
                                join account_move_line g on g.id = f.invoice_line_id
                                join account_move h on h.id = g.move_id
                                where h.invoice_date::TIMESTAMP::DATE >= '{_start_date}' and
                                h.invoice_date::TIMESTAMP::DATE <= '{_end_date}' and h.state in ('draft','approval','posted')
                        )""".format(_start_date=str(self.start_date),_end_date=str(self.end_date)))
        data_preview = self._cr.dictfetchall()
        if len(data_preview) > 0 :
            uid = self._uid
            for data in data_preview:
                so_line = self.env['sale.order.line'].sudo().search([
                    ('id', '=', data['sale_line_id'])
                ])
                harga_jual = round(data['harga_jual'], 2)
                if harga_jual != 0:
                    harga_beli = data['harga_beli']
                    total_beli = data['total_beli']
                else:
                    harga_beli = 0
                    total_beli = 0
                # total_jual = round(harga_jual * data['qty'],2)
                total_jual = data['total_jual']
                profit = total_jual - total_beli
                # persentase = profit / 100
                if total_beli > 0:
                    persentase = profit / total_beli * 100
                elif harga_jual == 0:
                    persentase = 0
                else:
                    persentase = 100
                ins_values = ",".join(["('{}',{},'{}',{},'{}',{},{},{},{},{},{},{},{},{},{},{})".format(
                    data['tanggal'] or '',
                    data['so_id'] or 'Null',
                    data['no_penjualan'] or '',
                    data['pelanggan'] or '',
                    data['sales_person'] or '',
                    data['product_id'] or 'Null',
                    data['uom_id'] or 'Null',
                    round(data['qty'] or 0, 2),
                    round(harga_beli or 0, 2),
                    round(harga_jual or 0, 2),
                    round(total_beli or 0, 2),
                    round(total_jual or 0, 2),
                    round(profit or 0, 2),
                    round(persentase or 0, 2),
                    uid,
                    new_header.id
                )])
                ins_query = "insert into pnl_sales_report_preview_line (tanggal, so_id, no_penjualan, pelanggan, sales_person," \
                            "product_id,uom_id,qty,harga_beli,harga_jual,total_beli,total_jual,profit,persentase," \
                            "create_uid,pnl_sales_preview_id) values {_values}".format(_values=ins_values)
                self._cr.execute(ins_query)
                self._cr.commit()

        form_view_id= self.env['ir.model.data']._xmlid_to_res_id('ati_pbf_sale.pnl_sale_report_form_view_id')
        return {
            'name': new_header.name,
            'view_type': 'form',
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
            'res_model': 'pnl.sales.report.preview',
            'views': [[form_view_id, 'form']],
            'res_id': new_header.id
        }

    def func_print_excel(self):
        vals_header = {
            "name": 'Laporan Laba/Rugi Penjualan Per Sales Produk',
            "start_date": self.start_date,
            "end_date": self.end_date,
            "salesperson": self.salesperson.id
        }
        new_header = self.env['wizard.pnl.sale.sales'].sudo().create(vals_header)
        if self.salesperson:
            self._cr.execute("""(
                select
                    b.date_order as tanggal,
                    b.id as so_id,
                    a.id as sale_line_id,
                    b.name as no_penjualan,
                    b.partner_id as pelanggan,
                    e.name as sales_person,
                    g.product_id as product_id,
                    g.product_uom_id as uom_id,
                    g.quantity as qty,
                    d.hna as harga_beli,
                    (coalesce(d.hna*g.quantity,0)) as total_beli,
                    g.price_subtotal as total_jual,
                    g.harga_satuan as harga_jual
                    from sale_order_line a
                    join sale_order b on b.id = a.order_id
                    join product_product c on c.id = a.product_id
                    join product_template d on d.id = c.product_tmpl_id
                    join hr_employee e on e.id = b.sales_person
                    join sale_order_line_invoice_rel f on f.order_line_id = a.id
                    join account_move_line g on g.id = f.invoice_line_id
                    join account_move h on h.id = g.move_id
                    where b.sales_person = {_salesperson} and h.invoice_date::TIMESTAMP::DATE >= '{_start_date}' and
                    h.invoice_date::TIMESTAMP::DATE <= '{_end_date}' and h.state in ('draft','approval','posted')
            )""".format(_salesperson=self.salesperson.id,_start_date=str(self.start_date),_end_date=str(self.end_date)))
        else:
            self._cr.execute("""(
                            select
                                b.date_order as tanggal,
                                b.id as so_id,
                                a.id as sale_line_id,
                                b.name as no_penjualan,
                                b.partner_id as pelanggan,
                                e.name as sales_person,
                                g.product_id as product_id,
                                g.product_uom_id as uom_id,
                                g.quantity as qty,
                                d.hna as harga_beli,
                                (coalesce(d.hna*g.quantity,0)) as total_beli,
                                g.price_subtotal as total_jual,
                                g.harga_satuan as harga_jual
                                from sale_order_line a
                                join sale_order b on b.id = a.order_id
                                join product_product c on c.id = a.product_id
                                join product_template d on d.id = c.product_tmpl_id
                                join hr_employee e on e.id = b.sales_person
                                join sale_order_line_invoice_rel f on f.order_line_id = a.id
                                join account_move_line g on g.id = f.invoice_line_id
                                join account_move h on h.id = g.move_id
                                where h.invoice_date::TIMESTAMP::DATE >= '{_start_date}' and
                                h.invoice_date::TIMESTAMP::DATE <= '{_end_date}' and h.state in ('draft','approval','posted')
                        )""".format(_start_date=str(self.start_date), _end_date=str(self.end_date)))
        data_preview = self._cr.dictfetchall()
        if len(data_preview) > 0 :
            uid = self._uid
            for data in data_preview:
                so_line = self.env['sale.order.line'].sudo().search([
                    ('id', '=', data['sale_line_id'])
                ])
                harga_jual = round(data['harga_jual'], 2)
                if harga_jual != 0:
                    harga_beli = data['harga_beli']
                    total_beli = data['total_beli']
                else:
                    harga_beli = 0
                    total_beli = 0
                # total_jual = round(harga_jual * data['qty'], 2)
                total_jual = data['total_jual']
                profit = total_jual - total_beli
                # persentase = profit / 100
                if total_beli > 0:
                    persentase = profit / total_beli * 100
                elif harga_jual == 0:
                    persentase = 0
                else:
                    persentase = 100
                ins_values = ",".join(["('{}',{},'{}',{},'{}',{},{},{},{},{},{},{},{},{},{},{})".format(
                    data['tanggal'] or '',
                    data['so_id'] or 'Null',
                    data['no_penjualan'] or '',
                    data['pelanggan'] or '',
                    data['sales_person'] or '',
                    data['product_id'] or 'Null',
                    data['uom_id'] or 'Null',
                    round(data['qty'] or 0, 2),
                    round(harga_beli or 0, 2),
                    round(harga_jual or 0, 2),
                    round(total_beli or 0, 2),
                    round(total_jual or 0, 2),
                    round(profit or 0, 2),
                    round(persentase or 0, 2),
                    uid,
                    new_header.id
                )])
                ins_query = "insert into wizard_pnl_sale_sales_line (tanggal, so_id, no_penjualan, pelanggan,sales_person," \
                            "product_id,uom_id,qty,harga_beli,harga_jual,total_beli,total_jual,profit,persentase," \
                            "create_uid,wizard_pnl_sales_id) values {_values}".format(_values=ins_values)
                self._cr.execute(ins_query)
                self._cr.commit()
        return {
            'type': 'ir.actions.act_url',
            'url' : '/pnl_sales_report/%s' % (new_header.id),
            'target' : 'new',
        }

class wizard_pnl_sale_sales_line(models.TransientModel):
    _name = 'wizard.pnl.sale.sales.line'

    wizard_pnl_sales_id = fields.Many2one('wizard.pnl.sale.sales', string='Wizard Pnl Sales Id')
    tanggal = fields.Date(string='Tanggal')
    so_id = fields.Many2one('sale.order', string='So Id')
    no_penjualan = fields.Char(string='No. Penjualan')
    sales_person = fields.Char(string='Sales Person')
    no_order = fields.Char(string='No. Order')
    pelanggan = fields.Many2one('res.partner', string='Pelanggan')
    product_id = fields.Many2one('product.product', string='Barang')
    uom_id = fields.Many2one('uom.uom', string='Satuan')
    qty = fields.Float(string='QTY', default=0.0)
    harga_beli = fields.Float(string='Harga Beli', default=0.0)
    harga_jual = fields.Float(string='Harga Jual')
    total_beli = fields.Float(string='Total Beli')
    total_jual = fields.Float(string='Total Jual')
    profit = fields.Float(string='Profit')
    persentase = fields.Float(string='Persentase')

class WizardPnlProfitSales(models.TransientModel):
    _name = 'wizard.pnl.profit.sales'
    _description = 'Wizard PNL Profit sales'

    # sales_person = fields.Many2one('res.users', string='Sales Person (*)', index=True, tracking=1)
    name = fields.Char(string='Name', default='Rekap Penjualan Profit Sales')
    salesperson = fields.Many2one('hr.employee', string='Sales Person')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    wizard_pnl_profit_ids = fields.One2many('wizard.pnl.profit.sales.line', 'wizard_pnl_profit_id', string='Wizard Pnl Profit Ids')


    def func_insert_data_preview(self):
        vals_header = {
            "name": 'Rekap Penjualan Profit Sales',
            "start_date": self.start_date,
            "end_date": self.end_date,
            "sales": 'All Sales Person',
            "sales_person": self.salesperson.id
        }
        new_header = self.env['pnl.profit.report.preview'].sudo().create(vals_header)
        if self.salesperson :
            self._cr.execute("""(
                select
                    x.sales_person as sales_person,
                    sum(x.total_beli) as total_beli,
                    sum(x.total_jual) as total_jual,
                --    sum(x.profit) as profit,
                    sum(x.total_jual - x.total_beli) as profit,
                    case
                        when sum(x.total_beli) > 0 then
                        (sum(x.total_jual - x.total_beli))/sum(x.total_beli)*100
                        else 0
                    end as persentase
                --    sum(x.persentase) as persentase
                    from
                    (select
                    e.name as sales_person,
                    case
                        when g.price_subtotal > 0 and d.hna > 0 then
                        (coalesce(d.hna*g.quantity,0))
                        else 0
                    end as total_beli,
                    case 
                        when g.price_subtotal > 0 then
                        g.price_subtotal
                        else 0
                    end as total_jual
                --    case
                --        when a.price_subtotal > 0 and d.hna > 0 then
                --        (g.harga_satuan * g.quantity) - (coalesce(d.hna*g.quantity,0))
                --        else 0
                --    end as profit,
                --    case
                --        when a.price_subtotal > 0 and d.hna >0 then
                --            (((g.harga_satuan * g.quantity) - (coalesce(d.hna*g.quantity,0))) / ((coalesce(d.hna,0))*(coalesce(g.quantity,0))))*100
                --        else 0
                --    end as persentase
                    from sale_order_line a
                    join sale_order b on b.id = a.order_id
                    join product_product c on c.id = a.product_id
                    join product_template d on d.id = c.product_tmpl_id
                    join hr_employee e on e.id = b.sales_person
                    join sale_order_line_invoice_rel f on f.order_line_id = a.id
                    join account_move_line g on g.id = f.invoice_line_id
                    join account_move h on h.id = g.move_id
                where h.invoice_date::TIMESTAMP::DATE >= '{_start_date}' and
                    h.invoice_date::TIMESTAMP::DATE <= '{_end_date}' and b.sales_person = {_sales_person} and h.state in ('draft','approval','posted')
                ) x
                group by
                x.sales_person
            )""".format(_sales_person=self.salesperson.id,_start_date=str(self.start_date),_end_date=str(self.end_date)))

        else:
            self._cr.execute("""(
                            select
                                x.sales_person as sales_person,
                                sum(x.total_beli) as total_beli,
                                sum(x.total_jual) as total_jual,
                            --    sum(x.profit) as profit,
                                sum(x.total_jual - x.total_beli) as profit,
                                case
                                    when sum(x.total_beli) > 0 then
                                    (sum(x.total_jual - x.total_beli))/sum(x.total_beli)*100
                                    else 0
                                end as persentase
                            --    sum(x.persentase) as persentase
                                from
                                (select
                                e.name as sales_person,
                                case
                                    when g.price_subtotal > 0 and d.hna > 0 then
                                    (coalesce(d.hna*g.quantity,0))
                                    else 0
                                end as total_beli,
                                case 
                                    when g.price_subtotal > 0 then
                                    g.price_subtotal
                                    else 0
                                end as total_jual
                            --    case
                            --        when a.price_subtotal > 0 and d.hna > 0 then
                            --        (g.harga_satuan * g.quantity) - (coalesce(d.hna*g.quantity,0))
                            --        else 0
                            --    end as profit,
                            --    case
                            --        when a.price_subtotal > 0 and d.hna >0 then
                            --            (((g.harga_satuan * g.quantity) - (coalesce(d.hna*g.quantity,0))) / ((coalesce(d.hna,0))*(coalesce(g.quantity,0))))*100
                            --        else 0
                            --    end as persentase
                                from sale_order_line a
                                join sale_order b on b.id = a.order_id
                                join product_product c on c.id = a.product_id
                                join product_template d on d.id = c.product_tmpl_id
                                join hr_employee e on e.id = b.sales_person
                                join sale_order_line_invoice_rel f on f.order_line_id = a.id
                                join account_move_line g on g.id = f.invoice_line_id
                                join account_move h on h.id = g.move_id
                            where h.invoice_date::TIMESTAMP::DATE >= '{_start_date}' and
                                h.invoice_date::TIMESTAMP::DATE <= '{_end_date}' and h.state in ('draft','approval','posted')
                            ) x
                            group by
                            x.sales_person
                        )""".format(_start_date=str(self.start_date),_end_date=str(self.end_date)))
        data_preview = self._cr.dictfetchall()
        if len(data_preview) > 0 :
            uid = self._uid
            for data in data_preview:
                if data['total_beli'] > 0:
                    persentase = data['profit'] / data['total_beli'] * 100
                else :
                    persentase = 0
                ins_values = ",".join(["('{}',{},{},{},{},{},{})".format(
                    data['sales_person'] or '',
                    round(data['total_beli'] or 0, 2),
                    round(data['total_jual'] or 0, 2),
                    round(data['profit'] or 0, 2),
                    round(persentase or 0, 2),
                    uid,
                    new_header.id
                )])
                ins_query = "insert into pnl_profit_report_preview_line (sales_person," \
                            "total_beli,total_jual,profit,persentase," \
                            "create_uid,pnl_profit_preview_id) values {_values}".format(_values=ins_values)
                self._cr.execute(ins_query)
                self._cr.commit()

        form_view_id= self.env['ir.model.data']._xmlid_to_res_id('ati_pbf_sale.pnl_profit_report_form_view_id')
        return {
            'name': new_header.name,
            'view_type': 'form',
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
            'res_model': 'pnl.profit.report.preview',
            'views': [[form_view_id, 'form']],
            'res_id': new_header.id
        }

    def func_print_profit_excel(self):
        vals_header = {
            "name": 'Rekap Penjualan Profit Sales',
            "start_date": self.start_date,
            "end_date": self.end_date,
            "salesperson": self.salesperson.id
        }
        new_header = self.env['wizard.pnl.profit.sales'].sudo().create(vals_header)
        if self.salesperson:
            self._cr.execute("""(
                select
                    x.sales_person as sales_person,
                    sum(x.total_beli) as total_beli,
                    sum(x.total_jual) as total_jual,
                --    sum(x.profit) as profit,
                    sum(x.total_jual - x.total_beli) as profit,
                    case
                        when sum(x.total_beli) > 0 then
                        (sum(x.total_jual - x.total_beli))/sum(x.total_beli)*100
                        else 0
                    end as persentase
                --    sum(x.persentase) as persentase
                    from
                    (select
                    e.name as sales_person,
                    case
                        when g.price_subtotal > 0 and d.hna > 0 then
                        (coalesce(d.hna*g.quantity,0))
                        else 0
                    end as total_beli,
                    case 
                        when g.price_subtotal > 0 then
                        g.price_subtotal
                        else 0
                    end as total_jual
                --    case
                --        when a.price_subtotal > 0 and d.hna > 0 then
                --        (g.harga_satuan * g.quantity) - (coalesce(d.hna*g.quantity,0))
                --        else 0
                --    end as profit,
                --    case
                --        when a.price_subtotal > 0 and d.hna >0 then
                --            (((g.harga_satuan * g.quantity) - (coalesce(d.hna*g.quantity,0))) / ((coalesce(d.hna,0))*(coalesce(g.quantity,0))))*100
                --        else 0
                --    end as persentase
                    from sale_order_line a
                    join sale_order b on b.id = a.order_id
                    join product_product c on c.id = a.product_id
                    join product_template d on d.id = c.product_tmpl_id
                    join hr_employee e on e.id = b.sales_person
                    join sale_order_line_invoice_rel f on f.order_line_id = a.id
                    join account_move_line g on g.id = f.invoice_line_id
                    join account_move h on h.id = g.move_id
                where h.invoice_date::TIMESTAMP::DATE >= '{_start_date}' and
                    h.invoice_date::TIMESTAMP::DATE <= '{_end_date}' and b.sales_person = {_salesperson} and h.state in ('draft','approval','posted')
                ) x
                group by
                x.sales_person
            )""".format(_salesperson=self.salesperson.id,_start_date=str(self.start_date),_end_date=str(self.end_date)))
        else:
            self._cr.execute("""(
                            select
                                x.sales_person as sales_person,
                                sum(x.total_beli) as total_beli,
                                sum(x.total_jual) as total_jual,
                            --    sum(x.profit) as profit,
                                sum(x.total_jual - x.total_beli) as profit,
                                case
                                    when sum(x.total_beli) > 0 then
                                    (sum(x.total_jual - x.total_beli))/sum(x.total_beli)*100
                                    else 0
                                end as persentase
                            --    sum(x.persentase) as persentase
                                from
                                (select
                                e.name as sales_person,
                                case
                                    when g.price_subtotal > 0 and d.hna > 0 then
                                    (coalesce(d.hna*g.quantity,0))
                                    else 0
                                end as total_beli,
                                case 
                                    when g.price_subtotal > 0 then
                                    g.price_subtotal
                                    else 0
                                end as total_jual
                            --    case
                            --        when a.price_subtotal > 0 and d.hna > 0 then
                            --        (g.harga_satuan * g.quantity) - (coalesce(d.hna*g.quantity,0))
                            --        else 0
                            --    end as profit,
                            --    case
                            --        when a.price_subtotal > 0 and d.hna >0 then
                            --            (((g.harga_satuan * g.quantity) - (coalesce(d.hna*g.quantity,0))) / ((coalesce(d.hna,0))*(coalesce(g.quantity,0))))*100
                            --        else 0
                            --    end as persentase
                                from sale_order_line a
                                join sale_order b on b.id = a.order_id
                                join product_product c on c.id = a.product_id
                                join product_template d on d.id = c.product_tmpl_id
                                join hr_employee e on e.id = b.sales_person
                                join sale_order_line_invoice_rel f on f.order_line_id = a.id
                                join account_move_line g on g.id = f.invoice_line_id
                                join account_move h on h.id = g.move_id
                            where h.invoice_date::TIMESTAMP::DATE >= '{_start_date}' and
                                h.invoice_date::TIMESTAMP::DATE <= '{_end_date}' and h.state in ('draft','approval','posted')
                            ) x
                            group by
                            x.sales_person
                        )""".format(_start_date=str(self.start_date), _end_date=str(self.end_date)))
        data_preview = self._cr.dictfetchall()
        if len(data_preview) > 0 :
            uid = self._uid
            for data in data_preview:
                if data['total_beli'] > 0:
                    persentase = data['profit'] / data['total_beli'] * 100
                else:
                    persentase = 0
                ins_values = ",".join(["('{}',{},{},{},{},{},{})".format(
                    data['sales_person'] or '',
                    round(data['total_beli'] or 0, 2),
                    round(data['total_jual'] or 0, 2),
                    round(data['profit'] or 0, 2),
                    round(persentase or 0, 2),
                    uid,
                    new_header.id
                )])
                ins_query = "insert into wizard_pnl_profit_sales_line (sales_person," \
                            "total_beli,total_jual,profit,persentase," \
                            "create_uid,wizard_pnl_profit_id) values {_values}".format(_values=ins_values)
                self._cr.execute(ins_query)
                self._cr.commit()
        return {
            'type': 'ir.actions.act_url',
            'url' : '/pnl_profit_report/%s' % (new_header.id),
            'target' : 'new',
        }

class wizard_pnl_sale_sales_line(models.TransientModel):
    _name = 'wizard.pnl.profit.sales.line'

    wizard_pnl_profit_id = fields.Many2one('wizard.pnl.profit.sales', string='Wizard Pnl Profit Id')
    sales_person = fields.Char(string='Sales Person')
    total_beli = fields.Float(string='Total Beli')
    total_jual = fields.Float(string='Total Jual')
    profit = fields.Float(string='Profit')
    persentase = fields.Float(string='Persentase')