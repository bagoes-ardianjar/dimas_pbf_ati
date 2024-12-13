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

    # @api.onchange('name')
    # def func_onchange_name_address(self):
    #     for this in self:
    #         if this.name and this._origin.id:
    #             if "'" or '"' in this.name:
    #                 print('sss',this._origin.id,this.name)
    #                 raise UserError('Single or double quotation marks are not allowed in this field')

    @api.model
    def create(self, vals):
        res = super(InheritRespartner, self).create(vals)

        for rec in res:
            if rec.name:
                if "'" in rec.name or '"' in rec.name:
                    raise UserError('Single or double quotation marks are not allowed in field name')
                    break
            if rec.street:
                if "'" in rec.street or '"' in rec.street:
                    raise UserError('Single or double quotation marks are not allowed in field address')
                    break
        return res

    def write(self, vals):
        res = super(InheritRespartner, self).write(vals)
        for this in self:
            if this.name:
                if "'" in this.name or '"' in this.name:
                    raise UserError('Single or double quotation marks are not allowed in field name')
                    break
            if this.street:
                if "'" in this.street or '"' in this.street:
                    raise UserError('Single or double quotation marks are not allowed in field address')
                    break
        return res

    type_partner                = fields.Selection([('customer','Customer'),('supplier','Supplier')], string="Type")
    expired_date_certificate    = fields.Date('Expired Date Certificate')
    code_bmp                    = fields.Char('Code Supplier')
    code_e_report               = fields.Char('Code E-Report')
    code_customer               = fields.Char('Code Customer')
    code_bpom                   = fields.Char('Code BPOM')
    supplier_type_id            = fields.Many2one('supplier.type','Supplier Type')
    customer_type_id            = fields.Many2one('customer.type','Customer Type')
    margin_ids                  = fields.Many2many('m.margin',string='Margin', tracking=True)
    type_product_supplied_ids    = fields.Many2many('type.product.supplied',string='Product Type Supplier')

    # ===APJ
    # apj_employee_id             = fields.Many2one('hr.employee','APJ Employee')
    apj_employee_id             = fields.Char('APJ Employee')
    no_sipa                     = fields.Char('SIPA')
    due_date_sipa               = fields.Date('Due Date SIPA')
    apj_no_telp                 = fields.Char('No Telp APJ') 
    apj_email                   = fields.Char('Email APJ')

    # ===PJT Alkes
    # pjt_employee_id             = fields.Many2one('hr.employee','PJT Employee')
    pjt_employee_id             = fields.Char('PJT Employee')
    pjt_no_doc                  = fields.Char('No Dokument PJT Alkes')
    due_date_pjt                = fields.Date('Due Date PJT')
    pjt_no_telp                 = fields.Char('No Telp PJT') 
    pjt_email                   = fields.Char('Email PJT')


    # ===Supplier
    no_siub                     = fields.Char('No SIUB/NIB')
    no_izin_sarana              = fields.Char('No Izin Sarana')
    due_date_sarana             = fields.Date('Due Date Sarana')
    no_cpob_cpotb_cpakb         = fields.Char('No CPOB/CPOTB/CPAKB')
    due_date_cpob_cpotb_cpakb   = fields.Date('Due Date CPOB/CPOTB/CPAKB')
    no_sertif_cdakb             = fields.Char('No Sertif CDAKB')
    due_date_cdakb              = fields.Date('Due Date CDAKB')
    no_ipak_sdak_idak           = fields.Char('No IPAK/SDAK/IDAK')
    due_date_ipak_sdak_idak     = fields.Date('Due Date IPAK/SDAK/IDAK')
    no_sertif_cdob              = fields.Char('No Sertif CDOB')
    due_date_cdob               = fields.Date('Due Date CDOB')
    no_sertif_cdob_ccp          = fields.Char('No Sertif CDOB CCP')
    due_date_cdob_ccp           = fields.Date('Due Date CDOB CCP')
    x_membership                = fields.Boolean('Membership')
    # sales_person = fields.Many2one('hr.employee', string='Sales Person (*)', index=True, tracking=1)

    # ===Name AA Penerima Delegasi
    name_aping                  = fields.Char('Name APING')
    no_sipa_aping               = fields.Char('No SIPA')
    due_date_sipa_aping         = fields.Date('Due Date SIPA')

    ''' Internal Notes '''
    expired_registration = fields.Date(string='Expired Registration', default=date.today(), required=True)
    code_ga = fields.Char(string='Code GA')
    code_alkes = fields.Char(string='Code Alkes')
    notes = fields.Text(string='Notes')
    customer_partner_ids = fields.One2many('customer.partner', 'partner_id', 'List Customer')

    def return_customer_expired_registration(self):
        partner_ids = partner_ids = self.env['res.partner'].sudo().search([('customer_rank', '>', 0), ('expired_registration', '<', fields.Date.today() + relativedelta(months=1))])
        return partner_ids

    def return_vendor_expired_registration(self):
        partner_ids = partner_ids = self.env['res.partner'].sudo().search([('supplier_rank', '>', 0), ('expired_registration', '<', fields.Date.today() + relativedelta(months=1))])
        return partner_ids

    def template_email_reminder_expired_registration(self, email_to, mail_server_id):
      template_mail = False
      template = self.env.ref('ati_contact_pbf.mail_template_reminder_partner_expired_registration')
      template_values = {
         'subject': f'Reminder Expired Registration {fields.Date.today().strftime("%d-%m-%Y")}',
         'email_to': email_to,
         'email_cc': False,
         'auto_delete': False,
         'partner_to': False,
         'scheduled_date': False,
         'mail_server_id': mail_server_id.id,
         'body_html': '''
                <table border="0" cellpadding="0" cellspacing="0" style="width:100%; margin:0px auto;">
                    <tbody>
                        <tr>
                            <td style="text-align:left; height:25px; width:5%;"></td>
                            <td style="text-align:left; height:25px; width:40%;"></td>
                            <td style="text-align:left; height:25px; width:55%;"></td>
                        <tr>
                            <td colspan="3" valign="top" style="text-align: left; font-size: 14px;">
                            Customer Registration Expired
                            </td>
                        </tr>
                        <tr>
                            <td><span>No</span></td>
                            <td><span>Name</span></td>
                            <td><span>Expired Date</span></td>
                        </tr>
                        <t t-set="i" t-value="1"/>
                        <t t-foreach="object.return_customer_expired_registration()" t-as="l">
                            <tr>
                                <td>
                                    <span><t t-esc="i"/></span>
                                </td>
                                <td>
                                    <span><t t-esc="l.name"/></span>
                                </td>
                                <td>
                                    <span><t t-esc="l.expired_registration.strftime('%d-%m-%Y')"/></span>
                                </td>
                            </tr>
                            <t t-set="i" t-value="i+1"/>
                        </t>
                        <tr>
                            <td colspan="3" valign="top" style="text-align: left; font-size: 14px;">
                            <br></br>----------------------------------------------------------------------<br></br>
                            </td>
                        </tr>
                        <tr>
                            <td colspan="3" valign="top" style="text-align: left; font-size: 14px;">
                            Vendor Registration Expired
                            </td>
                        </tr>
                        <tr>
                            <td><span>No</span></td>
                            <td><span>Name</span></td>
                            <td><span>Expired Date</span></td>
                        </tr>
                        <t t-set="i" t-value="1"/>
                        <t t-foreach="object.return_vendor_expired_registration()" t-as="l">
                            <tr>
                                <td>
                                    <span><t t-esc="i"/></span>
                                </td>
                                <td>
                                    <span><t t-esc="l.name"/></span>
                                </td>
                                <td>
                                    <span><t t-esc="l.expired_registration.strftime('%d-%m-%Y')"/></span>
                                </td>
                            </tr>
                            <t t-set="i" t-value="i+1"/>
                        </t>
                    </tbody>
                </table>
            ''',
      }
      template.sudo().write(template_values)
      if template:
         template_mail = template.sudo().send_mail(
            self.id,
            notif_layout='mail.mail_notification_light')
      return template_mail
    
    def cron_reminder_expired_registration(self):
        email_to = []
        mail_server_id = False
        user = self.env.user
        email_user_ids = user.company_id.remainder_email_user_ids
        mail_server_id = user.company_id.remainder_email_mail_server_id
        for email_user in email_user_ids:
            if email_user.partner_id and email_user.partner_id.email:
               email_to.append(email_user.partner_id.email)
        
        if not mail_server_id:
            raise UserError('Please setup mail server for remainder email partner expired registration in master company')

        if not email_to:
            raise UserError('Please select user destination for remainder email partner expired registration in master company')

        if email_to:
            email_to = (','.join(email_to))
        template_mail = self.template_email_reminder_expired_registration(email_to, mail_server_id)
        if template_mail:
            self.env['mail.mail'].sudo().browse(template_mail).send()
        

class CustomerPartner(models.Model):
    _name = 'customer.partner'
    _description = 'List Customer Partner'

    name = fields.Char(string='Nama')
    no_sipttk = fields.Char(string='No SIPTTK')
    expired_employee_date = fields.Date(string='Masa Berlaku')
    partner_id = fields.Many2one('res.partner', 'Partner')