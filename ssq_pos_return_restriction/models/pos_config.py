from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PosConfig(models.Model):
    _inherit = "pos.config"

    is_return_allowed_control = fields.Boolean(
        string="Restrict Return",
        default=False,
    )
    return_allowed_employee_ids = fields.Many2many(
        "hr.employee",
        "pos_config_return_allowed_employee_rel",
        string="Employees Allowed to Return",
        help="Employees allowed to return products in POS",
    )

    @api.constrains("return_allowed_employee_ids", "employee_ids")
    def _check_return_allowed_employee_ids(self):
        for record in self:
            if record.is_return_allowed_control and record.employee_ids and record.return_allowed_employee_ids:
                if not set(record.return_allowed_employee_ids.ids).issubset(set(record.employee_ids.ids)):
                    raise ValidationError(_("Employees Allowed to Return should be in Allowed Employees"))
