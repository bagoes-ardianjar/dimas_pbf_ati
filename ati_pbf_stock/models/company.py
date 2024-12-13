from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ResCompany(models.Model):
    _inherit = 'res.company'

    no_izin_pbf_pusat = fields.Char(string='No Izin PBF Pusat')
    no_izin_pak_pusat = fields.Char(string='No Izin PAK Pusat')
    cdob_ccp = fields.Char(string='CDOB CCP')
    cdob_lainnya = fields.Char(string='CDOB Lainnya')
    cdakb = fields.Char(string='CDAKB')