# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv.expression import AND
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

class StockPickingWorkOrderBatch(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = "stock.picking.work.order.batch"
    _description = "Picking Batch Delivery Order"
    _order = "name desc"

    name = fields.Char(string='Batch Picking Delivery Order', default='New',
        copy=False, required=True, readonly=True,
        help='Name of the WO batch transfer')
    user_id = fields.Many2one('res.users', string='Responsible', tracking=True, check_company=True,
        help='Person responsible for this batch transfer')
    company_id = fields.Many2one('res.company', string="Company", required=True, readonly=True,
        index=True, default=lambda self: self.env.company)
    picking_ids = fields.One2many('stock.picking', 'wo_batch_id', string='Transfers', domain="[('id', 'in', allowed_picking_ids)]", check_company=True,
        help='List of transfers associated to this batch')
    allowed_picking_ids = fields.One2many('stock.picking', compute='_compute_allowed_picking_ids')
    picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type', domain="[('code', '=', 'outgoing')]",
        check_company=True, copy=False)
    picking_type_code = fields.Selection(related='picking_type_id.code')
    scheduled_date = fields.Datetime('Scheduled Date', copy=False, store=True, readonly=False, compute="_compute_scheduled_date",
        help="""Scheduled date for the transfers to be processed.""")
    partner_id = fields.Many2one('res.partner', string='Customer')
    expedition_name = fields.Char('Nama Ekspedisi')
    plat_number_id = fields.Many2one('plat.number', string='No. Plat')
    res_driver_id = fields.Many2one('res.driver', string='Nama Supir')
    koli_ids = fields.One2many('stock.picking.koli', 'wo_batch_id')
    # state = fields.Selection([
    #     ('draft', 'Draft'),
    #     ('in_progress', 'In progress'),
    #     ('done', 'Done'),
    #     ('cancel', 'Cancelled')], default='draft',
    #     store=True, compute='_compute_state',
    #     copy=False, tracking=True, required=True, readonly=True)


    @api.depends('company_id', 'picking_type_id', 'partner_id')
    def _compute_allowed_picking_ids(self):
        for batch in self:
            domain = [
                ('company_id', '=', batch.company_id.id)
            ]
            if batch.partner_id:
                domain += [('partner_id', '=', batch.partner_id.id)]
            else:
                domain += [('picking_type_id.code', '=', 'outgoing')]
            batch.allowed_picking_ids = self.env['stock.picking'].search(domain)

    @api.depends('picking_ids', 'picking_ids.scheduled_date')
    def _compute_scheduled_date(self):
        for rec in self:
            rec.scheduled_date = min(rec.picking_ids.filtered('scheduled_date').mapped('scheduled_date'), default=False)

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('batch.work.order') or '/'
        return super().create(vals)


class Driver(models.Model):
    _name = "res.driver"
    _description = "Driver"
    _order = "name"

    name = fields.Char(string='Driver Name', help='Driver Name')
    active = fields.Boolean('Active', default=True, help="By unchecking the active field, you may hide a driver.")


class PlatNumber(models.Model):
    _name = "plat.number"
    _description = "Driver"
    _order = "name"

    name = fields.Char(string='Plat Number', help='Plat Number')
    active = fields.Boolean('Active', default=True, help="By unchecking the active field, you may hide a plat number.")