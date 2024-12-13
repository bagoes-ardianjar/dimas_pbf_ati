from odoo import models, fields, api, exceptions, _


class wizard_po(models.TransientModel):
    _name = 'wizard.po'

    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    golongan_obat = fields.Many2one(comodel_name='jenis.obat', string='Golongan Obat')


    def get_excel_report_bpom(self):
        # redirect ke controller /sale/excel_report untuk generate file excel
        return {
            'type': 'ir.actions.act_url',
            'url': '/purchase/excel_report/%s' % (self.id),
            'target': 'new',
        }

