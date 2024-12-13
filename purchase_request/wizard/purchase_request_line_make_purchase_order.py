# Copyright 2018-2019 ForgeFlow, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseRequestLineMakePurchaseOrder(models.TransientModel):
    _name = "purchase.request.line.make.purchase.order"
    _description = "Purchase Request Line Make Purchase Order"

    supplier_id = fields.Many2one(
        comodel_name="res.partner",
        string="Supplier",
        required=True,
        context={"res_partner_search_mode": "supplier"},
    )
    item_ids = fields.One2many(
        comodel_name="purchase.request.line.make.purchase.order.item",
        inverse_name="wiz_id",
        string="Items",
    )
    purchase_order_id = fields.Many2one(
        comodel_name="purchase.order",
        string="Purchase Order",
        domain=[("state", "=", "draft")],
    )
    sync_data_planned = fields.Boolean(
        string="Merge on PO lines with equal Scheduled Date"
    )

    @api.model
    def _prepare_item(self, line):
        return {
            "line_id": line.id,
            "request_id": line.request_id.id,
            "product_id": line.product_id.id,
            "name": line.name or line.product_id.name,
            "product_qty": line.pending_qty_to_receive,
            "product_uom_id": line.product_uom_id.id,
        }

    @api.model
    def _check_valid_request_line(self, request_line_ids):
        picking_type = False
        company_id = False

        for line in self.env["purchase.request.line"].browse(request_line_ids):
            if line.request_id.state == "done":
                raise UserError(_("The purchase has already been completed."))
            if line.request_id.state != "approved":
                raise UserError(
                    _("Purchase Request %s is not approved") % line.request_id.name
                )

            if line.purchase_state == "done":
                raise UserError(_("The purchase has already been completed."))

            line_company_id = line.company_id and line.company_id.id or False
            if company_id is not False and line_company_id != company_id:
                raise UserError(_("You have to select lines from the same company."))
            else:
                company_id = line_company_id

            line_picking_type = line.request_id.picking_type_id or False
            if not line_picking_type:
                raise UserError(_("You have to enter a Picking Type."))
            if picking_type is not False and line_picking_type != picking_type:
                raise UserError(
                    _("You have to select lines from the same Picking Type.")
                )
            else:
                picking_type = line_picking_type

    @api.model
    def check_group(self, request_lines):
        if len(list(set(request_lines.mapped("request_id.group_id")))) > 1:
            raise UserError(
                _(
                    "You cannot create a single purchase order from "
                    "purchase requests that have different procurement group."
                )
            )

    @api.model
    def get_items(self, request_line_ids):
        request_line_obj = self.env["purchase.request.line"]
        items = []
        request_lines = request_line_obj.browse(request_line_ids)
        self._check_valid_request_line(request_line_ids)
        self.check_group(request_lines)
        for line in request_lines:
            items.append([0, 0, self._prepare_item(line)])
        return items

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        active_model = self.env.context.get("active_model", False)
        request_line_ids = []
        if active_model == "purchase.request.line":
            request_line_ids += self.env.context.get("active_ids", [])
        elif active_model == "purchase.request":
            request_ids = self.env.context.get("active_ids", False)
            request_line_ids += (
                self.env[active_model].browse(request_ids).mapped("line_ids.id")
            )
        if not request_line_ids:
            return res
        res["item_ids"] = self.get_items(request_line_ids)
        request_lines = self.env["purchase.request.line"].browse(request_line_ids)
        supplier_ids = request_lines.mapped("supplier_id").ids
        if len(supplier_ids) == 1:
            res["supplier_id"] = supplier_ids[0]
        return res

    @api.model
    def _prepare_purchase_order(self, picking_type, group_id, company, origin):
        if not self.supplier_id:
            raise UserError(_("Enter a supplier."))
        supplier = self.supplier_id
        data = {
            "origin": origin,
            "partner_id": self.supplier_id.id,
            "fiscal_position_id": supplier.property_account_position_id
            and supplier.property_account_position_id.id
            or False,
            "picking_type_id": picking_type.id,
            "company_id": company.id,
            "group_id": group_id.id,
        }
        return data

    @api.model
    def _get_purchase_line_onchange_fields(self):
        return ["product_uom", "price_unit", "name", "taxes_id"]

    @api.model
    def _execute_purchase_line_onchange(self, vals):
        cls = self.env["purchase.order.line"]
        onchanges_dict = {
            "onchange_product_id": self._get_purchase_line_onchange_fields()
        }
        for onchange_method, changed_fields in onchanges_dict.items():
            if any(f not in vals for f in changed_fields):
                obj = cls.new(vals)
                getattr(obj, onchange_method)()
                for field in changed_fields:
                    vals[field] = obj._fields[field].convert_to_write(obj[field], obj)

    def create_allocation(self, po_line, pr_line, new_qty, alloc_uom):
        vals = {
            "requested_product_uom_qty": new_qty,
            "product_uom_id": alloc_uom.id,
            "purchase_request_line_id": pr_line.id,
            "purchase_line_id": po_line.id,
        }
        return self.env["purchase.request.allocation"].create(vals)

    @api.model
    def _prepare_purchase_order_line(self, po, item):
        if not item.product_id:
            raise UserError(_("Please select a product for all lines"))
        product = item.product_id

        # Keep the standard product UOM for purchase order so we should
        # convert the product quantity to this UOM
        qty = item.product_uom_id._compute_quantity(
            item.product_qty, product.uom_po_id or product.uom_id
        )
        # Suggest the supplier min qty as it's done in Odoo core
        min_qty = item.line_id._get_supplier_min_qty(product, po.partner_id)
        qty = max(qty, min_qty)
        date_required = item.line_id.date_required
        vals = {
            "name": product.name,
            "order_id": po.id,
            "product_id": product.id,
            "product_uom": product.uom_po_id.id or product.uom_id.id,
            "price_unit": 0.0,
            "product_qty": qty,
            "account_analytic_id": item.line_id.analytic_account_id.id,
            "purchase_request_lines": [(4, item.line_id.id)],
            "date_planned": datetime(
                date_required.year, date_required.month, date_required.day
            ),
            "move_dest_ids": [(4, x.id) for x in item.line_id.move_dest_ids],
        }
        if item.line_id.analytic_tag_ids:
            vals["analytic_tag_ids"] = [
                (4, ati) for ati in item.line_id.analytic_tag_ids.ids
            ]
        self._execute_purchase_line_onchange(vals)
        return vals

    @api.model
    def _get_purchase_line_name(self, order, line):
        product_lang = line.product_id.with_context(
            lang=self.supplier_id.lang, partner_id=self.supplier_id.id
        )
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += "\n" + product_lang.description_purchase
        return name

    @api.model
    def _get_order_line_search_domain(self, order, item):
        vals = self._prepare_purchase_order_line(order, item)
        name = self._get_purchase_line_name(order, item)
        order_line_data = [
            ("order_id", "=", order.id),
            ("name", "=", name),
            ("product_id", "=", item.product_id.id or False),
            ("product_uom", "=", vals["product_uom"]),
            ("account_analytic_id", "=", item.line_id.analytic_account_id.id or False),
        ]
        if self.sync_data_planned:
            date_required = item.line_id.date_required
            order_line_data += [
                (
                    "date_planned",
                    "=",
                    datetime(
                        date_required.year, date_required.month, date_required.day
                    ),
                )
            ]
        if not item.product_id:
            order_line_data.append(("name", "=", item.name))
        return order_line_data

    def make_sale_order(self):
        for rec in self:
            # company = self.env['res.company']._find_company_from_partner(rec.supplier_id.id)
            company_rec = self.env['res.company']._find_company_from_partner(rec.supplier_id.id)
            if company_rec:
                # print("company", company_rec, self._context)
                rec.with_user(company_rec.intercompany_user_id).with_context(default_company_id=company_rec.id).with_company(company_rec).inter_company_create_sale_order(company_rec)

        return True

    def inter_company_create_sale_order(self, company):
        # print("inter_company_create_sale_order", self._context)
        """ Create a Sales Order from the current PO (self)
            Note : In this method, reading the current PO is done as sudo, and the creation of the derived
            SO as intercompany_user, minimizing the access right required for the trigger user.
            :param company : the company of the created PO
            :rtype company : res.company record
        """
        # find user for creating and validation SO/PO from partner company
        purchase_request_id = self._context.get('purchase_request_id', False)
        request_id = self.env['purchase.request'].search([('id', '=', purchase_request_id)])
        intercompany_uid = company.intercompany_user_id and company.intercompany_user_id.id or False
        if not intercompany_uid:
            raise UserError(_(
                'Provide at least one user for inter company relation for %(name)s',
                name=company.name,
            ))
        # check intercompany user access rights
        if not self.env['sale.order'].check_access_rights('create', raise_exception=False):
            raise UserError(_(
                "Inter company user of company %(name)s doesn't have enough access rights",
                name=company.name,
            ))

        for rec in self:
            # check pricelist currency should be same with SO/PO document
            company_partner = request_id.company_id.partner_id.with_user(intercompany_uid)
            if request_id.currency_id.id != company_partner.property_product_pricelist.currency_id.id:
                raise UserError(_(
                    'You cannot create SO from PO because sale price list currency is different '
                    'than purchase price list currency.\n'
                    'The currency of the SO is obtained from the pricelist of the company partner.\n\n'
                    '(SO currency: %(so_currency)s, Pricelist: %(pricelist)s, Partner: %(partner)s (ID: %(id)s))',
                    so_currency=request_id.currency_id.name,
                    pricelist=company_partner.property_product_pricelist.display_name,
                    partner=company_partner.display_name,
                    id=company_partner.id,
                ))

            # create the SO and generate its lines from the PO lines
            # read it as sudo, because inter-compagny user can not have the access right on PO
            direct_delivery_address = request_id.picking_type_id.warehouse_id.partner_id.id #or rec.dest_address_id.id
            sale_order_data = rec.sudo()._prepare_sale_order_data(
                request_id.name, company_partner, company,
                direct_delivery_address or False)
            inter_user = self.env['res.users'].sudo().browse(intercompany_uid)
            # lines are browse as sudo to access all data required to be copied on SO line (mainly for company dependent field like taxes)
            # for line in rec.order_line.sudo():
            for line in rec.item_ids.sudo():
                sale_order_data['order_line'] += [(0, 0, rec._prepare_sale_order_line_data(line, company))]
            sale_order = self.env['sale.order'].with_context(allowed_company_ids=inter_user.company_ids.ids).with_user(intercompany_uid).create(sale_order_data)
            sale_order.order_line._compute_tax_id()
            msg = _("Automatically generated from %(origin)s of company %(company)s.", origin=request_id.name, company=request_id.company_id.name)
            sale_order.message_post(body=msg)
            print("sale_order", sale_order.name)

            # update sale order id in purchase request #
            request_id.write({'sale_id': sale_order.id})

            # write vendor reference field on PO
            # if not rec.partner_ref:
            #     rec.partner_ref = sale_order.name

            #Validation of sales order
            if company.auto_validation:
                sale_order.with_user(intercompany_uid).action_confirm()

    def _prepare_sale_order_data(self, name, partner, company, direct_delivery_address):
        print("_prepare_sale_order_data", self._context)
        """ Generate the Sales Order values from the PO
            :param name : the origin client reference
            :rtype name : string
            :param partner : the partner reprenseting the company
            :rtype partner : res.partner record
            :param company : the company of the created SO
            :rtype company : res.company record
            :param direct_delivery_address : the address of the SO
            :rtype direct_delivery_address : res.partner record
        """
        self.ensure_one()
        purchase_request_id = self._context.get('purchase_request_id', False)
        request_id = self.env['purchase.request'].search([('id', '=', purchase_request_id)])
        partner_addr = partner.sudo().address_get(['invoice', 'delivery', 'contact'])
        warehouse = company.warehouse_id and company.warehouse_id.company_id.id == company.id and company.warehouse_id or False
        if not warehouse:
            raise UserError(_('Configure correct warehouse for company(%s) from Menu: Settings/Users/Companies', company.name))
        return {
            'name': self.env['ir.sequence'].sudo().next_by_code('sale.order') or '/',
            'company_id': company.id,
            'team_id': self.env['crm.team'].with_context(allowed_company_ids=company.ids)._get_default_team_id(domain=[('company_id', '=', company.id)]).id,
            'warehouse_id': warehouse.id,
            'client_order_ref': name,
            'partner_id': partner.id,
            'pricelist_id': partner.property_product_pricelist.id,
            'partner_invoice_id': partner_addr['invoice'],
            'date_order': request_id.date_start,#self.date_order,
            'fiscal_position_id': partner.property_account_position_id.id,
            'payment_term_id': partner.property_payment_term_id.id,
            'user_id': False,
            # 'auto_generated': True,
            # 'auto_purchase_order_id': self.id,
            # 'partner_shipping_id': direct_delivery_address or partner_addr['delivery'],
            'partner_shipping_id': partner.id,
            'origin': request_id.origin,
            'order_line': [],
        }

    @api.model
    def _prepare_sale_order_line_data(self, line, company):
        """ Generate the Sales Order Line values from the PO line
            :param line : the origin Purchase Order Line
            :rtype line : purchase.order.line record
            :param company : the company of the created SO
            :rtype company : res.company record
        """
        # it may not affected because of parallel company relation
        price = 0.0
        quantity = line.product_id and line.product_uom_id._compute_quantity(line.product_qty, line.product_id.uom_id) or line.product_qty
        price = line.product_id and line.product_uom_id._compute_price(price, line.product_id.uom_id) or price
        return {
            'name': line.name,
            'product_uom_qty': quantity,
            'product_id': line.product_id and line.product_id.id or False,
            'product_uom': line.product_id and line.product_id.uom_id.id or line.product_uom.id,
            # 'price_unit': price,
            'customer_lead': line.product_id and line.product_id.sale_delay or 0.0,
            'company_id': company.id,
            # 'display_type': line.display_type,
        }


    def make_purchase_order(self):
        res = []
        purchase_obj = self.env["purchase.order"]
        po_line_obj = self.env["purchase.order.line"]
        pr_line_obj = self.env["purchase.request.line"]
        purchase = False

        for item in self.item_ids:
            line = item.line_id
            if item.product_qty <= 0.0:
                raise UserError(_("Enter a positive quantity."))
            if self.purchase_order_id:
                purchase = self.purchase_order_id
            if not purchase:
                po_data = self._prepare_purchase_order(
                    line.request_id.picking_type_id,
                    line.request_id.group_id,
                    line.company_id,
                    line.origin,
                )
                purchase = purchase_obj.create(po_data)

            # Look for any other PO line in the selected PO with same
            # product and UoM to sum quantities instead of creating a new
            # po line
            domain = self._get_order_line_search_domain(purchase, item)
            available_po_lines = po_line_obj.search(domain)
            new_pr_line = True
            # If Unit of Measure is not set, update from wizard.
            if not line.product_uom_id:
                line.product_uom_id = item.product_uom_id
            # Allocation UoM has to be the same as PR line UoM
            alloc_uom = line.product_uom_id
            wizard_uom = item.product_uom_id
            if available_po_lines and not item.keep_description:
                new_pr_line = False
                po_line = available_po_lines[0]
                po_line.purchase_request_lines = [(4, line.id)]
                po_line.move_dest_ids |= line.move_dest_ids
                po_line_product_uom_qty = po_line.product_uom._compute_quantity(
                    po_line.product_uom_qty, alloc_uom
                )
                wizard_product_uom_qty = wizard_uom._compute_quantity(
                    item.product_qty, alloc_uom
                )
                all_qty = min(po_line_product_uom_qty, wizard_product_uom_qty)
                self.create_allocation(po_line, line, all_qty, alloc_uom)
            else:
                po_line_data = self._prepare_purchase_order_line(purchase, item)
                if item.keep_description:
                    po_line_data["name"] = item.name
                po_line = po_line_obj.create(po_line_data)
                po_line_product_uom_qty = po_line.product_uom._compute_quantity(
                    po_line.product_uom_qty, alloc_uom
                )
                wizard_product_uom_qty = wizard_uom._compute_quantity(
                    item.product_qty, alloc_uom
                )
                all_qty = min(po_line_product_uom_qty, wizard_product_uom_qty)
                self.create_allocation(po_line, line, all_qty, alloc_uom)
            # TODO: Check propagate_uom compatibility:
            new_qty = pr_line_obj._calc_new_qty(
                line, po_line=po_line, new_pr_line=new_pr_line
            )
            po_line.product_qty = new_qty
            po_line._onchange_quantity()
            # The onchange quantity is altering the scheduled date of the PO
            # lines. We do not want that:
            date_required = item.line_id.date_required
            po_line.date_planned = datetime(
                date_required.year, date_required.month, date_required.day
            )
            res.append(purchase.id)

        return {
            "domain": [("id", "in", res)],
            "name": _("RFQ"),
            "view_mode": "tree,form",
            "res_model": "purchase.order",
            "view_id": False,
            "context": False,
            "type": "ir.actions.act_window",
        }


class PurchaseRequestLineMakePurchaseOrderItem(models.TransientModel):
    _name = "purchase.request.line.make.purchase.order.item"
    _description = "Purchase Request Line Make Purchase Order Item"

    wiz_id = fields.Many2one(
        comodel_name="purchase.request.line.make.purchase.order",
        string="Wizard",
        required=True,
        ondelete="cascade",
        readonly=True,
    )
    line_id = fields.Many2one(
        comodel_name="purchase.request.line", string="Purchase Request Line"
    )
    request_id = fields.Many2one(
        comodel_name="purchase.request",
        related="line_id.request_id",
        string="Purchase Request",
        readonly=False,
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        related="line_id.product_id",
        readonly=False,
    )
    name = fields.Char(string="Description", required=True)
    product_qty = fields.Float(
        string="Quantity to purchase", digits="Product Unit of Measure"
    )
    product_uom_id = fields.Many2one(
        comodel_name="uom.uom", string="UoM", required=True
    )
    keep_description = fields.Boolean(
        string="Copy descriptions to new PO",
        help="Set true if you want to keep the "
        "descriptions provided in the "
        "wizard in the new PO.",
    )

    @api.onchange("product_id")
    def onchange_product_id(self):
        if self.product_id:
            if not self.keep_description:
                name = self.product_id.name
            code = self.product_id.code
            sup_info_id = self.env["product.supplierinfo"].search(
                [
                    "|",
                    ("product_id", "=", self.product_id.id),
                    ("product_tmpl_id", "=", self.product_id.product_tmpl_id.id),
                    ("name", "=", self.wiz_id.supplier_id.id),
                ]
            )
            if sup_info_id:
                p_code = sup_info_id[0].product_code
                p_name = sup_info_id[0].product_name
                name = "[{}] {}".format(
                    p_code if p_code else code, p_name if p_name else name
                )
            else:
                if code:
                    name = "[{}] {}".format(
                        code, self.name if self.keep_description else name
                    )
            if self.product_id.description_purchase and not self.keep_description:
                name += "\n" + self.product_id.description_purchase
            self.product_uom_id = self.product_id.uom_id.id
            if name:
                self.name = name
