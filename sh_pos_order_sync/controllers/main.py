# -*- coding: utf-8 -*-
# Copyright (C) Softhealer Technologies.

from odoo.http import request
from odoo.addons.bus.controllers.main import BusController


class PosOrderController(BusController):

    def _poll(self, dbname, channels, last, options):
        """Add the relevant channels to the BusController polling."""
        if options.get('order.pos'):
            channels = list(channels)
            lock_channel = (
                request.db,
                'order.pos',
                options.get('order.pos')
            )
            channels.append(lock_channel)
        return super(PosOrderController, self)._poll(dbname, channels, last, options)
