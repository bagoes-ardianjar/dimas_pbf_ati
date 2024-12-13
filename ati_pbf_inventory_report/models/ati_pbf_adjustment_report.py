from odoo import models, fields, api, exceptions, _

class ati_pbf_adjustment_report(models.TransientModel):
    _name = 'ati.pbf.adjustment.report'

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    location_ids = fields.Many2many(comodel_name='stock.location', string='Location')

    def action_print_report_adjustment(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'location_ids': self.location_ids.ids
            },
        }
        # data = {'start_date': self.start_date, 'end_date': self.end_date}
        return self.env.ref('ati_pbf_inventory_report.action_report_adjustment').report_action(self, data=data)

class adjustment_report_template(models.AbstractModel):
    _name = 'report.ati_pbf_inventory_report.adjustment_report_template'

    def _get_report_values(self, docids, data=None):
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        param_location_ids = data['form']['location_ids']
        location_ids = []
        docs = []

        _where = ""
        if start_date and end_date:
            _where = "where DATE(sq.write_date) between '{_start}' and '{_end}' and sq.inventory_quantity_set = False ".format(_start=start_date, _end=end_date)
        # print("param_location_ids", param_location_ids)
        if param_location_ids:
            location_ids = []
            for rec in param_location_ids:
                location_ids.append(rec)
            if len(location_ids) == 1:
                locations = str(tuple(list(set(location_ids))))
                # print(products)
                location = locations.replace(',)', ')')
                # print(product)
                if location:
                    _where += 'and sl.id = {}'.format(location)
            elif len(location_ids) > 1:
                locations = str(tuple(list(set(location_ids))))
                if locations:
                    _where += 'and sl.id IN {}'.format(locations)
        elif not param_location_ids:
            location_ids = []
            self._cr.execute("""select id,name from stock_location where active = true and name != 'Inventory adjustment' ORDER BY id""")
            loc = self._cr.fetchall()
            if loc:
                for x in loc:
                    location_ids.append(x[0])

            if location_ids:
                locations = str(tuple(list(set(location_ids))))
                if locations:
                    _where += 'and sl.id IN {}'.format(locations)


        # print("1", start_date, end_date, location_ids)
        self._cr.execute(
            """
                select 
                    sq.write_date,
                    pt.name,
                    uu.name as uom_name,
                    sl.complete_name as location_name,
                    coalesce(sq.cat_quantity,0) as cat,
                    coalesce(sq.riil_quantity,0) as riil,
                    coalesce(sq.riil_quantity,0) - coalesce(sq.cat_quantity,0) as kor,
                    coalesce(ip.value_float, 0) as hpp_satuan,
                    (coalesce(sq.riil_quantity,0) - coalesce(sq.cat_quantity,0))*coalesce(ip.value_float,0) as hpp_total,
                    x_adjustment_reason as alasan
                from 
                    stock_quant sq
                    join product_product pp on sq.product_id = pp.id
                    join product_template pt on pp.product_tmpl_id = pt.id
                    join uom_uom uu on pt.uom_id = uu.id
                    join stock_location sl on sq.location_id = sl.id
                    left join (
                        select res_id, value_float
                        from ir_property ip 
                        where name = 'standard_price'
                    ) ip on ip.res_id = 'product.product,'||pp.id
                {_where}
                order by 
                    sq.write_date,
                    sl.name
                    
            """.format(_where=_where))
        res_adjustment = self._cr.dictfetchall()

        data = {}
        adjustment_list = []
        if res_adjustment:
            for rec in res_adjustment:
                # if rec.get('cat') > 0 or rec.get('riil') > 0:
                adjustment_list.append({
                    'tanggal': rec.get('write_date'),
                    'nama_barang': rec.get('name'),
                    'satuan': rec.get('uom_name'),
                    'lokasi': rec.get('location_name'),
                    'cat': rec.get('cat'),
                    'riil': rec.get('riil'),
                    'kor': rec.get('kor'),
                    'hpp_satuan': rec.get('hpp_satuan'),
                    'hpp_total': rec.get('kor') * rec.get('hpp_satuan'),
                    'alasan': rec.get('alasan')
                })

        if adjustment_list:
            docs = adjustment_list

        # print("docs", docs)
        result = {
            # 'doc_ids': data['ids'],
            # 'doc_model': data['model'],
            'start_date': start_date,
            'end_date': end_date,
            'docs': docs,
            # 'total_debit_all': total_debit_all,
            # 'total_debit_untaxed_all': total_debit_untaxed_all
        }
        return result