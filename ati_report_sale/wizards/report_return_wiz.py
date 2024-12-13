from odoo import models, fields, api, exceptions, _
 
class x_report_return(models.TransientModel):
    _name = 'x.report.return.xml'
 
 
    # so_id = fields.Many2many('sale.order', string='Sale Order')
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")

    def new_get_report(self):
        self.with_context(start_date=self.start_date, end_date=self.end_date).get_excel_report_return()
 
    def get_excel_report_return(self):
        # redirect ke controller /sale/excel_report untuk generate file excel
        #code by adelia
        return {
            'type': 'ir.actions.act_url',
            'url': '/return/excel_report/%s' % (self.id),
            'target': 'new',
        }