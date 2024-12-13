from odoo import fields, models, api, _
from odoo.exceptions import UserError

class WizardPnlSaleProduct(models.TransientModel):
    _name = 'wizard.pnl.sale.product'
    _description = 'Wizard PNL Sale product'

    product_type = fields.Selection([("all","All"),("active","Active"), ("is_transaction", "Is Transaction")], string='Filter by Product')
    margin_id = fields.Many2one('m.margin', string='Category Customer')
    sales_person = fields.Many2one('hr.employee', string='Sales Person')
    produk_umum = fields.Boolean(sting='Umum')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')

    def button_generate_excel(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'wizard.pnl.sale.product'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        return self.env.ref('ati_pbf_sale.wizard_pnl_sale_product_xlsx').report_action(self, data=datas)
