# -*- coding: utf-8 -*-
######################################################################################
#
#    Odoo Being
#
#    Copyright (C) 2021-TODAY Odoo Being(<https://www.odoobeing.com>).
#    Author: Odoo Being(<https://www.odoobeing.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
########################################################################################
{
    'name': "POS Combo Products",
    'summary': """
        Helps to sell product by combo.""",
    'description': """
        POS combo product,  pos, odoo15 pos, pos odoo15, odoo 15, combo products, receipt, custom receipt in odoo15,
        odoo15 receipt, odoobeing, odoo 15 point of sale, odoo15 point of sale, odoo 15 receipt, pos screen,
        point of sale, custom order in pos, custom popup in pos, odoo 15 pos popup, odoo 15 pos report,
        odoo15 pos report, pos report odoo15, odoo15 .""",
    'author': "Odoo Being",
    'website': "https://www.odoobeing.com",
    'license': 'OPL-1',
    'category': 'Point of Sale',
    'version': '15.0.1.0.1',
    'support': 'odoobeing@gmail.com',
    'price': '12',
    'images': ['static/description/images/pos_combo_product.png'],
    'currency': 'USD',
    'installable': True,
    'auto_install': False,
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/combo_products_view.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            '/ob_pos_combo_product/static/src/css/combo_product.css',
            '/ob_pos_combo_product/static/src/js/combo_popup.js',
            '/ob_pos_combo_product/static/src/js/combo_products.js',
        ],
        'web.assets_qweb': [
            'ob_pos_combo_product/static/src/xml/combo_products.xml',
        ],
    },
}
