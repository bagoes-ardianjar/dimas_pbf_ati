import time
from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError
import xml.etree.ElementTree as etree
from datetime import datetime,date
import base64
import requests
from datetime import datetime, timedelta,date
from dateutil.relativedelta import relativedelta


class InheritRespartner(models.Model):
    _inherit = 'res.partner'

    sales_person = fields.Many2one('hr.employee', string='Sales Person', index=True, tracking=1)