from odoo import fields, models, api, _
from odoo.exceptions import UserError

class WizardVendorPayment(models.TransientModel):
    _name = 'wizard.vendor.payment'
    _description = 'Wizard Vendor Payment Report'

    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    category = fields.Selection([('jabodetabek', 'Jabodetabek'), ('non-jabodetabek', 'Non Jabodetabek')], string='Category')

    def button_generate_excel(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'wizard.vendor.payment'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        return self.env.ref('ati_invoice_payments.wizard_vendor_payment_xlsx').report_action(self, data=datas)