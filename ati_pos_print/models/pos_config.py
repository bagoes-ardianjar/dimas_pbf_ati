# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    employee_id = fields.Many2one('hr.employee', 'Apoteker', required=False)