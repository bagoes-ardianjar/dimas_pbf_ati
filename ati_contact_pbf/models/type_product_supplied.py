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


class TypeProductSupplied(models.Model):
    _name = 'type.product.supplied'

    name  = fields.Char('Name')
    