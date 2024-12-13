from odoo import fields, models, api, _
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    from odoo.addons.setu_advance_inventory_reports.library import xlsxwriter

from . import setu_excel_formatter
import base64
from io import BytesIO

class SetuInventoryFSNAnalysisReport(models.TransientModel):
    _name = 'setu.inventory.fsn.analysis.report'
    _description = """
        Inventory FSN Analysis Report
            This classification is based on the consumption pattern of the materials i.e. movement analysis forms the basis. 
            Here the items are classified into fast moving, slow moving and non-moving on the basis of frequency of transaction. 
            FSN analysis is especially useful to combat obsolete items whether spare parts are raw materials or components.
    """

    stock_file_data = fields.Binary('Stock Movement File')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    company_ids = fields.Many2many("res.company", string="Companies")
    product_category_ids = fields.Many2many("product.category", string="Product Categories")
    product_ids = fields.Many2many("product.product", string="Products")
    warehouse_ids = fields.Many2many("stock.warehouse", string="Warehouses")
    stock_movement_type = fields.Selection([('all', 'All'),
                                            ('fast', 'Fast Moving'),
                                            ('slow', 'Slow Moving'),
                                            ('non', 'Non Moving'),
                                            ('medium', 'Medium Moving')], "FSN Classification", default="all")

    @api.onchange('product_category_ids')
    def onchange_product_category_id(self):
        if self.product_category_ids:
            return {'domain' : { 'product_ids' : [('categ_id','child_of', self.product_category_ids.ids)] }}

    @api.onchange('company_ids')
    def onchange_company_id(self):
        if self.company_ids:
            return {'domain' : { 'warehouse_ids' : [('company_id','child_of', self.company_ids.ids)] }}

    def get_file_name(self):
        filename = "inventory_fsn_analysis_report.xlsx"
        return filename

    def create_excel_workbook(self, file_pointer):
        workbook = xlsxwriter.Workbook(file_pointer)
        return workbook

    def create_excel_worksheet(self, workbook, sheet_name):
        worksheet = workbook.add_worksheet(sheet_name)
        worksheet.set_default_row(22)
        # worksheet.set_border()
        return worksheet

    def set_column_width(self, workbook, worksheet):
        worksheet.set_column(0, 0, 14)
        worksheet.set_column(1, 3, 25)
        worksheet.set_column(4, 7, 14)
        worksheet.set_column(8, 8, 20)
        worksheet.set_column(9, 9, 16)
        worksheet.set_column(10, 10, 14)
        worksheet.set_column(11, 11, 20)

    def set_format(self, workbook, wb_format):
        wb_new_format = workbook.add_format(wb_format)
        wb_new_format.set_border()
        return wb_new_format

    def set_report_title(self, workbook, worksheet):
        wb_format = self.set_format(workbook, setu_excel_formatter.FONT_TITLE_CENTER)
        worksheet.merge_range(0, 0, 1, 7, "Inventory FSN Analysis Report", wb_format)
        wb_format_left = self.set_format(workbook, setu_excel_formatter.FONT_MEDIUM_BOLD_LEFT)
        wb_format_center = self.set_format(workbook, setu_excel_formatter.FONT_MEDIUM_BOLD_CENTER)

        worksheet.write(2, 0, "Report Start Date", wb_format_left)
        worksheet.write(3, 0, "Report End Date", wb_format_left)

        wb_format_center = self.set_format(workbook, {'num_format': 'dd/mm/yy', 'align' : 'center', 'bold':True ,'font_color' : 'red'})
        worksheet.write(2, 1, self.start_date, wb_format_center)
        worksheet.write(3, 1, self.end_date, wb_format_center)

    def get_inventory_fsn_analysis_report_data(self):
        """
        :return:
        """
        start_date = self.start_date
        end_date = self.end_date
        start_datetime = str(self.start_date) + ' 00:00:00'
        end_datetime = str(self.end_date) + ' 24:00:00'
        category_ids = company_ids = {}
        if self.product_category_ids:
            categories = self.env['product.category'].search([('id','child_of',self.product_category_ids.ids)])
            category_ids = set(categories.ids) or {}
        products = self.product_ids and set(self.product_ids.ids) or {}

        if self.company_ids:
            companies = self.env['res.company'].search([('id','child_of',self.company_ids.ids)])
            company_ids = set(companies.ids) or {}
        else:
            company_ids = set(self.env.context.get('allowed_company_ids',False) or self.env.user.company_ids.ids) or {}

        warehouses = self.warehouse_ids and set(self.warehouse_ids.ids) or {}

        # get_products_overstock_data(company_ids, product_ids, category_ids, warehouse_ids, start_date, end_date, advance_stock_days)
        # query = """
        #         Select * from get_inventory_fsn_analysis_report('%s','%s','%s','%s','%s','%s', '%s')
        #     """%(company_ids, products, category_ids, warehouses, start_date, end_date, self.stock_movement_type)
        # print(query)
        query = """
                SELECT
                    *,
                    --case when turnover_ratio = 0 then 0
                        --else days/turnover_ratio end as dayss,
                    -- case when turnover_ratio = 0 then 0
                        --when hna > 0 then (average_stock*days)/hna
                         --else 0 end as dayss,
                    case when turnover_ratio = 0 then 0
                        else days/turnover_ratio end as dayss,
                    case when turnover_ratio > 3 then 'Fast Moving'
                        when turnover_ratio > 1 and turnover_ratio <= 3 then 'Medium Moving'
                        when turnover_ratio > 0 and turnover_ratio <= 1 then 'Slow Moving'
                        when turnover_ratio <= 0 then 'Non Moving' 
                    end as fsn_class
                FROM
                (
                    select 
                        fsn.product_id,
                        pt.sku,
                        pt.hna,
                        (select name from jenis_obat where id = pt.jenis_obat limit 1) as golongan_obat,
                        fsn.product_name,
                        fsn.product_category_id,
                        fsn.category_name,
                -- 		warehouse_id,
                -- 		fsn.warehouse_name,
                        sum(COALESCE(opening_stock,0)) opening_stock,
                        sum(COALESCE(opening_stock,0)) + sum(COALESCE(po_stock.op_stock,0)) as total_stock,
                        sum(COALESCE(closing_stock,0)) closing_stock,
                        sum(COALESCE(opening_stock,0)) + sum(COALESCE(po_stock.op_stock,0)) - sum(COALESCE(closing_stock,0)) as cogs,
                        sum(fsn.average_stock) average_stock,
                        case when sum(fsn.average_stock) = 0 then 0
                            else ROUND((sum(COALESCE(opening_stock,0)) + sum(COALESCE(po_stock.op_stock,0)) - sum(COALESCE(closing_stock,0)))/sum(fsn.average_stock), 5) end as turnover_ratio,
                        DATE_PART('day', '%s'::timestamp - '%s'::timestamp) as days
                    from 
                        get_inventory_fsn_analysis_report('%s','%s','%s','%s','%s','%s', '%s') fsn
                        join product_product pp on fsn.product_id = pp.id
                        join product_template pt on pp.product_tmpl_id = pt.id
                        left join (
                            select
                                    cmp_id, company_name, p_id, product_name, categ_id, category_name, wh_id, warehouse_name, sum(product_qty) as op_stock
                            From
                            (
                                select
                                        T.company_id as cmp_id, T.company_name,
                                        T.product_id as p_id, T.product_name,
                                        T.product_category_id as categ_id, T.category_name,
                                        T.warehouse_id as wh_id, T.warehouse_name,
                                        product_qty
                                from get_stock_data('%s','%s','%s','%s', 'purchase' ,'%s','%s') T 
                                union all
                                select
                                        T.company_id as cmp_id, T.company_name,
                                        T.product_id as p_id, T.product_name,
                                        T.product_category_id as categ_id, T.category_name,
                                        T.warehouse_id as wh_id, T.warehouse_name,
                                        product_qty
                                from get_stock_data('%s','%s','%s','%s', 'sales_return' ,'%s','%s') T 
                                union all
                                select
                                        T.company_id as cmp_id, T.company_name,
                                        T.product_id as p_id, T.product_name,
                                        T.product_category_id as categ_id, T.category_name,
                                        T.warehouse_id as wh_id, T.warehouse_name,
                                        product_qty
                                from get_stock_data('%s','%s','%s','%s', 'adjustment_in' ,'%s','%s') T 
                                union all
                                select
                                        T.company_id as cmp_id, T.company_name,
                                        T.product_id as p_id, T.product_name,
                                        T.product_category_id as categ_id, T.category_name,
                                        T.warehouse_id as wh_id, T.warehouse_name,
                                        product_qty
                                from get_stock_data('%s','%s','%s','%s', 'transit_in' ,'%s','%s') T 
                                union all
                                select
                                        T.company_id as cmp_id, T.company_name,
                                        T.product_id as p_id, T.product_name,
                                        T.product_category_id as categ_id, T.category_name,
                                        T.warehouse_id as wh_id, T.warehouse_name,
                                        product_qty
                                from get_stock_data('%s','%s','%s','%s', 'production_in' ,'%s','%s') T 
                                union all
                                select
                                        T.company_id as cmp_id, T.company_name,
                                        T.product_id as p_id, T.product_name,
                                        T.product_category_id as categ_id, T.category_name,
                                        T.warehouse_id as wh_id, T.warehouse_name,
                                        product_qty
                                from get_stock_data('%s','%s','%s','%s', 'internal_in' ,'%s','%s') T 
                            )T
                            group by cmp_id, company_name, p_id, product_name, categ_id, category_name, wh_id, warehouse_name
                        ) po_stock on po_stock.p_id = fsn.product_id and po_stock.categ_id = fsn.product_category_id and po_stock.wh_id = fsn.warehouse_id
                -- 	where product_id = 15
                    group by 
                        product_id,
                        pt.sku,
                        pt.hna,
                        pt.jenis_obat,
                        fsn.product_name,
                        product_category_id,
                        fsn.category_name
                ) x
                where
                1 = case when '%s' = 'all' then 1
                else
                    case when '%s' = 'fast' then case when turnover_ratio > 0 and days/turnover_ratio between 1 and 31 then 1 else 0 end
                    else
                        case when '%s' = 'medium' then case when turnover_ratio > 0 and days/turnover_ratio between 32 and 89 then 1 else 0 end
                        else
                            case when '%s' = 'slow' then case when turnover_ratio > 0 and days/turnover_ratio >= 90 then 1 else 0 end
                            else
                                case when '%s' = 'non' then case when turnover_ratio <= 0 then 1 else 0 end
                                else 0 end
                            end
                        end
                    end
                end

            """ % (end_datetime, start_datetime, company_ids, products, category_ids, warehouses, start_date, end_date, 
            self.stock_movement_type, company_ids, products, category_ids, warehouses, start_date, end_date, company_ids, 
            products, category_ids, warehouses, start_date, end_date, company_ids, products, category_ids, warehouses, 
            start_date, end_date, company_ids, products, category_ids, warehouses, start_date, end_date, company_ids, 
            products, category_ids, warehouses, start_date, end_date, company_ids, products, category_ids, warehouses, 
            start_date, end_date, self.stock_movement_type, self.stock_movement_type, self.stock_movement_type, self.stock_movement_type, self.stock_movement_type)
        # print(query)
        self._cr.execute(query)
        stock_data = self._cr.dictfetchall()
        # print("\nstock_data", stock_data)
        # xx
        return stock_data

    def prepare_data_to_write(self, stock_data={}):
        """

        :param stock_data:
        :return:
        """
        warehouse_wise_data = {}
        for data in stock_data:
            key = (data.get('warehouse_id'), data.get('warehouse_name'))
            if not warehouse_wise_data.get(key,False):
                warehouse_wise_data[key] = {data.get('product_id') : data}
            else:
                warehouse_wise_data.get(key).update({data.get('product_id') : data})
        return warehouse_wise_data

    def download_report(self):
        # print("1111")
        file_name = self.get_file_name()
        file_pointer = BytesIO()
        stock_data = self.get_inventory_fsn_analysis_report_data()
        warehouse_wise_analysis_data = self.prepare_data_to_write(stock_data=stock_data)
        if not warehouse_wise_analysis_data:
            return False
        workbook = self.create_excel_workbook(file_pointer)
        for stock_data_key, stock_data_value in warehouse_wise_analysis_data.items():
            sheet_name = stock_data_key[1]
            wb_worksheet = self.create_excel_worksheet(workbook, sheet_name)
            row_no = 5
            self.write_report_data_header(workbook, wb_worksheet, row_no)
            for fsn_data_key, fsn_data_value in stock_data_value.items():
                row_no = row_no + 1
                self.write_data_to_worksheet(workbook, wb_worksheet, fsn_data_value, row=row_no)

        # workbook.save(file_name)
        workbook.close()
        file_pointer.seek(0)
        # file_data = base64.encodestring(file_pointer.read())
        file_data = base64.encodebytes(file_pointer.read())
        self.write({'stock_file_data' : file_data})
        file_pointer.close()

        return {
            'name' : 'Inventory FSN Analysis Report',
            'type' : 'ir.actions.act_url',
            'url': '/web/binary/setu_download_document?model=setu.inventory.fsn.analysis.report&field=stock_file_data&id=%s&filename=%s'%(self.id, file_name),
            'target': 'self',
        }

    def download_report_in_listview(self):
        stock_data = self.get_inventory_fsn_analysis_report_data()
        for fsn_data_value in stock_data:
            fsn_data_value['wizard_id'] = self.id
            self.create_data(fsn_data_value)

        graph_view_id = self.env.ref('setu_advance_inventory_reports.setu_inventory_fsn_analysis_bi_report_graph').id
        tree_view_id = self.env.ref('setu_advance_inventory_reports.setu_inventory_fsn_analysis_bi_report_tree').id
        is_graph_first = self.env.context.get('graph_report',False)
        report_display_views = []
        viewmode = ''
        if is_graph_first:
            report_display_views.append((graph_view_id, 'graph'))
            report_display_views.append((tree_view_id, 'tree'))
            viewmode="graph,tree"
        else:
            report_display_views.append((tree_view_id, 'tree'))
            report_display_views.append((graph_view_id, 'graph'))
            viewmode="tree,graph"
        return {
            'name': _('Inventory FSN Analysis'),
            'domain': [('wizard_id', '=', self.id)],
            'res_model': 'setu.inventory.fsn.analysis.bi.report',
            'view_mode': viewmode,
            'type': 'ir.actions.act_window',
            'views': report_display_views,
        }

    def create_data(self, data):
        del data['company_name']
        del data['product_name']
        del data['warehouse_name']
        del data['category_name']
        return self.env['setu.inventory.fsn.analysis.bi.report'].create(data)

    def write_report_data_header(self, workbook, worksheet, row):
        self.set_report_title(workbook,worksheet)
        self.set_column_width(workbook, worksheet)
        wb_format = self.set_format(workbook, setu_excel_formatter.FONT_MEDIUM_BOLD_CENTER)
        wb_format.set_text_wrap()
        odd_normal_right_format = self.set_format(workbook, setu_excel_formatter.ODD_FONT_MEDIUM_BOLD_RIGHT)
        even_normal_right_format = self.set_format(workbook, setu_excel_formatter.EVEN_FONT_MEDIUM_BOLD_RIGHT)
        normal_left_format = self.set_format(workbook, setu_excel_formatter.FONT_MEDIUM_BOLD_LEFT)

        worksheet.write(row, 0, 'No PLU', normal_left_format)
        worksheet.write(row, 1, 'Product Name', normal_left_format)
        worksheet.write(row, 2, 'Category', normal_left_format)
        worksheet.write(row, 3, 'Golongan Obat', normal_left_format)
        worksheet.write(row, 4, 'Stock Awal', odd_normal_right_format)
        worksheet.write(row, 5, 'Total Stock', even_normal_right_format)
        worksheet.write(row, 6, 'Stock Akhir', odd_normal_right_format)
        worksheet.write(row, 7, 'COGS', even_normal_right_format)
        worksheet.write(row, 8, 'Rata - Rata Persediaan', odd_normal_right_format)
        worksheet.write(row, 9, 'Turnover Ratio', even_normal_right_format)
        worksheet.write(row, 10, 'Days', odd_normal_right_format)
        worksheet.write(row, 11, 'FSN Classification', even_normal_right_format)

        return worksheet

    def write_data_to_worksheet(self, workbook, worksheet, data, row):
        # Start from the first cell. Rows and
        # columns are zero indexed.
        odd_normal_right_format = self.set_format(workbook, setu_excel_formatter.ODD_FONT_MEDIUM_NORMAL_RIGHT)
        even_normal_right_format = self.set_format(workbook, setu_excel_formatter.EVEN_FONT_MEDIUM_NORMAL_RIGHT)
        even_normal_center_format = self.set_format(workbook, setu_excel_formatter.EVEN_FONT_MEDIUM_NORMAL_CENTER)
        odd_normal_left_format = self.set_format(workbook, setu_excel_formatter.ODD_FONT_MEDIUM_NORMAL_LEFT)
        normal_left_format = self.set_format(workbook, setu_excel_formatter.FONT_MEDIUM_NORMAL_LEFT)
        worksheet.write(row, 0, data.get('sku',''), normal_left_format)
        worksheet.write(row, 1, data.get('product_name',''), normal_left_format)
        worksheet.write(row, 2, data.get('category_name',''), normal_left_format)
        worksheet.write(row, 3, data.get('golongan_obat',''), normal_left_format)
        worksheet.write(row, 4, data.get('opening_stock',''), odd_normal_right_format)
        worksheet.write(row, 5, data.get('total_stock',''), even_normal_right_format)
        worksheet.write(row, 6, data.get('closing_stock',''), odd_normal_right_format)
        worksheet.write(row, 7, data.get('cogs',''), even_normal_right_format)
        worksheet.write(row, 8, data.get('average_stock',''), odd_normal_right_format)
        worksheet.write(row, 9, data.get('turnover_ratio',''), even_normal_right_format)
        worksheet.write(row, 10, data.get('dayss',''), odd_normal_right_format)
        worksheet.write(row, 11, data.get('fsn_class',''), even_normal_center_format)
        return worksheet

class SetuInventoryFSNAnalysisBIReport(models.TransientModel):
    _name = 'setu.inventory.fsn.analysis.bi.report'

    product_id = fields.Many2one("product.product", "Product")
    product_category_id = fields.Many2one("product.category", "Category")
    warehouse_id = fields.Many2one("stock.warehouse")
    company_id = fields.Many2one("res.company", "Company")
    opening_stock = fields.Float("Opening Stock")
    closing_stock = fields.Float("Closing Stock")
    average_stock = fields.Float("Average Stock")
    sales = fields.Float("Sales")
    turnover_ratio = fields.Float("Turnover Ratio")
    stock_movement  = fields.Char("FSN Classification")
    wizard_id = fields.Many2one("setu.inventory.fsn.analysis.report")
