from odoo import models, fields, api, exceptions, _
 
class x_wizard_history_harga(models.TransientModel):
    _name = 'x.wizard.history.harga.xml'

    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
 
 
    def get_excel_report(self):
        # redirect ke controller /purchase/excel_report untuk generate file excel
        #code by adelia
        return {
            'type': 'ir.actions.act_url',
            'url': '/purchase/history_excel_report/%s' % (self.id),
            'target': 'new',
        }