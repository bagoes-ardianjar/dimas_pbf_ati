# -*- coding: utf-8 -*-
# from odoo import http


# class AtiPbfPurchaseOrderLine(http.Controller):
#     @http.route('/ati_pbf_purchase_order_line/ati_pbf_purchase_order_line', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ati_pbf_purchase_order_line/ati_pbf_purchase_order_line/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('ati_pbf_purchase_order_line.listing', {
#             'root': '/ati_pbf_purchase_order_line/ati_pbf_purchase_order_line',
#             'objects': http.request.env['ati_pbf_purchase_order_line.ati_pbf_purchase_order_line'].search([]),
#         })

#     @http.route('/ati_pbf_purchase_order_line/ati_pbf_purchase_order_line/objects/<model("ati_pbf_purchase_order_line.ati_pbf_purchase_order_line"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ati_pbf_purchase_order_line.object', {
#             'object': obj
#         })
