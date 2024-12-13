from odoo import models, fields, api, exceptions, _
 
class x_report_bpom(models.TransientModel):
    _name = 'x.report.bpom.xml'
 
 
    # so_id = fields.Many2many('sale.order', string='Sale Order')
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    golongan_obat = fields.Many2one(comodel_name='jenis.obat', string='Golongan Obat')
 
 
    def get_excel_report(self):
        # redirect ke controller /sale/excel_report untuk generate file excel
        #code by adelia
        return {
            'type': 'ir.actions.act_url',
            'url': '/sale/excel_report/%s' % (self.id),
            'target': 'new',
        }