import time
from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError
import xml.etree.ElementTree as etree
from datetime import datetime,date
import base64
import requests
from datetime import datetime, timedelta,date
from dateutil import relativedelta
from dateutil.relativedelta import relativedelta


class CustomerType(models.Model):
    _name = 'customer.type'

    name  = fields.Char('Name')
    