# -*- coding: utf-8 -*-
# from odoo import http


# class AtiPbfPromotionPo(http.Controller):
#     @http.route('/ati_pbf_promotion_po/ati_pbf_promotion_po', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ati_pbf_promotion_po/ati_pbf_promotion_po/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('ati_pbf_promotion_po.listing', {
#             'root': '/ati_pbf_promotion_po/ati_pbf_promotion_po',
#             'objects': http.request.env['ati_pbf_promotion_po.ati_pbf_promotion_po'].search([]),
#         })

#     @http.route('/ati_pbf_promotion_po/ati_pbf_promotion_po/objects/<model("ati_pbf_promotion_po.ati_pbf_promotion_po"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ati_pbf_promotion_po.object', {
#             'object': obj
#         })
