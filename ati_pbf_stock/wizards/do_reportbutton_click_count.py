from odoo import models, fields, _

class DoReportButtonClickCount(models.Model):
	_name = 'do.reportbutton.click'
	_description = 'Count DO report button click by each user login'

	name = fields.Many2one('res.users', string='User login')
	button_clicked = fields.Boolean('Button clicked', default=False)
	picking_ids = fields.Many2one('stock.picking')

class DoReportButtonOpened(models.TransientModel):
	_name = "do.reportbutton.opened"
	_description = "DO Report Button Opened"

	is_opened = fields.Boolean('Is Opened?')

	def get_default(self):
		#
		do_reportbutton_opened = self.env['do.reportbutton.opened'].search([], limit=1)
		return do_reportbutton_opened.name

	name = fields.Text(string="Message", readonly=True, default=get_default)

class DoReportButtonDenied(models.TransientModel):
	_name = "do.reportbutton.denied"
	_description = "DO Report Button Denied"

	def get_default(self):
		#
		do_reportbutton_denied = self.env['do.reportbutton.denied'].search([], limit=1)
		return do_reportbutton_denied.name

	name = fields.Text(string="Message", readonly=True, default=get_default)

class DoReportButtonRejected(models.TransientModel):
	_name = "do.reportbutton.rejected"
	_description = "DO Report Button Rejected"

	is_rejected = fields.Boolean('Is Rejected?')

	def get_default(self):
		#
		do_reportbutton_rejected = self.env['do.reportbutton.rejected'].search([], limit=1)
		return do_reportbutton_rejected.name

	name = fields.Text(string="Message", readonly=True, default=get_default)
