from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.addons import decimal_precision as dp


class PurchaseOrderAdl(models.Model):
    _inherit = 'purchase.order'
    _description = 'Purchase Order'

    @api.model
    def _get_default_name(self, company_id):
        company_idd = self.env['res.company'].search([('id', '=', company_id)])
        self.env.company = company_idd
        name = self.env["ir.sequence"].next_by_code("purchase.order")
        if not name:
            raise UserError(
                    _("No ir.sequence has been found for code '%s' in company '%s'. Please make sure a sequence is set for current company.")
                    % ('purchase.order', company_idd.name)
                )
        return name


    @api.model
    def create(self, vals):
        company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
        # Ensures default picking type and currency are taken from the right company.
        self_comp = self.with_company(company_id)
        if vals.get('name', 'New') == 'New':
            seq_date = None
            
            if 'date_order' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
            vals['name'] = self_comp.env['ir.sequence'].next_by_code('x.self.po', sequence_date=seq_date) or '/'
        
        vals, partner_vals = self._write_partner_values(vals)
        res = super(PurchaseOrderAdl, self_comp).create(vals)
        name = self_comp._get_default_name(vals.get('company_id'))
        vals["name"] = name
        if name:
            res.sudo().write({'name': name})
        if partner_vals:
            res.sudo().write(partner_vals)  # Because the purchase user doesn't have write on `res.partner`
        return res

    @api.onchange('order_line')
    def onchange_diskon_12(self):
        for rec in self:
            for order in rec.order_line:
                if order.discount_1:

                    dis_1 = (order.ati_price_unit * order.discount_1 / 100)
                    after_dis1= (order.ati_price_unit - dis_1 )
                    dis2=after_dis1 *  order.discount_2 / 100

                    order.amount_disc1=dis_1
                    order.amount_disc2=dis2

class PurchaseOrderLineadl(models.Model):
    _inherit = 'purchase.order.line'

    amount_disc1 = fields.Float('Amount Diskon 1')
    amount_disc2 = fields.Float('Amount Diskon 2')
    total_pembelian_for_report = fields.Float('Total for Report')

    # @api.depends('discount_1')
    # def compute_diskon(self):
    #     for rec in self:
    #         print(rec, '======rec')
    #         if not rec.discount_1:
    #             rec.amount_disc1 = 0
    #             rec.amount_disc2 = 0
    #         if rec.discount_1:
    #             dis_1 = (rec.ati_price_unit * rec.discount_1 / 100)
    #             rec.amount_disc1=dis_1

    #             print(rec.amount_disc1, '=================')
