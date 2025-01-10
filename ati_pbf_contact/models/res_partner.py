from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError

class res_partner(models.Model):
    _inherit = 'res.partner'
    _description = 'Centralize your address book'

    def write(self, vals):
        res = super(res_partner, self).write(vals)
        if 'margin_ids' in vals:
            for this in self:
                so_line = self.env['sale.order.line'].sudo().search([('order_id.partner_id', '=', this.id)])
                for l in so_line:
                    if l.order_id.state == 'draft':
                        if l.is_lock_price != True:
                            if not this.margin_ids or l.order_id.is_pasien == True:
                                if not l.product_id.margin:
                                    l.product_margin_percent = '0%'
                                else:
                                    l.product_margin_percent = str(l.product_id.margin.name) + '%'
                            else:
                                margin_from_customer = 0
                                for m_margin in this.margin_ids:
                                    margin_from_customer += m_margin.value
                                    l.product_margin_percent = str(margin_from_customer) + '%'
                        else:
                            pass
                    else:
                        pass
        return res

    @api.depends('user_id')
    def _compute_is_pasien_panel_res_partner(self):
        is_panel_access = self.env.user.has_group('ati_pbf_sale.sale_order_pasien_panel')
        if not self.env.user.has_group('ati_pbf_sale.sale_order_approval_apj'):
            if not is_panel_access:
                self.pasien_panel = False
            else:
                self.pasien_panel = True

        elif self.env.user.has_group('ati_pbf_sale.sale_order_approval_apj'):
            if not is_panel_access:
                self.pasien_panel = False
            else:
                self.pasien_panel = True

    @api.depends()
    def _compute_current_user(self):
        for partner in self:
            partner.current_user = self.env.user

    @api.depends('current_user')
    def get_is_invisible_panel(self):
        for this in self:
            # if this.current_user.login.lower() == 'apoteker':
            #     this.invisible_panel = True
            # elif this.current_user.name.lower() == 'apoteker':
            #     this.invisible_panel = True
            self._cr.execute("""
                    select b.uid from res_groups a
                    join res_groups_users_rel b on b.gid = a.id 
                    where lower(a.name) = 'hide is panel'
                    """)
            fet_user = self._cr.fetchall()
            user_panel = [uid[0] for uid in fet_user]
            if this.current_user.id in user_panel:
                this.invisible_panel = True
            elif this.type_partner == 'supplier':
                this.invisible_panel = True
            elif this.pasien_panel == False:
                this.invisible_panel = True
            else:
                this.invisible_panel = False

    current_user = fields.Many2one('res.users', string="Current User", compute='_compute_current_user')
    invisible_panel = fields.Boolean(string='Invisible Panel', default=False, compute=get_is_invisible_panel)
    _is_panel = fields.Boolean('Is Panel?', default=False)
    panel_ids = fields.One2many('panel.panel', 'partner_id', 'Panel')
    pasien_panel = fields.Boolean(string='Is Access Right?', compute='_compute_is_pasien_panel_res_partner', index=True)
    name = fields.Char(index=True, tracking=True,)

    # @api.depends('partner_id.name', 'partner_id.code_customer', 'partner_id.code_bmp')
    # def name_get(self):
    #     # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
    #     res = super().name_get()
    #     for partner_ in self:
    #         name = ''
    #         gotted_name = partner_._get_name()
    #         if partner_.type_partner == 'customer':
    #             print('1111',gotted_name)
    #             self.browse(self.ids).read(["name", "code_customer", "street", "street2", "city", "state_id", "zip", "country_id"])
    #             name = (('[' + partner_.code_customer + '] ') if partner_.code_customer else '') + gotted_name
    #         elif partner_.type_partner == 'supplier':
    #             self.browse(self.ids).read(["name", "code_bmp", "street", "street2", "city", "state_id", "zip", "country_id"])
    #             name = (('[' + partner_.code_bmp + '] ') if partner_.code_bmp else '') + gotted_name
    #
    #         x = res[0]
    #         y = list(x)
    #         y[1] = name
    #         x = tuple(y)
    #         res[0] = x
    #
    #
    #     return res

    @api.depends('partner_id.name', 'partner_id.code_customer', 'partner_id.code_bmp')
    def name_get(self):
        result=[]
        for rec in self:
            get_nama = rec._get_name()
            if rec.type_partner == 'customer':
                rec.browse(rec.ids).read(["name", "code_customer", "street", "street2", "city", "state_id", "zip", "country_id"])
                # new_name = ('[' + rec.code_customer + ']' if rec.code_customer else '') + get_nama
                new_name = ('[' + rec.code_customer + ']' if rec.code_customer else '') + rec.name
            elif rec.type_partner == 'supplier':
                rec.browse(rec.ids).read(["name", "code_bmp", "street", "street2", "city", "state_id", "zip", "country_id"])
                # new_name = ('[' + rec.code_bmp + ']' if rec.code_bmp else '') + get_nama
                new_name = ('[' + rec.code_bmp + ']' if rec.code_bmp else '') + rec.name
            else:
                # new_name = rec.name + get_nama
                # new_name = get_nama
                new_name = rec.name
            if rec._origin.id != False:
                if rec.name:
                    if "'" in rec.name or '"' in rec.name:
                        raise UserError('Single or double quotation marks are not allowed in field name')
                        break
                update_data = "update res_partner set display_name = '{_dn}' where id = {_id}".format(_dn=new_name, _id=rec.id)
                self._cr.execute(update_data)
            result.append((rec.id, '%s' % (new_name)))
        return result