# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "POS Promotional Offers & Discounts",
  "summary"              :  """The Module allows the POS user to create Promotions/Offers. Create multiple discount and offer free prdouct. Offer products are visible in Sale Orderlines.Odoo POS discount|Order discount|Customer discount POS|Purchase discount|Sales order discount""",
  "category"             :  "Point of Sale",
  "version"              :  "1.1.2",
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Odoo-POS-Promotional-Offers-Discounts.html",
  "description"          :  """POS sales promotions
POS discount offers
POS sales offers
POS receipt offer
POS promo offers
Pos seasonal discounts
Instant discount Odoo
Odoo POS Order Discount
POS Order line discount
POS Orderline discount
Discount per product
POS Per product off
Odoo POS discount
Order discount
Percentage discount odoo POS
Customer discount POS
Purchase discount 
Sales order discount
POS create discount""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=pos_promotional_discounts&custom_url=/pos/web",
  "depends"              :  ['point_of_sale'],
  "data"                 :  [
                             'security/ir.model.access.csv',
                             'views/promotional_message_view.xml',
                             'views/pos_config_view.xml',
                            ],
  "demo"                 :  ['demo/demo.xml'],
  "images"               :  ['static/description/POS-Promotion-banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "assets"               :  {
                              'point_of_sale.assets': [
                                  "/pos_promotional_discounts/static/src/js/models.js",
                                  "/pos_promotional_discounts/static/src/js/screens.js",
                                ],
                                'web.assets_qweb': [
                                  'pos_promotional_discounts/static/src/xml/pos.xml'
                                ],
                            },
  "auto_install"         :  False,
  "price"                :  49,
  "currency"             :  "USD",
  "pre_init_hook"        :  "pre_init_check",
}
