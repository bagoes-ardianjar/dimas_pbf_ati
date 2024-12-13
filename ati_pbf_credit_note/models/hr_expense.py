from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, Warning, RedirectWarning
from datetime import date, datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from dateutil.relativedelta import relativedelta
import pytz

DATETIME = pytz.timezone('Asia/Jakarta')



class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'


    def _check_can_approve(self):
        return True