from odoo import models, fields, api, exceptions, _


class wizard_po_retur(models.TransientModel):
    _name = 'wizard.po.retur'

    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")


    def get_excel_retur_supplier(self):
        # redirect ke controller /sale/excel_report untuk generate file excel
        return {
            'type': 'ir.actions.act_url',
            'url': '/purchase/retur/excel_report/%s' % (self.id),
            'target': 'new',
        }

