# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import AccessError, UserError, ValidationError
import datetime
from datetime import datetime

class action_promotion_so(models.Model):
    _inherit = 'sale.order'

    # def confirm_quotation_with_apj(self):
    #     check_data_discount = self.order_line.filtered(lambda x: x.is_promotion == False and x.is_discount == False)
    #     if check_data_discount:
    #         raise UserError('Click the Promotion button to check your product got a promo')

    def action_promotion(self):
        # check_data = self.order_line.filtered(lambda x: x.is_promotion == True)
        # if check_data:
        #     raise UserError('You cannot use a promotion more than once')

        for line in self.order_line:
            line.is_promo = True

        # order_line_ids = [line.product_id.id for line in self.order_line]
        list_product_promotion_not_active = []
        promotion_not_active_ids = self.env['so.promotion'].sudo().search([('status', '!=', True)])
        for promotion_not_active in promotion_not_active_ids:
            for product in promotion_not_active.product_ids:
                list_product_promotion_not_active.append(product.id)
        # product_promotion_not_active = [promotion_not_active.product_ids.ids for promotion_not_active in promotion_not_active_ids]
        # product_not_active_ids = [product.id for product in product_promotion_not_active]
        for line in self.order_line:
            if line.product_id.id in list_product_promotion_not_active:
                raise UserError(f'Promotion not Approve in product {line.product_id.display_name}')

        product = []
        promotion = self.env['so.promotion'].search([('status', '=', True)])
        ## CHECK STATE
        if self.state in ('sale','done','cancel'):
            raise UserError(_('Cannot add Promotion in this state. Please contact Administrator.'))

        for promotion_product in promotion:
            if promotion_product.reward_type == 'product':
                for order_line in self.order_line:
                    if (promotion_product.rule_partners_domain and promotion_product.product_ids):
                        if promotion_product.rule_date_from and promotion_product.rule_date_to:
                            for product_ids_list in promotion_product.product_ids:
                                # filter = promotion_product.filtered(lambda r: product_ids_list.id == rec.product_id.id)
                                free_product = product_ids_list.id
                                for customer_id in promotion_product.rule_partners_domain:
                                    customer = customer_id.id

                                    if order_line.product_id.id == free_product and customer == self.partner_id.id and ((promotion_product.rule_min_quantity > 0 and int(order_line.product_uom_qty) >= promotion_product.rule_min_quantity) or (promotion_product.rule_minimum_amount > 0 and order_line.price_subtotal  >= promotion_product.rule_minimum_amount )):
                                            date_order = datetime.strptime(str(self.date_order),
                                                                           "%Y-%m-%d %H:%M:%S")
                                            start_date = datetime.strptime(str(promotion_product.rule_date_from),
                                                                           "%Y-%m-%d %H:%M:%S")
                                            end_date = datetime.strptime(str(promotion_product.rule_date_to),
                                                                         "%Y-%m-%d %H:%M:%S")

                                            if date_order <= end_date and date_order >= start_date:
                                                if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':
                                                    # taxes = order_line.tax_id.name
                                                    # if taxes:
                                                    #     taxes = taxes.rstrip(taxes[-1])
                                                    taxes = 0
                                                    if order_line.tax_id:
                                                        taxes = int(order_line.tax_id.amount)
                                                    result = order_line.price_subtotal * int(taxes) / 100
                                                    total = result + order_line.price_subtotal
                                                    if total >= promotion_product.rule_minimum_amount:
                                                        if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                            promotion_product.remaining_use_promotion = promotion_product.maximum_use_number - 1
                                                            minim_qty = 1
                                                            if promotion_product.rule_min_quantity > 0:
                                                                minim_qty = int((int(order_line.product_uom_qty)/promotion_product.rule_min_quantity))
                                                            elif promotion_product.rule_minimum_amount > 0:
                                                                minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                            reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                            if order_line.is_promotion == False:
                                                                product.append((0, 0, {
                                                                    'is_promotion' : True,
                                                                    # 'product_id': promotion_product.discount_line_product_id.id,
                                                                    'product_id': promotion_product.reward_product_id.id,
                                                                    # 'name': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                                    # 'name': promotion_product.reward_product_desc+' - '+promotion_product.reward_product_id.name,
                                                                    'name': promotion_product.reward_product_desc,
                                                                    'product_uom_qty': reward_qty,
                                                                    'price_unit': 0, }))
                                                                order_line.is_promotion = True
                                                        elif promotion_product.maximum_use_number == 0:
                                                            minim_qty = 1
                                                            if promotion_product.rule_min_quantity > 0:
                                                                minim_qty = int((int(order_line.product_uom_qty)/promotion_product.rule_min_quantity))
                                                            elif promotion_product.rule_minimum_amount > 0:
                                                                minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                            reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                            if order_line.is_promotion == False:
                                                                product.append((0, 0, {
                                                                    'is_promotion': True,
                                                                    # 'product_id': promotion_product.discount_line_product_id.id,
                                                                    'product_id': promotion_product.reward_product_id.id,
                                                                    # 'name': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                                    # 'name': promotion_product.reward_product_desc+' - '+promotion_product.reward_product_id.name,
                                                                    'name': promotion_product.reward_product_desc,
                                                                    'product_uom_qty': reward_qty,
                                                                    'price_unit': 0, }))
                                                                order_line.is_promotion = True

                                                elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':
                                                    total = order_line.price_subtotal
                                                    if total >= promotion_product.rule_minimum_amount:
                                                        if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                            promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1
                                                            minim_qty = 1
                                                            if promotion_product.rule_min_quantity > 0:
                                                                minim_qty = int((int(order_line.product_uom_qty)/promotion_product.rule_min_quantity))
                                                            elif promotion_product.rule_minimum_amount > 0:
                                                                minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                            reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                            if order_line.is_promotion == False:
                                                                product.append((0, 0, {
                                                                    'is_promotion': True,
                                                                    # 'product_id': promotion_product.discount_line_product_id.id,
                                                                    'product_id': promotion_product.reward_product_id.id,
                                                                    # 'name': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                                    # 'name': promotion_product.reward_product_desc+' - '+promotion_product.reward_product_id.name,
                                                                    'name': promotion_product.reward_product_desc,
                                                                    'product_uom_qty': reward_qty,
                                                                    'price_unit': 0, }))
                                                                order_line.is_promotion = True
                                                        elif promotion_product.maximum_use_number == 0:
                                                            minim_qty = 1
                                                            if promotion_product.rule_min_quantity > 0:
                                                                minim_qty = int((int(order_line.product_uom_qty)/promotion_product.rule_min_quantity))
                                                            elif promotion_product.rule_minimum_amount > 0:
                                                                minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                            reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                            if order_line.is_promotion == False:
                                                                product.append((0, 0, {
                                                                    'is_promotion': True,
                                                                    # 'product_id': promotion_product.discount_line_product_id.id,
                                                                    'product_id': promotion_product.reward_product_id.id,
                                                                    # 'name': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                                    # 'name': promotion_product.reward_product_desc+' - '+promotion_product.reward_product_id.name,
                                                                    'name': promotion_product.reward_product_desc,
                                                                    'product_uom_qty': reward_qty,
                                                                    'price_unit': 0, }))
                                                                order_line.is_promotion = True
                        else:
                            for product_ids_list in promotion_product.product_ids:
                                # filter = promotion_product.filtered(lambda r: product_ids_list.id == rec.product_id.id)
                                free_product = product_ids_list.id
                                customer = []
                                for customer_id in promotion_product.rule_partners_domain:
                                    customer = customer_id.id
                                    if order_line.product_id.id == free_product and customer == self.partner_id.id and ((promotion_product.rule_min_quantity > 0 and int(order_line.product_uom_qty) >= promotion_product.rule_min_quantity) or (promotion_product.rule_minimum_amount > 0 and order_line.price_subtotal  >= promotion_product.rule_minimum_amount )):
                                        if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':
                                            # taxes = order_line.tax_id.name
                                            # if taxes:
                                            #     taxes = taxes.rstrip(taxes[-1])
                                            taxes = 0
                                            if order_line.tax_id:
                                                taxes = int(order_line.tax_id.amount)
                                            result = order_line.price_subtotal * int(taxes) / 100
                                            total = result + order_line.price_subtotal
                                            if total >= promotion_product.rule_minimum_amount :
                                                if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                    promotion_product.remaining_use_promotion = promotion_product.maximum_use_number - 1
                                                    minim_qty = 1
                                                    if promotion_product.rule_min_quantity > 0:
                                                        minim_qty = int((int(order_line.product_uom_qty)/promotion_product.rule_min_quantity))
                                                    elif promotion_product.rule_minimum_amount > 0:
                                                        minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                    reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                    if order_line.is_promotion == False:
                                                        product.append((0, 0, {
                                                            'is_promotion': True,
                                                            # 'product_id': promotion_product.discount_line_product_id.id,
                                                            'product_id': promotion_product.reward_product_id.id,
                                                            # 'name': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                            # 'name': promotion_product.reward_product_desc+' - '+promotion_product.reward_product_id.name,
                                                            'name': promotion_product.reward_product_desc,
                                                            'product_uom_qty': reward_qty,
                                                            'price_unit': 0, }))
                                                        order_line.is_promotion = True
                                                elif promotion_product.maximum_use_number == 0:
                                                    minim_qty = 1
                                                    if promotion_product.rule_min_quantity > 0:
                                                        minim_qty = int((int(order_line.product_uom_qty)/promotion_product.rule_min_quantity))
                                                    elif promotion_product.rule_minimum_amount > 0:
                                                        minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                    reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                    if order_line.is_promotion == False:
                                                        product.append((0, 0, {
                                                            'is_promotion': True,
                                                            # 'product_id': promotion_product.discount_line_product_id.id,
                                                            'product_id': promotion_product.reward_product_id.id,
                                                            # 'name': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                            # 'name': promotion_product.reward_product_desc+' - '+promotion_product.reward_product_id.name,
                                                            'name': promotion_product.reward_product_desc,
                                                            'product_uom_qty': reward_qty,
                                                            'price_unit': 0, }))
                                                        order_line.is_promotion = True

                                        elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':
                                            total = order_line.price_subtotal
                                            if total >= promotion_product.rule_minimum_amount:
                                                if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                    promotion_product.remaining_use_promotion = promotion_product.maximum_use_number - 1
                                                    minim_qty = 1
                                                    if promotion_product.rule_min_quantity > 0:
                                                        minim_qty = int((int(order_line.product_uom_qty)/promotion_product.rule_min_quantity))
                                                    elif promotion_product.rule_minimum_amount > 0:
                                                        minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                    reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                    if order_line.is_promotion == False:
                                                        product.append((0, 0, {
                                                            'is_promotion': True,
                                                            # 'product_id': promotion_product.discount_line_product_id.id,
                                                            'product_id': promotion_product.reward_product_id.id,
                                                            # 'name': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                            # 'name': promotion_product.reward_product_desc+' - '+promotion_product.reward_product_id.name,
                                                            'name': promotion_product.reward_product_desc,
                                                            'product_uom_qty': reward_qty,
                                                            'price_unit': 0, }))
                                                        order_line.is_promotion = True
                                                elif promotion_product.maximum_use_number == 0:
                                                    minim_qty = 1
                                                    if promotion_product.rule_min_quantity > 0:
                                                        minim_qty = int((int(order_line.product_uom_qty)/promotion_product.rule_min_quantity))
                                                    elif promotion_product.rule_minimum_amount > 0:
                                                        minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                    reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                    if order_line.is_promotion == False:
                                                        product.append((0, 0, {
                                                            'is_promotion': True,
                                                            # 'product_id': promotion_product.discount_line_product_id.id,
                                                            'product_id': promotion_product.reward_product_id.id,
                                                            # 'name': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                            # 'name': promotion_product.reward_product_desc+' - '+promotion_product.reward_product_id.name,
                                                            'name': promotion_product.reward_product_desc,
                                                            'product_uom_qty': reward_qty,
                                                            'price_unit': 0, }))
                                                        order_line.is_promotion = True
                    elif promotion_product.rule_partners_domain:
                        if promotion_product.rule_date_from and promotion_product.rule_date_to:
                            for customer_id in promotion_product.rule_partners_domain:
                                customer = customer_id.id

                                if customer == self.partner_id.id and ((promotion_product.rule_min_quantity > 0 and int(order_line.product_uom_qty) >= promotion_product.rule_min_quantity) or (promotion_product.rule_minimum_amount > 0 and order_line.price_subtotal  >= promotion_product.rule_minimum_amount )):
                                        date_order = datetime.strptime(str(self.date_order),
                                                                       "%Y-%m-%d %H:%M:%S")
                                        start_date = datetime.strptime(str(promotion_product.rule_date_from),
                                                                       "%Y-%m-%d %H:%M:%S")
                                        end_date = datetime.strptime(str(promotion_product.rule_date_to),
                                                                     "%Y-%m-%d %H:%M:%S")

                                        if date_order <= end_date and date_order >= start_date:
                                            if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':
                                                # taxes = order_line.tax_id.name
                                                # if taxes:
                                                #     taxes = taxes.rstrip(taxes[-1])
                                                taxes = 0
                                                if order_line.tax_id:
                                                    taxes = int(order_line.tax_id.amount)
                                                result = order_line.price_subtotal * int(taxes) / 100
                                                total = result + order_line.price_subtotal
                                                if total >= promotion_product.rule_minimum_amount:
                                                    if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                        promotion_product.remaining_use_promotion = promotion_product.maximum_use_number - 1
                                                        minim_qty = 1
                                                        if promotion_product.rule_min_quantity > 0:
                                                            minim_qty = int((int(order_line.product_uom_qty)/promotion_product.rule_min_quantity))
                                                        elif promotion_product.rule_minimum_amount > 0:
                                                            minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                        reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                        if order_line.is_promotion == False:
                                                            product.append((0, 0, {
                                                                'is_promotion': True,
                                                                # 'product_id': promotion_product.discount_line_product_id.id,
                                                                'product_id': promotion_product.reward_product_id.id,
                                                                # 'name': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                                # 'name': promotion_product.reward_product_desc+' - '+promotion_product.reward_product_id.name,
                                                                'name': promotion_product.reward_product_desc,
                                                                'product_uom_qty': reward_qty,
                                                                'price_unit': 0, }))
                                                            order_line.is_promotion = True
                                                    elif promotion_product.maximum_use_number == 0:
                                                        minim_qty = 1
                                                        if promotion_product.rule_min_quantity > 0:
                                                            minim_qty = int((int(order_line.product_uom_qty)/promotion_product.rule_min_quantity))
                                                        elif promotion_product.rule_minimum_amount > 0:
                                                            minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                        reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                        if order_line.is_promotion == False:
                                                            product.append((0, 0, {
                                                                'is_promotion': True,
                                                                # 'product_id': promotion_product.discount_line_product_id.id,
                                                                'product_id': promotion_product.reward_product_id.id,
                                                                # 'name': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                                # 'name': promotion_product.reward_product_desc+' - '+promotion_product.reward_product_id.name,
                                                                'name': promotion_product.reward_product_desc,
                                                                'product_uom_qty': reward_qty,
                                                                'price_unit': 0, }))
                                                            order_line.is_promotion = True

                                            elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':
                                                total = order_line.price_subtotal
                                                if total >= promotion_product.rule_minimum_amount:
                                                    if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                        promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1
                                                        minim_qty = 1
                                                        if promotion_product.rule_min_quantity > 0:
                                                            minim_qty = int((int(order_line.product_uom_qty)/promotion_product.rule_min_quantity))
                                                        elif promotion_product.rule_minimum_amount > 0:
                                                            minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                        reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                        if order_line.is_promotion == False:
                                                            product.append((0, 0, {
                                                                'is_promotion': True,
                                                                # 'product_id': promotion_product.discount_line_product_id.id,
                                                                'product_id': promotion_product.reward_product_id.id,
                                                                # 'name': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                                # 'name': promotion_product.reward_product_desc+' - '+promotion_product.reward_product_id.name,
                                                                'name': promotion_product.reward_product_desc,
                                                                'product_uom_qty': reward_qty,
                                                                'price_unit': 0, }))
                                                            order_line.is_promotion = True
                                                    elif promotion_product.maximum_use_number == 0:
                                                        minim_qty = 1
                                                        if promotion_product.rule_min_quantity > 0:
                                                            minim_qty = int((int(order_line.product_uom_qty)/promotion_product.rule_min_quantity))
                                                        elif promotion_product.rule_minimum_amount > 0:
                                                            minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                        reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                        if order_line.is_promotion == False:
                                                            product.append((0, 0, {
                                                                'is_promotion': True,
                                                                # 'product_id': promotion_product.discount_line_product_id.id,
                                                                'product_id': promotion_product.reward_product_id.id,
                                                                # 'name': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                                # 'name': promotion_product.reward_product_desc+' - '+promotion_product.reward_product_id.name,
                                                                'name': promotion_product.reward_product_desc,
                                                                'product_uom_qty': reward_qty,
                                                                'price_unit': 0, }))
                                                            order_line.is_promotion = True
                        else:
                            for customer_id in promotion_product.rule_partners_domain:
                                customer = customer_id.id
                                if customer == self.partner_id.id and ((promotion_product.rule_min_quantity > 0 and int(order_line.product_uom_qty) >= promotion_product.rule_min_quantity) or (promotion_product.rule_minimum_amount > 0 and order_line.price_subtotal  >= promotion_product.rule_minimum_amount )):
                                    if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':
                                        # taxes = order_line.tax_id.name
                                        # if taxes:
                                        #     taxes = taxes.rstrip(taxes[-1])
                                        taxes = 0
                                        if order_line.tax_id:
                                            taxes = int(order_line.tax_id.amount)
                                        result = order_line.price_subtotal * int(taxes) / 100
                                        total = result + order_line.price_subtotal
                                        if total >= promotion_product.rule_minimum_amount :
                                            if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                promotion_product.remaining_use_promotion = promotion_product.maximum_use_number - 1
                                                minim_qty = 1
                                                if promotion_product.rule_min_quantity > 0:
                                                    minim_qty = int((int(order_line.product_uom_qty)/promotion_product.rule_min_quantity))
                                                elif promotion_product.rule_minimum_amount > 0:
                                                    minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                if order_line.is_promotion == False:
                                                    product.append((0, 0, {
                                                        'is_promotion': True,
                                                        # 'product_id': promotion_product.discount_line_product_id.id,
                                                         'product_id': promotion_product.reward_product_id.id,
                                                            # 'name': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                            # 'name': promotion_product.reward_product_desc+' - '+promotion_product.reward_product_id.name,
                                                        'name': promotion_product.reward_product_desc,
                                                        'product_uom_qty': reward_qty,
                                                        'price_unit': 0, }))
                                                    order_line.is_promotion = True
                                            elif promotion_product.maximum_use_number == 0:
                                                minim_qty = 1
                                                if promotion_product.rule_min_quantity > 0:
                                                    minim_qty = int((int(order_line.product_uom_qty)/promotion_product.rule_min_quantity))
                                                elif promotion_product.rule_minimum_amount > 0:
                                                    minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                if order_line.is_promotion == False:
                                                    product.append((0, 0, {
                                                        'is_promotion': True,
                                                        # 'product_id': promotion_product.discount_line_product_id.id,
                                                        'product_id': promotion_product.reward_product_id.id,
                                                        # 'name': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                        # 'name': promotion_product.reward_product_desc+' - '+promotion_product.reward_product_id.name,
                                                        'name': promotion_product.reward_product_desc,
                                                        'product_uom_qty': reward_qty,
                                                        'price_unit': 0, }))
                                                    order_line.is_promotion = True

                                    elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':
                                        total = order_line.price_subtotal
                                        if total >= promotion_product.rule_minimum_amount:
                                            if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                promotion_product.remaining_use_promotion = promotion_product.maximum_use_number - 1
                                                minim_qty = 1
                                                if promotion_product.rule_min_quantity > 0:
                                                    minim_qty = int((int(order_line.product_uom_qty)/promotion_product.rule_min_quantity))
                                                elif promotion_product.rule_minimum_amount > 0:
                                                    minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                if order_line.is_promotion == False:
                                                    product.append((0, 0, {
                                                        'is_promotion': True,
                                                        # 'product_id': promotion_product.discount_line_product_id.id,
                                                        'product_id': promotion_product.reward_product_id.id,
                                                        # 'name': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                        # 'name': promotion_product.reward_product_desc+' - '+promotion_product.reward_product_id.name,
                                                        'name': promotion_product.reward_product_desc,
                                                        'product_uom_qty': reward_qty,
                                                        'price_unit': 0, }))
                                                    order_line.is_promotion = True
                                            elif promotion_product.maximum_use_number == 0:
                                                minim_qty = 1
                                                if promotion_product.rule_min_quantity > 0:
                                                    minim_qty = int((int(order_line.product_uom_qty)/promotion_product.rule_min_quantity))
                                                elif promotion_product.rule_minimum_amount > 0:
                                                    minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                if order_line.is_promotion == False:
                                                    product.append((0, 0, {
                                                        'is_promotion': True,
                                                        # 'product_id': promotion_product.discount_line_product_id.id,
                                                        'product_id': promotion_product.reward_product_id.id,
                                                        # 'name': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                        # 'name': promotion_product.reward_product_desc+' - '+promotion_product.reward_product_id.name,
                                                        'name': promotion_product.reward_product_desc,
                                                        'product_uom_qty': reward_qty,
                                                        'price_unit': 0, }))
                                                    order_line.is_promotion = True
                    elif promotion_product.product_ids:
                        if promotion_product.rule_date_from and promotion_product.rule_date_to:
                            for product_ids_list in promotion_product.product_ids:
                                # filter = promotion_product.filtered(lambda r: product_ids_list.id == rec.product_id.id)
                                free_product = product_ids_list.id

                                if order_line.product_id.id == free_product and ((promotion_product.rule_min_quantity > 0 and int(order_line.product_uom_qty) >= promotion_product.rule_min_quantity) or (promotion_product.rule_minimum_amount > 0 and order_line.price_subtotal  >= promotion_product.rule_minimum_amount )):
                                    date_order = datetime.strptime(str(self.date_order),
                                                                   "%Y-%m-%d %H:%M:%S")
                                    start_date = datetime.strptime(str(promotion_product.rule_date_from),
                                                                   "%Y-%m-%d %H:%M:%S")
                                    end_date = datetime.strptime(str(promotion_product.rule_date_to),
                                                                 "%Y-%m-%d %H:%M:%S")

                                    if date_order <= end_date and date_order >= start_date:
                                        if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':
                                            # taxes = order_line.tax_id.name
                                            # if taxes:
                                            #     taxes = taxes.rstrip(taxes[-1])
                                            taxes = 0
                                            if order_line.tax_id:
                                                taxes = int(order_line.tax_id.amount)
                                            result = order_line.price_subtotal * int(taxes) / 100
                                            total = result + order_line.price_subtotal

                                            if total >= promotion_product.rule_minimum_amount:
                                                if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                    promotion_product.remaining_use_promotion = promotion_product.maximum_use_number - 1
                                                    minim_qty = 1
                                                    if promotion_product.rule_min_quantity > 0:
                                                        minim_qty = int((int(order_line.product_uom_qty)/promotion_product.rule_min_quantity))
                                                    elif promotion_product.rule_minimum_amount > 0:
                                                        minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                    reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                    if order_line.is_promotion == False:
                                                        product.append((0, 0, {
                                                            'is_promotion': True,
                                                            # 'product_id': promotion_product.discount_line_product_id.id,
                                                            'product_id': promotion_product.reward_product_id.id,
                                                            # 'name': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                            # 'name': promotion_product.reward_product_desc+' - '+promotion_product.reward_product_id.name,
                                                            'name': promotion_product.reward_product_desc,
                                                            'product_uom_qty': reward_qty,
                                                            'price_unit': 0, }))
                                                        order_line.is_promotion = True
                                                elif promotion_product.maximum_use_number == 0:
                                                    # print("TOTAL", total)
                                                    minim_qty = 1
                                                    if promotion_product.rule_min_quantity > 0:
                                                        minim_qty = int((int(order_line.product_uom_qty)/promotion_product.rule_min_quantity))
                                                    elif promotion_product.rule_minimum_amount > 0:
                                                        minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                    reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                    if order_line.is_promotion == False:
                                                        product.append((0, 0, {
                                                            'is_promotion': True,
                                                            # 'product_id': promotion_product.discount_line_product_id.id,
                                                            'product_id': promotion_product.reward_product_id.id,
                                                            # 'name': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                            # 'name': promotion_product.reward_product_desc+' - '+promotion_product.reward_product_id.name,
                                                            'name': promotion_product.reward_product_desc,
                                                            'product_uom_qty': reward_qty,
                                                            'price_unit': 0, }))
                                                        order_line.is_promotion = True

                                        elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':
                                            total = order_line.price_subtotal
                                            if total >= promotion_product.rule_minimum_amount:
                                                if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                    promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1
                                                    minim_qty = 1
                                                    if promotion_product.rule_min_quantity > 0:
                                                        minim_qty = int((int(order_line.product_uom_qty)/promotion_product.rule_min_quantity))
                                                    elif promotion_product.rule_minimum_amount > 0:
                                                        minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                    reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                    if order_line.is_promotion == False:
                                                        product.append((0, 0, {
                                                            'is_promotion': True,
                                                            # 'product_id': promotion_product.discount_line_product_id.id,
                                                            'product_id': promotion_product.reward_product_id.id,
                                                            # 'name': promotion_product.discount_line_product_id.name + '(Main product' + ' : ' + (product_ids_list.name) + ')',
                                                            # 'name': promotion_product.reward_product_desc+' - '+promotion_product.reward_product_id.name,
                                                            'name': promotion_product.reward_product_desc,
                                                            'product_uom_qty': reward_qty,
                                                            'price_unit': 0, }))
                                                        order_line.is_promotion = True
                                                elif promotion_product.maximum_use_number == 0:
                                                    minim_qty = 1
                                                    if promotion_product.rule_min_quantity > 0:
                                                        minim_qty = int((int(order_line.product_uom_qty)/promotion_product.rule_min_quantity))
                                                    elif promotion_product.rule_minimum_amount > 0:
                                                        minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                    reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                    if order_line.is_promotion == False:
                                                        product.append((0, 0, {
                                                            'is_promotion': True,
                                                            # 'product_id': promotion_product.discount_line_product_id.id,
                                                            'product_id': promotion_product.reward_product_id.id,
                                                            # 'name': promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                            # 'name': promotion_product.reward_product_desc+' - '+promotion_product.reward_product_id.name,
                                                            'name': promotion_product.reward_product_desc,
                                                            'product_uom_qty': reward_qty,
                                                            'price_unit': 0, }))
                                                        order_line.is_promotion = True
                        else:
                            for product_ids_list in promotion_product.product_ids:
                                # print("TANPA TANGGAL")
                                # filter = promotion_product.filtered(lambda r: product_ids_list.id == rec.product_id.id)
                                free_product = product_ids_list.id
                                customer = []

                                if order_line.product_id.id == free_product and ((promotion_product.rule_min_quantity > 0 and int(order_line.product_uom_qty) >= promotion_product.rule_min_quantity) or (promotion_product.rule_minimum_amount > 0 and order_line.price_subtotal  >= promotion_product.rule_minimum_amount )):
                                    # print("masuk sini")
                                    if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':
                                        # taxes = order_line.tax_id.name
                                        # if taxes:
                                        #     taxes = taxes.rstrip(taxes[-1])
                                        taxes = 0
                                        if order_line.tax_id:
                                            taxes = int(order_line.tax_id.amount)
                                        result = order_line.price_subtotal * int(taxes) / 100
                                        total = result + order_line.price_subtotal
                                        if total >= promotion_product.rule_minimum_amount :
                                            if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                promotion_product.remaining_use_promotion = promotion_product.maximum_use_number - 1
                                                minim_qty = 1
                                                if promotion_product.rule_min_quantity > 0:
                                                    minim_qty = int((int(order_line.product_uom_qty)/promotion_product.rule_min_quantity))
                                                elif promotion_product.rule_minimum_amount > 0:
                                                    minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                if order_line.is_promotion == False:
                                                    product.append((0, 0, {
                                                        'is_promotion': True,
                                                        # 'product_id': promotion_product.discount_line_product_id.id,
                                                        'product_id': promotion_product.reward_product_id.id,
                                                         # 'name' : promotion_product.discount_line_product_id.name + '- ' + (product_ids_list.name),
                                                        # 'name': promotion_product.reward_product_desc+' - '+promotion_product.reward_product_id.name,
                                                        'name': promotion_product.reward_product_desc,
                                                        'product_uom_qty': reward_qty,
                                                        'price_unit': 0, }))
                                                    order_line.is_promotion = True
                                            elif promotion_product.maximum_use_number == 0:
                                                minim_qty = 1
                                                if promotion_product.rule_min_quantity > 0:
                                                    minim_qty = int((int(order_line.product_uom_qty)/promotion_product.rule_min_quantity))
                                                elif promotion_product.rule_minimum_amount > 0:
                                                    minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                if order_line.is_promotion == False:
                                                    product.append((0, 0, {
                                                        'is_promotion': True,
                                                        # 'product_id': promotion_product.discount_line_product_id.id,
                                                        'product_id': promotion_product.reward_product_id.id,
                                                        # 'name': promotion_product.reward_product_desc+' - '+promotion_product.reward_product_id.name,
                                                        'name': promotion_product.reward_product_desc,
                                                        'product_uom_qty': reward_qty,
                                                        'price_unit': 0, }))
                                                    order_line.is_promotion = True

                                    elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':
                                            total = order_line.price_subtotal
                                            if total >= promotion_product.rule_minimum_amount:
                                                if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                    promotion_product.remaining_use_promotion = promotion_product.maximum_use_number - 1
                                                    minim_qty = 1
                                                    if promotion_product.rule_min_quantity > 0:
                                                        minim_qty = int((int(order_line.product_uom_qty)/promotion_product.rule_min_quantity))
                                                    elif promotion_product.rule_minimum_amount > 0:
                                                        minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                    reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                    if order_line.is_promotion == False:
                                                        product.append((0, 0, {
                                                            'is_promotion': True,
                                                            # 'product_id': promotion_product.discount_line_product_id.id,
                                                            'product_id': promotion_product.reward_product_id.id,
                                                            # 'name': promotion_product.discount_line_product_id.name + '(Main product' + ' : ' + (product_ids_list.name) + ')',
                                                            # 'name': promotion_product.reward_product_desc+' - '+promotion_product.reward_product_id.name,
                                                            'name': promotion_product.reward_product_desc,
                                                            'product_uom_qty': reward_qty,
                                                            'price_unit': 0, }))
                                                        order_line.is_promotion = True
                                                elif promotion_product.maximum_use_number == 0:
                                                    minim_qty = 1
                                                    if promotion_product.rule_min_quantity > 0:
                                                        minim_qty = int((int(order_line.product_uom_qty)/promotion_product.rule_min_quantity))
                                                    elif promotion_product.rule_minimum_amount > 0:
                                                        minim_qty = int((int(total)/promotion_product.rule_minimum_amount))
                                                    reward_qty = int(minim_qty*promotion_product.reward_product_quantity)
                                                    if order_line.is_promotion == False:
                                                        product.append((0, 0, {
                                                            'is_promotion': True,
                                                            # 'product_id': promotion_product.discount_line_product_id.id,
                                                            'product_id': promotion_product.reward_product_id.id,
                                                            # 'name': promotion_product.discount_line_product_id.name + '(Main product' + ' : ' + (product_ids_list.name) + ')',
                                                            # 'name': promotion_product.reward_product_desc+' - '+promotion_product.reward_product_id.name,
                                                            'name': promotion_product.reward_product_desc,
                                                            'product_uom_qty': reward_qty,
                                                            'price_unit': 0, }))
                                                        order_line.is_promotion = True
            if promotion_product.reward_type == 'discount':
                if promotion_product.rule_partners_domain and promotion_product.product_ids:
                    product_ids_update = []
                    for ids in promotion_product.product_ids:
                        product_ids_update.append(ids.id)
                    if promotion_product.rule_date_from and promotion_product.rule_date_to:
                        for product_ids_list in promotion_product.product_ids:
                            # filter = promotion_product.filtered(lambda r: product_ids_list.id == rec.product_id.id)
                            free_product = product_ids_list.id
                            for customer_id in promotion_product.rule_partners_domain:
                                customer = customer_id.id
                                for order_line in self.order_line:
                                    if order_line.product_id.id == free_product and customer == self.partner_id.id and ((promotion_product.rule_min_quantity > 0 and int(order_line.product_uom_qty) >= promotion_product.rule_min_quantity) or (promotion_product.rule_minimum_amount > 0 and order_line.price_subtotal  >= promotion_product.rule_minimum_amount )):

                                        date_order = datetime.strptime(str(self.date_order),
                                                                       "%Y-%m-%d %H:%M:%S")
                                        start_date = datetime.strptime(str(promotion_product.rule_date_from),
                                                                       "%Y-%m-%d %H:%M:%S")
                                        end_date = datetime.strptime(str(promotion_product.rule_date_to),
                                                                     "%Y-%m-%d %H:%M:%S")
                                        if date_order <= end_date and date_order >= start_date:
                                            if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':
                                                # taxes = order_line.tax_id.name
                                                # if taxes:
                                                #     taxes = taxes.rstrip(taxes[-1])
                                                taxes = 0
                                                if order_line.tax_id:
                                                    taxes = int(order_line.tax_id.amount)
                                                result = order_line.price_subtotal * int(taxes) / 100
                                                total = result + order_line.price_subtotal
                                                if total >= promotion_product.rule_minimum_amount:
                                                    if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                        promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1

                                                        if promotion_product.discount_type == 'percentage':
                                                            if promotion_product.discount_apply_on == 'specific_products':

                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                result_ = -diskon_percentage
                                                                po_line = self.env['sale.order.line'].sudo()
                                                                # taxes = order_line.tax_id.name
                                                                # if taxes:
                                                                #     taxes = taxes.rstrip(taxes[-1])
                                                                taxes = 0
                                                                if order_line.tax_id:
                                                                    taxes = int(order_line.tax_id.amount)
                                                                subtotal = order_line.price_subtotal * int(
                                                                    taxes) / 100
                                                                result_subt_total = order_line.price_subtotal + subtotal

                                                                for i in promotion_product.discount_specific_product_ids:
                                                                    disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                    if disc_product_id:
                                                                        if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                                if order_line.price_unit > promotion_product.discount_max_amount:

                                                                                    order_line.write({
                                                                                        'is_discount': True,
                                                                                        'discount_amount': promotion_product.discount_max_amount
                                                                                    })
                                                                                    # vals = {
                                                                                    #     'order_id': self.id,
                                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                    #     'price_unit': promotion_product.discount_max_amount,
                                                                                    #     'price_subtotal': result_subt_total,
                                                                                    # }
                                                                                    # if i.name not in self.order_line.mapped(
                                                                                    #         'description_product'):
                                                                                    #     po_line.create(vals)

                                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                    order_line.write({
                                                                                        'is_discount': True,
                                                                                        'discount': promotion_product.discount_percentage
                                                                                    })
                                                                                    # vals = {
                                                                                    #     'order_id': self.id,
                                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                    #     'price_unit': result_,
                                                                                    #     'price_subtotal': result_subt_total,
                                                                                    # }
                                                                                    # if i.name not in self.order_line.mapped(
                                                                                    #         'description_product'):
                                                                                    #     po_line.create(vals)
                                                                            elif int(
                                                                                    promotion_product.discount_max_amount) == 0:
                                                                                # print("DISKON amount 0")

                                                                                order_line.write({
                                                                                    'is_discount': True,
                                                                                    'discount': promotion_product.discount_percentage
                                                                                })
                                                                                # vals = {
                                                                                #     'order_id': self.id,
                                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                #     'price_unit': result_,
                                                                                #     'price_subtotal': result_subt_total,
                                                                                # }
                                                                                # if i.name not in self.order_line.mapped(
                                                                                #         'description_product'):
                                                                                #     po_line.create(vals)


                                                            elif promotion_product.discount_apply_on == 'cheapest_product':
                                                                product_list_update = self.env['sale.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])
                                                                # min_price = min(
                                                                #     self.order_line.mapped('price_unit'))
                                                                min_price = min(
                                                                    product_list_update.mapped('price_unit'))
                                                                po_line = self.env['sale.order.line'].sudo()
                                                                product_min_price = self.order_line.filtered(
                                                                    lambda r: r.price_unit == min_price)
                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                        # taxes = order_line.tax_id.name
                                                                        # if taxes:
                                                                        #     taxes = taxes.rstrip(taxes[-1])
                                                                        taxes = 0
                                                                        if order_line.tax_id:
                                                                            taxes = int(order_line.tax_id.amount)
                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit

                                                                        for i in product_min_price:
                                                                            i.write({
                                                                                'is_discount': True,
                                                                                'discount_amount': promotion_product.discount_max_amount
                                                                            })
                                                                        #     vals = {
                                                                        #         'order_id': self.id,
                                                                        #         'price_subtotal': resultsubtotal,
                                                                        #         'product_id': promotion_product.discount_line_product_id.id,
                                                                        #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                        #         'price_unit': promotion_product.discount_max_amount,
                                                                        #
                                                                        #     }
                                                                        #
                                                                        # if i.product_id.name not in self.order_line.mapped(
                                                                        #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                        #         'product_id').ids:
                                                                        #     po_line.create(vals)

                                                                    elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                        additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                        # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                        dis_res = order_line.harga_satuan_baru
                                                                        disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                        chepest_result = -diskon_percentage
                                                                        # taxes = order_line.tax_id.name
                                                                        # if taxes:
                                                                        #     taxes = taxes.rstrip(taxes[-1])
                                                                        taxes = 0
                                                                        if order_line.tax_id:
                                                                            taxes = int(order_line.tax_id.amount)
                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit

                                                                        for i in product_min_price:
                                                                            # i.write({'discount': promotion_product.discount_percentage})
                                                                            i.write({
                                                                                'is_discount': True,
                                                                                'discount_amount': disc_amount
                                                                            })
                                                                        #     vals = {
                                                                        #         'order_id': self.id,
                                                                        #         'price_subtotal': resultsubtotal,
                                                                        #         'product_id': promotion_product.discount_line_product_id.id,
                                                                        #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                        #         'price_unit': chepest_result,
                                                                        #
                                                                        #     }
                                                                        #
                                                                        # if i.product_id.name not in self.order_line.mapped(
                                                                        #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                        #     'product_id').ids:
                                                                        #     po_line.create(vals)

                                                                elif int(
                                                                        promotion_product.discount_max_amount) == 0:
                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    chepest_result = -diskon_percentage
                                                                    # taxes = order_line.tax_id.name
                                                                    # if taxes:
                                                                    #     taxes = taxes.rstrip(taxes[-1])
                                                                    taxes = 0
                                                                    if order_line.tax_id:
                                                                        taxes = int(order_line.tax_id.amount)

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({
                                                                            'is_discount': True,
                                                                            'discount_amount': disc_amount
                                                                        })
                                                                    #     vals = {
                                                                    #         'order_id': self.id,
                                                                    #         'price_subtotal': resultsubtotal,
                                                                    #         'product_id': promotion_product.discount_line_product_id.id,
                                                                    #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    #         'price_unit': chepest_result,
                                                                    #
                                                                    #     }
                                                                    #
                                                                    # if i.product_id.name not in self.order_line.mapped(
                                                                    #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    #     'product_id').ids:
                                                                    #     po_line.create(vals)

                                                            elif promotion_product.discount_apply_on == 'on_order':

                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if order_line.price_unit > promotion_product.discount_max_amount:
                                                                        po_line = self.env[
                                                                            'sale.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        on_order = -diskon_percentage
                                                                        # taxes = order_line.tax_id.name
                                                                        # if taxes:
                                                                        #     taxes = taxes.rstrip(taxes[-1])
                                                                        taxes = 0
                                                                        if order_line.tax_id:
                                                                            taxes = int(order_line.tax_id.amount)

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            i.write({
                                                                                'is_discount': True,
                                                                                'discount_amount': promotion_product.discount_max_amount
                                                                            })
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'price_subtotal': resultsubtotal,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                            #     'price_unit': promotion_product.discount_max_amount,
                                                                            #
                                                                            # }
                                                                            #
                                                                            # po_line.create(vals)
                                                                    elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                        po_line = self.env[
                                                                            'sale.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                        # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                        dis_res = order_line.harga_satuan_baru
                                                                        disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                        on_order = -diskon_percentage
                                                                        # taxes = order_line.tax_id.name
                                                                        # if taxes:
                                                                        #     taxes = taxes.rstrip(taxes[-1])
                                                                        taxes = 0
                                                                        if order_line.tax_id:
                                                                            taxes = int(order_line.tax_id.amount)
                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            # i.write({'discount': promotion_product.discount_percentage})
                                                                            i.write({
                                                                                'is_discount': True,
                                                                                'discount_amount': disc_amount
                                                                            })
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'price_subtotal': resultsubtotal,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                            #     'price_unit': on_order,
                                                                            #
                                                                            # }
                                                                            #
                                                                            # po_line.create(vals)
                                                                elif int(
                                                                        promotion_product.discount_max_amount) == 0:
                                                                    po_line = self.env[
                                                                        'sale.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    on_order = -diskon_percentage
                                                                    # taxes = order_line.tax_id.name
                                                                    # if taxes:
                                                                    #     taxes = taxes.rstrip(taxes[-1])
                                                                    taxes = 0
                                                                    if order_line.tax_id:
                                                                        taxes = int(order_line.tax_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({
                                                                            'is_discount': True,
                                                                            'discount_amount': disc_amount
                                                                        })
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #     'price_subtotal': resultsubtotal,
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        #     'price_unit': on_order,
                                                                        #
                                                                        # }
                                                                        #
                                                                        # po_line.create(vals)

                                                        elif promotion_product.discount_type == 'fixed_amount':

                                                            po_line = self.env['sale.order.line'].sudo()
                                                            order_line.write({
                                                                'is_discount': True,
                                                                'discount_amount': promotion_product.discount_fixed_amount
                                                            })

                                                            # vals = {
                                                            #     'order_id': self.id,
                                                            #     'product_id': order_line.product_id.id,
                                                            #     'description_product': 'fixed amount'+ ' ' + ' on product :' + ' ' + promotion_product.name,
                                                            #     'price_unit': promotion_product.discount_fixed_amount,
                                                            #
                                                            # }
                                                            # if promotion_product.name not in self.order_line.mapped(
                                                            #         'description_product'):
                                                            #     po_line.create(vals)

                                                    else:
                                                        if promotion_product.discount_type == 'percentage':
                                                            if promotion_product.discount_apply_on == 'specific_products':
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                result_ = -diskon_percentage
                                                                po_line = self.env['sale.order.line'].sudo()
                                                                # taxes = order_line.tax_id.name
                                                                # if taxes:
                                                                #     taxes = taxes.rstrip(taxes[-1])
                                                                taxes = 0
                                                                if order_line.tax_id:
                                                                    taxes = int(order_line.tax_id.amount)
                                                                subtotal = order_line.price_subtotal * int(
                                                                    taxes) / 100
                                                                result_subt_total = order_line.price_subtotal + subtotal

                                                                for i in promotion_product.discount_specific_product_ids:
                                                                    disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                    if disc_product_id:
                                                                        if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                                if order_line.price_unit > promotion_product.discount_max_amount:

                                                                                    order_line.write({
                                                                                        'is_discount': True,
                                                                                        'discount_amount': promotion_product.discount_max_amount
                                                                                    })
                                                                                    # vals = {
                                                                                    #     'order_id': self.id,
                                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                    #     'price_unit': promotion_product.discount_max_amount,
                                                                                    #     'price_subtotal': result_subt_total,
                                                                                    # }
                                                                                    # if i.name not in self.order_line.mapped(
                                                                                    #         'description_product'):
                                                                                    #     po_line.create(vals)

                                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                    order_line.write({
                                                                                        'is_discount': True,
                                                                                        'discount': promotion_product.discount_percentage
                                                                                    })
                                                                                    # vals = {
                                                                                    #     'order_id': self.id,
                                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                    #     'price_unit': result_,
                                                                                    #     'price_subtotal': result_subt_total,
                                                                                    # }
                                                                                    # if i.name not in self.order_line.mapped(
                                                                                    #         'description_product'):
                                                                                    #     po_line.create(vals)
                                                                            elif int(
                                                                                    promotion_product.discount_max_amount) == 0:

                                                                                order_line.write({
                                                                                    'is_discount': True,
                                                                                    'discount': promotion_product.discount_percentage
                                                                                })
                                                                                # vals = {
                                                                                #     'order_id': self.id,
                                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                #     'price_unit': result_,
                                                                                #     'price_subtotal': result_subt_total,
                                                                                # }
                                                                                # if i.name not in self.order_line.mapped(
                                                                                #         'description_product'):
                                                                                #     po_line.create(vals)

                                                            elif promotion_product.discount_apply_on == 'cheapest_product':
                                                                product_list_update = self.env['sale.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])
                                                                # min_price = min(
                                                                #     self.order_line.mapped('price_unit'))
                                                                min_price = min(
                                                                    product_list_update.mapped('price_unit'))
                                                                po_line = self.env['sale.order.line'].sudo()
                                                                product_min_price = self.order_line.filtered(
                                                                    lambda r: r.price_unit == min_price)
                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                        # taxes = order_line.tax_id.name
                                                                        # if taxes:
                                                                        #     taxes = taxes.rstrip(taxes[-1])
                                                                        taxes = 0
                                                                        if order_line.tax_id:
                                                                            taxes = int(order_line.tax_id.amount)
                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit
                                                                        for i in product_min_price:
                                                                            i.write({
                                                                                'is_discount': True,
                                                                                'discount_amount': promotion_product.discount_max_amount
                                                                            })
                                                                        #     vals = {
                                                                        #         'order_id': self.id,
                                                                        #         'price_subtotal': resultsubtotal,
                                                                        #         'product_id': promotion_product.discount_line_product_id.id,
                                                                        #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                        #         'price_unit': promotion_product.discount_max_amount,
                                                                        #
                                                                        #     }
                                                                        #
                                                                        # if i.product_id.name not in self.order_line.mapped(
                                                                        #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                        #         'product_id').ids:
                                                                        #     po_line.create(vals)

                                                                    elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                        additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                        # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                        dis_res = order_line.harga_satuan_baru
                                                                        disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                        chepest_result = -diskon_percentage
                                                                        # taxes = order_line.tax_id.name
                                                                        # if taxes:
                                                                        #     taxes = taxes.rstrip(taxes[-1])
                                                                        taxes = 0
                                                                        if order_line.tax_id:
                                                                            taxes = int(order_line.tax_id.amount)
                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit

                                                                        for i in product_min_price:
                                                                            # i.write({'discount': promotion_product.discount_percentage})
                                                                            i.write({
                                                                                'is_discount': True,
                                                                                'discount_amount': disc_amount
                                                                            })
                                                                        #     vals = {
                                                                        #         'order_id': self.id,
                                                                        #         'price_subtotal': resultsubtotal,
                                                                        #         'product_id': promotion_product.discount_line_product_id.id,
                                                                        #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                        #         'price_unit': chepest_result,
                                                                        #
                                                                        #     }
                                                                        #
                                                                        # if i.product_id.name not in self.order_line.mapped(
                                                                        #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                        #     'product_id').ids:
                                                                        #     po_line.create(vals)

                                                                elif int(
                                                                        promotion_product.discount_max_amount) == 0:
                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    chepest_result = -diskon_percentage
                                                                    # taxes = order_line.tax_id.name
                                                                    # if taxes:
                                                                    #     taxes = taxes.rstrip(taxes[-1])
                                                                    taxes = 0
                                                                    if order_line.tax_id:
                                                                        taxes = int(order_line.tax_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({
                                                                            'is_discount': True,
                                                                            'discount_amount': disc_amount
                                                                        })
                                                                    #     vals = {
                                                                    #         'order_id': self.id,
                                                                    #         'price_subtotal': resultsubtotal,
                                                                    #         'product_id': promotion_product.discount_line_product_id.id,
                                                                    #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    #         'price_unit': chepest_result,
                                                                    #
                                                                    #     }
                                                                    #
                                                                    # if i.product_id.name not in self.order_line.mapped(
                                                                    #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    #     'product_id').ids:
                                                                    #     po_line.create(vals)

                                                            elif promotion_product.discount_apply_on == 'on_order':

                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if order_line.price_unit > promotion_product.discount_max_amount:
                                                                        po_line = self.env[
                                                                            'sale.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        on_order = -diskon_percentage
                                                                        # taxes = order_line.tax_id.name
                                                                        # if taxes:
                                                                        #     taxes = taxes.rstrip(taxes[-1])
                                                                        taxes = 0
                                                                        if order_line.tax_id:
                                                                            taxes = int(order_line.tax_id.amount)
                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            i.write({
                                                                                'is_discount': True,
                                                                                'discount_amount': promotion_product.discount_max_amount
                                                                            })
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'price_subtotal': resultsubtotal,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                            #     'price_unit': promotion_product.discount_max_amount,
                                                                            #
                                                                            # }
                                                                            #
                                                                            # po_line.create(vals)
                                                                    elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                        po_line = self.env[
                                                                            'sale.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                        # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                        dis_res = order_line.harga_satuan_baru
                                                                        disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                        on_order = -diskon_percentage
                                                                        # taxes = order_line.tax_id.name
                                                                        # if taxes:
                                                                        #     taxes = taxes.rstrip(taxes[-1])
                                                                        taxes = 0
                                                                        if order_line.tax_id:
                                                                            taxes = int(order_line.tax_id.amount)
                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            # i.write({'discount': promotion_product.discount_percentage})
                                                                            i.write({
                                                                                'is_discount': True,
                                                                                'discount_amount': disc_amount
                                                                            })
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'price_subtotal': resultsubtotal,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                            #     'price_unit': on_order,
                                                                            #
                                                                            # }
                                                                            #
                                                                            # po_line.create(vals)
                                                                elif int(
                                                                        promotion_product.discount_max_amount) == 0:
                                                                    po_line = self.env[
                                                                        'sale.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    on_order = -diskon_percentage
                                                                    # taxes = order_line.tax_id.name
                                                                    # if taxes:
                                                                    #     taxes = taxes.rstrip(taxes[-1])
                                                                    taxes = 0
                                                                    if order_line.tax_id:
                                                                        taxes = int(order_line.tax_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({
                                                                            'is_discount': True,
                                                                            'discount_amount': disc_amount
                                                                        })
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #     'price_subtotal': resultsubtotal,
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        #     'price_unit': on_order,
                                                                        #
                                                                        # }
                                                                        #
                                                                        # po_line.create(vals)

                                                        elif promotion_product.discount_type == 'fixed_amount':

                                                            po_line = self.env['sale.order.line'].sudo()
                                                            order_line.write({'discount_amount': promotion_product.discount_fixed_amount})

                                                            # vals = {
                                                            #     'order_id': self.id,
                                                            #      'product_id': order_line.product_id.id,
                                                            #      'description_product': 'fixed amount'+ ' ' + ' on product :' + ' ' + promotion_product.name,
                                                            #     'price_unit': promotion_product.discount_fixed_amount,
                                                            #
                                                            # }
                                                            # if promotion_product.name not in self.order_line.mapped(
                                                            #         'description_product'):
                                                            #     po_line.create(vals)

                                            elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':

                                                total = order_line.price_subtotal
                                                if total >= promotion_product.rule_minimum_amount:
                                                    if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                        promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1

                                                        if promotion_product.discount_type == 'percentage':
                                                            if promotion_product.discount_apply_on == 'specific_products':
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                result_ = -diskon_percentage
                                                                po_line = self.env['sale.order.line'].sudo()
                                                                # taxes = order_line.tax_id.name
                                                                # if taxes:
                                                                #     taxes = taxes.rstrip(taxes[-1])
                                                                taxes = 0
                                                                if order_line.tax_id:
                                                                    taxes = int(order_line.tax_id.amount)
                                                                subtotal = order_line.price_subtotal * int(
                                                                    taxes) / 100
                                                                result_subt_total = order_line.price_subtotal + subtotal

                                                                for i in promotion_product.discount_specific_product_ids:
                                                                    disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                    if disc_product_id:
                                                                        if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                                if order_line.price_unit > promotion_product.discount_max_amount:

                                                                                    order_line.write({
                                                                                        'is_discount': True,
                                                                                        'discount_amount': promotion_product.discount_max_amount
                                                                                    })
                                                                                    # vals = {
                                                                                    #     'order_id': self.id,
                                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                    #     'price_unit': promotion_product.discount_max_amount,
                                                                                    #     'price_subtotal': result_subt_total,
                                                                                    # }
                                                                                    # if i.name not in self.order_line.mapped(
                                                                                    #         'description_product'):
                                                                                    #     po_line.create(vals)

                                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                    order_line.write({
                                                                                        'is_discount': True,
                                                                                        'discount': promotion_product.discount_percentage
                                                                                    })
                                                                                    # vals = {
                                                                                    #     'order_id': self.id,
                                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                    #     'price_unit': result_,
                                                                                    #     'price_subtotal': result_subt_total,
                                                                                    # }
                                                                                    # if i.name not in self.order_line.mapped(
                                                                                    #         'description_product'):
                                                                                    #     po_line.create(vals)
                                                                            elif int(
                                                                                    promotion_product.discount_max_amount) == 0:
                                                                                # print("max amount kosong")

                                                                                order_line.write({
                                                                                    'is_discount': True,
                                                                                    'discount': promotion_product.discount_percentage
                                                                                })
                                                                                # vals = {
                                                                                #     'order_id': self.id,
                                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                #     'price_unit': result_,
                                                                                #     'price_subtotal': result_subt_total,
                                                                                # }
                                                                                # if i.name not in self.order_line.mapped(
                                                                                #         'description_product'):
                                                                                #     po_line.create(vals)


                                                            elif promotion_product.discount_apply_on == 'cheapest_product':

                                                                product_list_update = self.env['sale.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])
                                                                # min_price = min(
                                                                #     self.order_line.mapped('price_unit'))
                                                                min_price = min(
                                                                    product_list_update.mapped('price_unit'))
                                                                po_line = self.env['sale.order.line'].sudo()
                                                                product_min_price = self.order_line.filtered(
                                                                    lambda r: r.price_unit == min_price)
                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                        # taxes = order_line.tax_id.name
                                                                        # if taxes:
                                                                        #     taxes = taxes.rstrip(taxes[-1])
                                                                        taxes = 0
                                                                        if order_line.tax_id:
                                                                            taxes = int(order_line.tax_id.amount)
                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit

                                                                        for i in product_min_price:
                                                                            i.write({
                                                                                'is_discount': True,
                                                                                'discount_amount': promotion_product.discount_max_amount
                                                                            })
                                                                        #     vals = {
                                                                        #         'order_id': self.id,
                                                                        #         'price_subtotal': resultsubtotal,
                                                                        #         'product_id': promotion_product.discount_line_product_id.id,
                                                                        #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                        #         'price_unit': promotion_product.discount_max_amount,
                                                                        #
                                                                        #     }
                                                                        #
                                                                        # if i.product_id.name not in self.order_line.mapped(
                                                                        #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                        #     'product_id').ids:
                                                                        #     po_line.create(vals)

                                                                    elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                        additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                        # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                        dis_res = order_line.harga_satuan_baru
                                                                        disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                        chepest_result = -diskon_percentage
                                                                        # taxes = order_line.tax_id.name
                                                                        # if taxes:
                                                                        #     taxes = taxes.rstrip(taxes[-1])
                                                                        taxes = 0
                                                                        if order_line.tax_id:
                                                                            taxes = int(order_line.tax_id.amount)
                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit

                                                                        for i in product_min_price:
                                                                            # i.write({'discount': promotion_product.discount_percentage})
                                                                            i.write({
                                                                                'is_discount': True,
                                                                                'discount_amount': disc_amount
                                                                            })
                                                                        #     vals = {
                                                                        #         'order_id': self.id,
                                                                        #         'price_subtotal': resultsubtotal,
                                                                        #         'product_id': promotion_product.discount_line_product_id.id,
                                                                        #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                        #         'price_unit': chepest_result,
                                                                        #
                                                                        #     }
                                                                        #
                                                                        # if i.product_id.name not in self.order_line.mapped(
                                                                        #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                        #     'product_id').ids:
                                                                        #     po_line.create(vals)

                                                                elif int(
                                                                        promotion_product.discount_max_amount) == 0:
                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    chepest_result = -diskon_percentage
                                                                    # taxes = order_line.tax_id.name
                                                                    # if taxes:
                                                                    #     taxes = taxes.rstrip(taxes[-1])
                                                                    taxes = 0
                                                                    if order_line.tax_id:
                                                                        taxes = int(order_line.tax_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({
                                                                            'is_discount': True,
                                                                            'discount_amount': disc_amount
                                                                        })
                                                                    #     vals = {
                                                                    #         'order_id': self.id,
                                                                    #         'price_subtotal': resultsubtotal,
                                                                    #         'product_id': promotion_product.discount_line_product_id.id,
                                                                    #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    #         'price_unit': chepest_result,
                                                                    #
                                                                    #     }
                                                                    #
                                                                    # if i.product_id.name not in self.order_line.mapped(
                                                                    #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    #     'product_id').ids:
                                                                    #     po_line.create(vals)

                                                            elif promotion_product.discount_apply_on == 'on_order':

                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if order_line.price_unit > promotion_product.discount_max_amount:
                                                                        po_line = self.env[
                                                                            'sale.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        on_order = -diskon_percentage
                                                                        # taxes = order_line.tax_id.name
                                                                        # if taxes:
                                                                        #     taxes = taxes.rstrip(taxes[-1])
                                                                        taxes = 0
                                                                        if order_line.tax_id:
                                                                            taxes = int(order_line.tax_id.amount)
                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            i.write({
                                                                                'is_discount': True,
                                                                                'discount_amount': promotion_product.discount_max_amount
                                                                            })
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'price_subtotal': resultsubtotal,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                            #     'price_unit': promotion_product.discount_max_amount,
                                                                            #
                                                                            # }
                                                                            #
                                                                            # po_line.create(vals)
                                                                    elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                        po_line = self.env[
                                                                            'sale.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                        # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                        dis_res = order_line.harga_satuan_baru
                                                                        disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                        on_order = -diskon_percentage
                                                                        # taxes = order_line.tax_id.name
                                                                        # if taxes:
                                                                        #     taxes = taxes.rstrip(taxes[-1])
                                                                        taxes = 0
                                                                        if order_line.tax_id:
                                                                            taxes = int(order_line.tax_id.amount)
                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            # i.write({'discount': promotion_product.discount_percentage})
                                                                            i.write({
                                                                                'is_discount': True,
                                                                                'discount_amount': disc_amount
                                                                            })
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'price_subtotal': resultsubtotal,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                            #     'price_unit': on_order,
                                                                            #
                                                                            # }
                                                                            #
                                                                            # po_line.create(vals)
                                                                elif int(
                                                                        promotion_product.discount_max_amount) == 0:
                                                                    po_line = self.env[
                                                                        'sale.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage
                                                                    # taxes = order_line.tax_id.name
                                                                    # if taxes:
                                                                    #     taxes = taxes.rstrip(taxes[-1])
                                                                    taxes = 0
                                                                    if order_line.tax_id:
                                                                        taxes = int(order_line.tax_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        i.write({
                                                                            'is_discount': True,
                                                                            'discount': promotion_product.discount_percentage
                                                                        })
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #     'price_subtotal': resultsubtotal,
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        #     'price_unit': on_order,
                                                                        #
                                                                        # }
                                                                        #
                                                                        # po_line.create(vals)

                                                        elif promotion_product.discount_type == 'fixed_amount':

                                                            po_line = self.env['sale.order.line'].sudo()
                                                            order_line.write({
                                                                'is_discount': True,
                                                                'discount_amount': promotion_product.discount_fixed_amount
                                                            })

                                                            # vals = {
                                                            #     'order_id': self.id,
                                                            #     'product_id': order_line.product_id.id,
                                                            #     'description_product': 'fixed amount'+ ' ' + ' on product :' + ' ' + promotion_product.name,
                                                            #     'price_unit': promotion_product.discount_fixed_amount,
                                                            #
                                                            # }
                                                            # if promotion_product.name not in self.order_line.mapped(
                                                            #         'description_product'):
                                                            #     po_line.create(vals)

                                                    else:
                                                        if promotion_product.discount_type == 'percentage':
                                                            if promotion_product.discount_apply_on == 'specific_products':
                                                                # taxes = order_line.tax_id.name
                                                                # if taxes:
                                                                #     taxes = taxes.rstrip(taxes[-1])
                                                                taxes = 0
                                                                if order_line.tax_id:
                                                                    taxes = int(order_line.tax_id.amount)
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                result_ = -diskon_percentage
                                                                po_line = self.env['sale.order.line'].sudo()
                                                                subtotal = order_line.price_subtotal * int(
                                                                    taxes) / 100
                                                                result_subt_total = order_line.price_subtotal + subtotal

                                                                for i in promotion_product.discount_specific_product_ids:
                                                                    disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                    if disc_product_id:
                                                                        if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                                if order_line.price_unit > promotion_product.discount_max_amount:

                                                                                    order_line.write({
                                                                                        'is_discount': True,
                                                                                        'discount_amount': promotion_product.discount_max_amount
                                                                                    })
                                                                                    # vals = {
                                                                                    #     'order_id': self.id,
                                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                    #     'price_unit': promotion_product.discount_max_amount,
                                                                                    #     'price_subtotal': result_subt_total,
                                                                                    # }
                                                                                    # if i.name not in self.order_line.mapped(
                                                                                    #         'description_product'):
                                                                                    #     po_line.create(vals)

                                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                    order_line.write({
                                                                                        'is_discount': True,
                                                                                        'discount': promotion_product.discount_percentage
                                                                                    })
                                                                                    # vals = {
                                                                                    #     'order_id': self.id,
                                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                    #     'price_unit': result_,
                                                                                    #     'price_subtotal': result_subt_total,
                                                                                    # }
                                                                                    # if i.name not in self.order_line.mapped(
                                                                                    #         'description_product'):
                                                                                    #     po_line.create(vals)
                                                                            elif int(
                                                                                    promotion_product.discount_max_amount) == 0:

                                                                                order_line.write({
                                                                                    'is_discount': True,
                                                                                    'discount': promotion_product.discount_percentage
                                                                                })
                                                                                # vals = {
                                                                                #     'order_id': self.id,
                                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                #     'price_unit': result_,
                                                                                #     'price_subtotal': result_subt_total,
                                                                                # }
                                                                                # if i.name not in self.order_line.mapped(
                                                                                #         'description_product'):
                                                                                #     po_line.create(vals)


                                                            elif promotion_product.discount_apply_on == 'cheapest_product':
                                                                product_list_update = self.env['sale.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])
                                                                # min_price = min(
                                                                #     self.order_line.mapped('price_unit'))
                                                                min_price = min(
                                                                    product_list_update.mapped('price_unit'))
                                                                po_line = self.env['sale.order.line'].sudo()
                                                                product_min_price = self.order_line.filtered(
                                                                    lambda r: r.price_unit == min_price)
                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if product_min_price.price_unit > promotion_product.discount_max_amount:
                                                                        # taxes = order_line.tax_id.name
                                                                        # if taxes:
                                                                        #     taxes = taxes.rstrip(taxes[-1])
                                                                        taxes = 0
                                                                        if order_line.tax_id:
                                                                            taxes = int(order_line.tax_id.amount)

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit

                                                                        for i in product_min_price:
                                                                            i.write({
                                                                                'is_discount': True,
                                                                                'discount_amount': promotion_product.discount_max_amount
                                                                            })
                                                                        #     vals = {
                                                                        #         'order_id': self.id,
                                                                        #         'price_subtotal': resultsubtotal,
                                                                        #         'product_id': promotion_product.discount_line_product_id.id,
                                                                        #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                        #         'price_unit': promotion_product.discount_max_amount,
                                                                        #
                                                                        #     }
                                                                        # if i.product_id.name not in self.order_line.mapped(
                                                                        #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                        #         'product_id').ids:
                                                                        #     po_line.create(vals)

                                                                    elif product_min_price.price_unit < promotion_product.discount_max_amount:
                                                                        # taxes = order_line.tax_id.name
                                                                        # if taxes:
                                                                        #     taxes = taxes.rstrip(taxes[-1])
                                                                        taxes = 0
                                                                        if order_line.tax_id:
                                                                            taxes = int(order_line.tax_id.amount)

                                                                        diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                        additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                        # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                        dis_res = order_line.harga_satuan_baru
                                                                        disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                        chepest_result = -diskon_percentage

                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + product_min_price.price_unit

                                                                        for i in product_min_price:
                                                                            # i.write({'discount': promotion_product.discount_percentage})
                                                                            i.write({
                                                                                'is_discount': True,
                                                                                'discount_amount': disc_amount
                                                                            })
                                                                        #     vals = {
                                                                        #         'order_id': self.id,
                                                                        #         'price_subtotal': resultsubtotal,
                                                                        #         'product_id': promotion_product.discount_line_product_id.id,
                                                                        #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                        #         'price_unit': chepest_result,
                                                                        #
                                                                        #     }
                                                                        #
                                                                        # if i.product_id.name not in self.order_line.mapped(
                                                                        #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                        #     'product_id').ids:
                                                                        #     po_line.create(vals)

                                                                elif int(
                                                                        promotion_product.discount_max_amount) == 0:
                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    chepest_result = -diskon_percentage
                                                                    # taxes = order_line.tax_id.name
                                                                    # if taxes:
                                                                    #     taxes = taxes.rstrip(taxes[-1])
                                                                    taxes = 0
                                                                    if order_line.tax_id:
                                                                        taxes = int(order_line.tax_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({
                                                                            'is_discount': True,
                                                                            'discount_amount': disc_amount
                                                                        })
                                                                    #     vals = {
                                                                    #         'order_id': self.id,
                                                                    #         'price_subtotal': resultsubtotal,
                                                                    #         'product_id': promotion_product.discount_line_product_id.id,
                                                                    #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    #         'price_unit': chepest_result,
                                                                    #
                                                                    #     }
                                                                    #
                                                                    # if i.product_id.name not in self.order_line.mapped(
                                                                    #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    #     'product_id').ids:
                                                                    #     po_line.create(vals)

                                                            elif promotion_product.discount_apply_on == 'on_order':

                                                                if int(promotion_product.discount_max_amount) > 0:
                                                                    calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    if order_line.price_unit > promotion_product.discount_max_amount:
                                                                        po_line = self.env[
                                                                            'sale.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        on_order = -diskon_percentage
                                                                        # taxes = order_line.tax_id.name
                                                                        # if taxes:
                                                                        #     taxes = taxes.rstrip(taxes[-1])
                                                                        taxes = 0
                                                                        if order_line.tax_id:
                                                                            taxes = int(order_line.tax_id.amount)
                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            i.write({
                                                                                'is_discount': True,
                                                                                'discount_amount': promotion_product.discount_max_amount
                                                                            })
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'price_subtotal': resultsubtotal,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                            #     'price_unit': promotion_product.discount_max_amount,
                                                                            #
                                                                            # }
                                                                            #
                                                                            # po_line.create(vals)
                                                                    elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                        po_line = self.env[
                                                                            'sale.order.line'].sudo()
                                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                        # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                        dis_res = order_line.harga_satuan_baru
                                                                        disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                        on_order = -diskon_percentage
                                                                        # taxes = order_line.tax_id.name
                                                                        # if taxes:
                                                                        #     taxes = taxes.rstrip(taxes[-1])
                                                                        taxes = 0
                                                                        if order_line.tax_id:
                                                                            taxes = int(order_line.tax_id.amount)
                                                                        subtotal = diskon_percentage * int(
                                                                            taxes) / 100
                                                                        resultsubtotal = subtotal + order_line.price_unit

                                                                        for i in order_line:
                                                                            # i.write({'discount': promotion_product.discount_percentage})
                                                                            i.write({
                                                                                'is_discount': True,
                                                                                'discount_amount': disc_amount
                                                                            })
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'price_subtotal': resultsubtotal,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                            #     'price_unit': on_order,
                                                                            #
                                                                            # }
                                                                            #
                                                                            # po_line.create(vals)
                                                                elif int(
                                                                        promotion_product.discount_max_amount) == 0:
                                                                    po_line = self.env[
                                                                        'sale.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    on_order = -diskon_percentage
                                                                    # taxes = order_line.tax_id.name
                                                                    # if taxes:
                                                                    #     taxes = taxes.rstrip(taxes[-1])
                                                                    taxes = 0
                                                                    if order_line.tax_id:
                                                                        taxes = int(order_line.tax_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({
                                                                            'is_discount': True,
                                                                            'discount_amount': disc_amount
                                                                        })
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #     'price_subtotal': resultsubtotal,
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        #     'price_unit': on_order,
                                                                        #
                                                                        # }
                                                                        #
                                                                        # po_line.create(vals)

                                                        elif promotion_product.discount_type == 'fixed_amount':

                                                            po_line = self.env['sale.order.line'].sudo()
                                                            order_line.write({
                                                                'is_discount': True,
                                                                'discount_amount': promotion_product.discount_fixed_amount
                                                            })
                    else:
                        for product_ids_list in promotion_product.product_ids:

                            # filter = promotion_product.filtered(lambda r: product_ids_list.id == rec.product_id.id)


                            for customer_id in promotion_product.rule_partners_domain:

                                for order_line in self.order_line:
                                    if order_line.product_id.id == product_ids_list.id and customer_id.id == self.partner_id.id and ((promotion_product.rule_min_quantity > 0 and int(order_line.product_uom_qty) >= promotion_product.rule_min_quantity) or (promotion_product.rule_minimum_amount > 0 and order_line.price_subtotal  >= promotion_product.rule_minimum_amount )):

                                        if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':
                                            # taxes = order_line.tax_id.name
                                            # if taxes:
                                            #     taxes = taxes.rstrip(taxes[-1])
                                            taxes = 0
                                            if order_line.tax_id:
                                                taxes = int(order_line.tax_id.amount)
                                            result = order_line.price_subtotal * int(taxes) / 100
                                            total = result + order_line.price_subtotal
                                            if total >= promotion_product.rule_minimum_amount:
                                                if promotion_product.remaining_use_promotion > 0 and promotion_product.remaining_use_promotion > 0:
                                                    promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1

                                                    if promotion_product.discount_type == 'percentage':
                                                        if promotion_product.discount_apply_on == 'specific_products':
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            result_ = -diskon_percentage
                                                            po_line = self.env['sale.order.line'].sudo()
                                                            # taxes = order_line.tax_id.name
                                                            # if taxes:
                                                            #     taxes = taxes.rstrip(taxes[-1])
                                                            taxes = 0
                                                            if order_line.tax_id:
                                                                taxes = int(order_line.tax_id.amount)
                                                            subtotal = order_line.price_subtotal * int(
                                                                taxes) / 100
                                                            result_subt_total = order_line.price_subtotal + subtotal

                                                            for i in promotion_product.discount_specific_product_ids:
                                                                disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                if disc_product_id:
                                                                    if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                        if int(promotion_product.discount_max_amount) > 0:
                                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                            if order_line.price_unit > promotion_product.discount_max_amount:

                                                                                order_line.write({'is_discount': True,'discount_amount': promotion_product.discount_max_amount})
                                                                                # vals = {
                                                                                #     'order_id': self.id,
                                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                #     'price_unit': promotion_product.discount_max_amount,
                                                                                #     'price_subtotal': result_subt_total,
                                                                                # }
                                                                                # if i.name not in self.order_line.mapped(
                                                                                #         'description_product'):
                                                                                #     po_line.create(vals)

                                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                order_line.write({'discount': promotion_product.discount_percentage})
                                                                                # vals = {
                                                                                #     'order_id': self.id,
                                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                #     'price_unit': result_,
                                                                                #     'price_subtotal': result_subt_total,
                                                                                # }
                                                                                # if i.name not in self.order_line.mapped(
                                                                                #         'description_product'):
                                                                                #     po_line.create(vals)
                                                                        elif int(
                                                                                promotion_product.discount_max_amount) == 0:

                                                                            order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            #     'price_unit': result_,
                                                                            #     'price_subtotal': result_subt_total,
                                                                            # }
                                                                            # if i.name not in self.order_line.mapped(
                                                                            #         'description_product'):
                                                                            #     po_line.create(vals)


                                                        elif promotion_product.discount_apply_on == 'cheapest_product':
                                                            product_list_update = self.env['sale.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])
                                                            # min_price = min(
                                                            #     self.order_line.mapped('price_unit'))
                                                            min_price = min(
                                                                product_list_update.mapped('price_unit'))
                                                            po_line = self.env['sale.order.line'].sudo()
                                                            product_min_price = self.order_line.filtered(
                                                                lambda r: r.price_unit == min_price)
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    # taxes = order_line.tax_id.name
                                                                    # if taxes:
                                                                    #     taxes = taxes.rstrip(taxes[-1])
                                                                    taxes = 0
                                                                    if order_line.tax_id:
                                                                        taxes = int(order_line.tax_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                    #     vals = {
                                                                    #         'order_id': self.id,
                                                                    #         'price_subtotal': resultsubtotal,
                                                                    #         'product_id': promotion_product.discount_line_product_id.id,
                                                                    #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    #         'price_unit': promotion_product.discount_max_amount,
                                                                    #
                                                                    #     }
                                                                    #
                                                                    # if i.product_id.name not in self.order_line.mapped(
                                                                    #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    #     'product_id').ids:
                                                                    #     po_line.create(vals)

                                                                elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    chepest_result = -diskon_percentage
                                                                    # taxes = order_line.tax_id.name
                                                                    # if taxes:
                                                                    #     taxes = taxes.rstrip(taxes[-1])
                                                                    taxes = 0
                                                                    if order_line.tax_id:
                                                                        taxes = int(order_line.tax_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    #     vals = {
                                                                    #         'order_id': self.id,
                                                                    #         'price_subtotal': resultsubtotal,
                                                                    #         'product_id': promotion_product.discount_line_product_id.id,
                                                                    #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    #         'price_unit': chepest_result,
                                                                    #
                                                                    #     }
                                                                    #
                                                                    # if i.product_id.name not in self.order_line.mapped(
                                                                    #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    #     'product_id').ids:
                                                                    #     po_line.create(vals)

                                                            elif int(
                                                                    promotion_product.discount_max_amount) == 0:
                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                chepest_result = -diskon_percentage
                                                                # taxes = order_line.tax_id.name
                                                                # if taxes:
                                                                #     taxes = taxes.rstrip(taxes[-1])
                                                                taxes = 0
                                                                if order_line.tax_id:
                                                                    taxes = int(order_line.tax_id.amount)
                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                #     vals = {
                                                                #         'order_id': self.id,
                                                                #         'price_subtotal': resultsubtotal,
                                                                #         'product_id': promotion_product.discount_line_product_id.id,
                                                                #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                #         'price_unit': chepest_result,
                                                                #
                                                                #     }
                                                                #
                                                                # if i.product_id.name not in self.order_line.mapped(
                                                                #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                #     'product_id').ids:
                                                                #     po_line.create(vals)

                                                        elif promotion_product.discount_apply_on == 'on_order':

                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if order_line.price_unit > promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'sale.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage
                                                                    # taxes = order_line.tax_id.name
                                                                    # if taxes:
                                                                    #     taxes = taxes.rstrip(taxes[-1])

                                                                    taxes = 0
                                                                    if order_line.tax_id:
                                                                        taxes = int(order_line.tax_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #     'price_subtotal': resultsubtotal,
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        #     'price_unit': promotion_product.discount_max_amount,
                                                                        #
                                                                        # }
                                                                        #
                                                                        # po_line.create(vals)
                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'sale.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    on_order = -diskon_percentage
                                                                    # taxes = order_line.tax_id.name
                                                                    # if taxes:
                                                                    #     taxes = taxes.rstrip(taxes[-1])

                                                                    taxes = 0
                                                                    if order_line.tax_id:
                                                                        taxes = int(order_line.tax_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #     'price_subtotal': resultsubtotal,
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        #     'price_unit': on_order,
                                                                        #
                                                                        # }
                                                                        #
                                                                        # po_line.create(vals)
                                                            elif int(
                                                                    promotion_product.discount_max_amount) == 0:
                                                                po_line = self.env[
                                                                    'sale.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                on_order = -diskon_percentage
                                                                # taxes = order_line.tax_id.name
                                                                # if taxes:
                                                                #     taxes = taxes.rstrip(taxes[-1])
                                                                taxes = 0
                                                                if order_line.tax_id:
                                                                    taxes = int(order_line.tax_id.amount)
                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    # vals = {
                                                                    #     'order_id': self.id,
                                                                    #     'price_subtotal': resultsubtotal,
                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    #     'price_unit': on_order,
                                                                    #
                                                                    # }
                                                                    #
                                                                    # po_line.create(vals)

                                                    elif promotion_product.discount_type == 'fixed_amount':

                                                        po_line = self.env['sale.order.line'].sudo()
                                                        order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_fixed_amount})

                                                        # vals = {
                                                        #     'order_id': self.id,
                                                        #      'product_id': order_line.product_id.id,
                                                        #      'description_product': 'fixed amount'+ ' ' + ' on product :' + ' ' + promotion_product.name,
                                                        #     'price_unit': promotion_product.discount_fixed_amount,
                                                        #
                                                        # }
                                                        # if promotion_product.name not in self.order_line.mapped(
                                                        #         'description_product'):
                                                        #     po_line.create(vals)
                                                else:
                                                    if promotion_product.discount_type == 'percentage':
                                                        if promotion_product.discount_apply_on == 'specific_products':
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            result_ = -diskon_percentage
                                                            po_line = self.env['sale.order.line'].sudo()
                                                            # taxes = order_line.tax_id.name
                                                            # if taxes:
                                                            #     taxes = taxes.rstrip(taxes[-1])

                                                            taxes = 0
                                                            if order_line.tax_id:
                                                                taxes = int(order_line.tax_id.amount)
                                                            subtotal = order_line.price_subtotal * int(
                                                                taxes) / 100
                                                            result_subt_total = order_line.price_subtotal + subtotal

                                                            for i in promotion_product.discount_specific_product_ids:
                                                                disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                if disc_product_id:
                                                                    if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                        if int(promotion_product.discount_max_amount) > 0:
                                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                            if order_line.price_unit > promotion_product.discount_max_amount:

                                                                                order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                                # vals = {
                                                                                #     'order_id': self.id,
                                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                #     'price_unit': promotion_product.discount_max_amount,
                                                                                #     'price_subtotal': result_subt_total,
                                                                                # }
                                                                                # if i.name not in self.order_line.mapped(
                                                                                #         'description_product'):
                                                                                #     po_line.create(vals)

                                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                                # vals = {
                                                                                #     'order_id': self.id,
                                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                #     'price_unit': result_,
                                                                                #     'price_subtotal': result_subt_total,
                                                                                # }
                                                                                # if i.name not in self.order_line.mapped(
                                                                                #         'description_product'):
                                                                                #     po_line.create(vals)
                                                                        elif int(
                                                                                promotion_product.discount_max_amount) == 0:

                                                                            order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            #     'price_unit': result_,
                                                                            #     'price_subtotal': result_subt_total,
                                                                            # }
                                                                            # if i.name not in self.order_line.mapped(
                                                                            #         'description_product'):
                                                                            #     po_line.create(vals)


                                                        elif promotion_product.discount_apply_on == 'cheapest_product':
                                                            product_list_update = self.env['sale.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])
                                                            # min_price = min(
                                                            #     self.order_line.mapped('price_unit'))
                                                            min_price = min(
                                                                product_list_update.mapped('price_unit'))
                                                            po_line = self.env['sale.order.line'].sudo()
                                                            product_min_price = self.order_line.filtered(
                                                                lambda r: r.price_unit == min_price)
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    # taxes = order_line.tax_id.name
                                                                    # if taxes:
                                                                    #     taxes = taxes.rstrip(taxes[-1])

                                                                    taxes = 0
                                                                    if order_line.tax_id:
                                                                        taxes = int(order_line.tax_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                    #     vals = {
                                                                    #         'order_id': self.id,
                                                                    #         'price_subtotal': resultsubtotal,
                                                                    #         'product_id': promotion_product.discount_line_product_id.id,
                                                                    #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    #         'price_unit': promotion_product.discount_max_amount,
                                                                    #
                                                                    #     }
                                                                    #
                                                                    # if i.product_id.name not in self.order_line.mapped(
                                                                    #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    #     'product_id').ids:
                                                                    #     po_line.create(vals)

                                                                elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    chepest_result = -diskon_percentage
                                                                    # taxes = order_line.tax_id.name
                                                                    # if taxes:
                                                                    #     taxes = taxes.rstrip(taxes[-1])

                                                                    taxes = 0
                                                                    if order_line.tax_id:
                                                                        taxes = int(order_line.tax_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    #     vals = {
                                                                    #         'order_id': self.id,
                                                                    #         'price_subtotal': resultsubtotal,
                                                                    #         'product_id': promotion_product.discount_line_product_id.id,
                                                                    #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    #         'price_unit': chepest_result,
                                                                    #
                                                                    #     }
                                                                    #
                                                                    # if i.product_id.name not in self.order_line.mapped(
                                                                    #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    #     'product_id').ids:
                                                                    #     po_line.create(vals)

                                                            elif int(
                                                                    promotion_product.discount_max_amount) == 0:
                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                chepest_result = -diskon_percentage
                                                                # taxes = order_line.tax_id.name
                                                                # if taxes:
                                                                #     taxes = taxes.rstrip(taxes[-1])

                                                                taxes = 0
                                                                if order_line.tax_id:
                                                                    taxes = int(order_line.tax_id.amount)
                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    i.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                #     vals = {
                                                                #         'order_id': self.id,
                                                                #         'price_subtotal': resultsubtotal,
                                                                #         'product_id': promotion_product.discount_line_product_id.id,
                                                                #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                #         'price_unit': chepest_result,
                                                                #
                                                                #     }
                                                                #
                                                                # if i.product_id.name not in self.order_line.mapped(
                                                                #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                #     'product_id').ids:
                                                                #     po_line.create(vals)

                                                        elif promotion_product.discount_apply_on == 'on_order':

                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if order_line.price_unit > promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'sale.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage
                                                                    # taxes = order_line.tax_id.name
                                                                    # if taxes:
                                                                    #     taxes = taxes.rstrip(taxes[-1])

                                                                    taxes = 0
                                                                    if order_line.tax_id:
                                                                        taxes = int(order_line.tax_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #     'price_subtotal': resultsubtotal,
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        #     'price_unit': promotion_product.discount_max_amount,
                                                                        #
                                                                        # }
                                                                        #
                                                                        # po_line.create(vals)
                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'sale.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    on_order = -diskon_percentage
                                                                    # taxes = order_line.tax_id.name
                                                                    # if taxes:
                                                                    #     taxes = taxes.rstrip(taxes[-1])

                                                                    taxes = 0
                                                                    if order_line.tax_id:
                                                                        taxes = int(order_line.tax_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #     'price_subtotal': resultsubtotal,
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        #     'price_unit': on_order,
                                                                        #
                                                                        # }
                                                                        #
                                                                        # po_line.create(vals)
                                                            elif int(
                                                                    promotion_product.discount_max_amount) == 0:
                                                                po_line = self.env[
                                                                    'sale.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                on_order = -diskon_percentage
                                                                # taxes = order_line.tax_id.name
                                                                # if taxes:
                                                                #     taxes = taxes.rstrip(taxes[-1])

                                                                taxes = 0
                                                                if order_line.tax_id:
                                                                    taxes = int(order_line.tax_id.amount)
                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    # vals = {
                                                                    #     'order_id': self.id,
                                                                    #     'price_subtotal': resultsubtotal,
                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    #     'price_unit': on_order,
                                                                    #
                                                                    # }
                                                                    #
                                                                    # po_line.create(vals)

                                                    elif promotion_product.discount_type == 'fixed_amount':

                                                        po_line = self.env['sale.order.line'].sudo()
                                                        order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_fixed_amount})

                                                        # vals = {
                                                        #     'order_id': self.id,
                                                        #     'product_id': order_line.product_id.id,
                                                        #     'description_product': 'fixed amount' + ' ' + ' on product :' + ' ' + promotion_product.name,
                                                        #     'price_unit': promotion_product.discount_fixed_amount,
                                                        #
                                                        # }
                                                        # if promotion_product.name not in self.order_line.mapped(
                                                        #         'description_product'):
                                                        #     po_line.create(vals)

                                        elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':
                                            total = order_line.price_subtotal
                                            if total >= promotion_product.rule_minimum_amount:
                                                if promotion_product.remaining_use_promotion > 0:
                                                    promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1

                                                    if promotion_product.discount_type == 'percentage':
                                                        if promotion_product.discount_apply_on == 'specific_products':
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            result_ = -diskon_percentage
                                                            po_line = self.env['sale.order.line'].sudo()
                                                            # taxes = order_line.tax_id.name
                                                            # if taxes:
                                                            #     taxes = taxes.rstrip(taxes[-1])

                                                            taxes = 0
                                                            if order_line.tax_id:
                                                                taxes = int(order_line.tax_id.amount)
                                                            subtotal = order_line.price_subtotal * int(
                                                                taxes) / 100
                                                            result_subt_total = order_line.price_subtotal + subtotal

                                                            for i in promotion_product.discount_specific_product_ids:
                                                                disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                if disc_product_id:
                                                                    if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                        if int(promotion_product.discount_max_amount) > 0:
                                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                            if order_line.price_unit > promotion_product.discount_max_amount:

                                                                                order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                                # vals = {
                                                                                #     'order_id': self.id,
                                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                #     'price_unit': promotion_product.discount_max_amount,
                                                                                #     'price_subtotal': result_subt_total,
                                                                                # }
                                                                                # if i.name not in self.order_line.mapped(
                                                                                #         'description_product'):
                                                                                #     po_line.create(vals)

                                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                                # vals = {
                                                                                #     'order_id': self.id,
                                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                #     'price_unit': result_,
                                                                                #     'price_subtotal': result_subt_total,
                                                                                # }
                                                                                # if i.name not in self.order_line.mapped(
                                                                                #         'description_product'):
                                                                                #     po_line.create(vals)
                                                                        elif int(
                                                                                promotion_product.discount_max_amount) == 0:

                                                                            order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            #     'price_unit': result_,
                                                                            #     'price_subtotal': result_subt_total,
                                                                            # }
                                                                            # if i.name not in self.order_line.mapped(
                                                                            #         'description_product'):
                                                                            #     po_line.create(vals)


                                                        elif promotion_product.discount_apply_on == 'cheapest_product':
                                                            product_list_update = self.env['sale.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])
                                                            # min_price = min(
                                                            #     self.order_line.mapped('price_unit'))
                                                            min_price = min(
                                                                product_list_update.mapped('price_unit'))
                                                            po_line = self.env['sale.order.line'].sudo()
                                                            product_min_price = self.order_line.filtered(
                                                                lambda r: r.price_unit == min_price)
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    # taxes = order_line.tax_id.name
                                                                    # if taxes:
                                                                    #     taxes = taxes.rstrip(taxes[-1])

                                                                    taxes = 0
                                                                    if order_line.tax_id:
                                                                        taxes = int(order_line.tax_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                    #     vals = {
                                                                    #         'order_id': self.id,
                                                                    #         'price_subtotal': resultsubtotal,
                                                                    #         'product_id': promotion_product.discount_line_product_id.id,
                                                                    #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    #         'price_unit': promotion_product.discount_max_amount,
                                                                    #
                                                                    #     }
                                                                    #
                                                                    # if i.product_id.name not in self.order_line.mapped(
                                                                    #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    #     'product_id').ids:
                                                                    #     po_line.create(vals)

                                                                elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    chepest_result = -diskon_percentage
                                                                    # taxes = order_line.tax_id.name
                                                                    # if taxes:
                                                                    #     taxes = taxes.rstrip(taxes[-1])

                                                                    taxes = 0
                                                                    if order_line.tax_id:
                                                                        taxes = int(order_line.tax_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    #     vals = {
                                                                    #         'order_id': self.id,
                                                                    #         'price_subtotal': resultsubtotal,
                                                                    #         'product_id': promotion_product.discount_line_product_id.id,
                                                                    #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    #         'price_unit': chepest_result,
                                                                    #
                                                                    #     }
                                                                    #
                                                                    # if i.product_id.name not in self.order_line.mapped(
                                                                    #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    #     'product_id').ids:
                                                                    #     po_line.create(vals)

                                                            elif int(
                                                                    promotion_product.discount_max_amount) == 0:
                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                chepest_result = -diskon_percentage
                                                                # taxes = order_line.tax_id.name
                                                                # if taxes:
                                                                #     taxes = taxes.rstrip(taxes[-1])

                                                                taxes = 0
                                                                if order_line.tax_id:
                                                                    taxes = int(order_line.tax_id.amount)
                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                #     vals = {
                                                                #         'order_id': self.id,
                                                                #         'price_subtotal': resultsubtotal,
                                                                #         'product_id': promotion_product.discount_line_product_id.id,
                                                                #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                #         'price_unit': chepest_result,
                                                                #
                                                                #     }
                                                                #
                                                                # if i.product_id.name not in self.order_line.mapped(
                                                                #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                #     'product_id').ids:
                                                                #     po_line.create(vals)

                                                        elif promotion_product.discount_apply_on == 'on_order':

                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if order_line.price_unit > promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'sale.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage
                                                                    # taxes = order_line.tax_id.name
                                                                    # if taxes:
                                                                    #     taxes = taxes.rstrip(taxes[-1])

                                                                    taxes = 0
                                                                    if order_line.tax_id:
                                                                        taxes = int(order_line.tax_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #     'price_subtotal': resultsubtotal,
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        #     'price_unit': promotion_product.discount_max_amount,
                                                                        #
                                                                        # }
                                                                        #
                                                                        # po_line.create(vals)
                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'sale.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    on_order = -diskon_percentage
                                                                    # taxes = order_line.tax_id.name
                                                                    # if taxes:
                                                                    #     taxes = taxes.rstrip(taxes[-1])

                                                                    taxes = 0
                                                                    if order_line.tax_id:
                                                                        taxes = int(order_line.tax_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #     'price_subtotal': resultsubtotal,
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        #     'price_unit': on_order,
                                                                        #
                                                                        # }
                                                                        #
                                                                        # po_line.create(vals)
                                                            elif int(
                                                                    promotion_product.discount_max_amount) == 0:
                                                                po_line = self.env[
                                                                    'sale.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                on_order = -diskon_percentage
                                                                # taxes = order_line.tax_id.name
                                                                # if taxes:
                                                                #     taxes = taxes.rstrip(taxes[-1])

                                                                taxes = 0
                                                                if order_line.tax_id:
                                                                    taxes = int(order_line.tax_id.amount)
                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    # vals = {
                                                                    #     'order_id': self.id,
                                                                    #     'price_subtotal': resultsubtotal,
                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    #     'price_unit': on_order,
                                                                    #
                                                                    # }
                                                                    #
                                                                    # po_line.create(vals)

                                                    elif promotion_product.discount_type == 'fixed_amount':

                                                        po_line = self.env['sale.order.line'].sudo()
                                                        order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_fixed_amount})

                                                        # vals = {
                                                        #     'order_id': self.id,
                                                        #     'product_id': order_line.product_id.id,
                                                        #     'description_product': 'fixed amount' + ' ' + ' on product :' + ' ' + promotion_product.name,
                                                        #     'price_unit': promotion_product.discount_fixed_amount,
                                                        #
                                                        # }
                                                        # if promotion_product.name not in self.order_line.mapped(
                                                        #         'description_product'):
                                                        #     po_line.create(vals)
                                                else:
                                                    if promotion_product.discount_type == 'percentage':
                                                        if promotion_product.discount_apply_on == 'specific_products':
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            result_ = -diskon_percentage
                                                            po_line = self.env['sale.order.line'].sudo()
                                                            # taxes = order_line.tax_id.name
                                                            # if taxes:
                                                            #     taxes = taxes.rstrip(taxes[-1])

                                                            taxes = 0
                                                            if order_line.tax_id:
                                                                taxes = int(order_line.tax_id.amount)
                                                            subtotal = order_line.price_subtotal * int(
                                                                taxes) / 100
                                                            result_subt_total = order_line.price_subtotal + subtotal

                                                            for i in promotion_product.discount_specific_product_ids:
                                                                disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                if disc_product_id:
                                                                    if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                        if int(promotion_product.discount_max_amount) > 0:
                                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                            if order_line.price_unit > promotion_product.discount_max_amount:

                                                                                order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})

                                                                                # vals = {
                                                                                #     'order_id': self.id,
                                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                #     'price_unit': promotion_product.discount_max_amount,
                                                                                #     'price_subtotal': result_subt_total,
                                                                                # }
                                                                                # if i.name not in self.order_line.mapped(
                                                                                #         'description_product'):
                                                                                #     po_line.create(vals)

                                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                                # vals = {
                                                                                #     'order_id': self.id,
                                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                #     'price_unit': result_,
                                                                                #     'price_subtotal': result_subt_total,
                                                                                # }
                                                                                # if i.name not in self.order_line.mapped(
                                                                                #         'description_product'):
                                                                                #     po_line.create(vals)
                                                                        elif int(
                                                                                promotion_product.discount_max_amount) == 0:

                                                                            order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            #     'price_unit': result_,
                                                                            #     'price_subtotal': result_subt_total,
                                                                            # }
                                                                            # if i.name not in self.order_line.mapped(
                                                                            #         'description_product'):
                                                                            #     po_line.create(vals)


                                                        elif promotion_product.discount_apply_on == 'cheapest_product':
                                                            product_list_update = self.env['sale.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])
                                                            # min_price = min(
                                                            #     self.order_line.mapped('price_unit'))
                                                            min_price = min(
                                                                product_list_update.mapped('price_unit'))
                                                            po_line = self.env['sale.order.line'].sudo()
                                                            product_min_price = self.order_line.filtered(
                                                                lambda r: r.price_unit == min_price)
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    # taxes = order_line.tax_id.name
                                                                    # if taxes:
                                                                    #     taxes = taxes.rstrip(taxes[-1])

                                                                    taxes = 0
                                                                    if order_line.tax_id:
                                                                        taxes = int(order_line.tax_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                    #     vals = {
                                                                    #         'order_id': self.id,
                                                                    #         'price_subtotal': resultsubtotal,
                                                                    #         'product_id': promotion_product.discount_line_product_id.id,
                                                                    #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    #         'price_unit': promotion_product.discount_max_amount,
                                                                    #
                                                                    #     }
                                                                    #
                                                                    # if i.product_id.name not in self.order_line.mapped(
                                                                    #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    #     'product_id').ids:
                                                                    #     po_line.create(vals)

                                                                elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    chepest_result = -diskon_percentage
                                                                    # taxes = order_line.tax_id.name
                                                                    # if taxes:
                                                                    #     taxes = taxes.rstrip(taxes[-1])

                                                                    taxes = 0
                                                                    if order_line.tax_id:
                                                                        taxes = int(order_line.tax_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    #     vals = {
                                                                    #         'order_id': self.id,
                                                                    #         'price_subtotal': resultsubtotal,
                                                                    #         'product_id': promotion_product.discount_line_product_id.id,
                                                                    #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    #         'price_unit': chepest_result,
                                                                    #
                                                                    #     }
                                                                    #
                                                                    # if i.product_id.name not in self.order_line.mapped(
                                                                    #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    #     'product_id').ids:
                                                                    #     po_line.create(vals)

                                                            elif int(
                                                                    promotion_product.discount_max_amount) == 0:
                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                chepest_result = -diskon_percentage
                                                                # taxes = order_line.tax_id.name
                                                                # if taxes:
                                                                #     taxes = taxes.rstrip(taxes[-1])

                                                                taxes = 0
                                                                if order_line.tax_id:
                                                                    taxes = int(order_line.tax_id.amount)
                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                #     vals = {
                                                                #         'order_id': self.id,
                                                                #         'price_subtotal': resultsubtotal,
                                                                #         'product_id': promotion_product.discount_line_product_id.id,
                                                                #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                #         'price_unit': chepest_result,
                                                                #
                                                                #     }
                                                                #
                                                                # if i.product_id.name not in self.order_line.mapped(
                                                                #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                #     'product_id').ids:
                                                                #     po_line.create(vals)

                                                        elif promotion_product.discount_apply_on == 'on_order':

                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if order_line.price_unit > promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'sale.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage
                                                                    # taxes = order_line.tax_id.name
                                                                    # if taxes:
                                                                    #     taxes = taxes.rstrip(taxes[-1])

                                                                    taxes = 0
                                                                    if order_line.tax_id:
                                                                        taxes = int(order_line.tax_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #     'price_subtotal': resultsubtotal,
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        #     'price_unit': promotion_product.discount_max_amount,
                                                                        #
                                                                        # }
                                                                        #
                                                                        # po_line.create(vals)
                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'sale.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    on_order = -diskon_percentage
                                                                    # taxes = order_line.tax_id.name
                                                                    # if taxes:
                                                                    #     taxes = taxes.rstrip(taxes[-1])

                                                                    taxes = 0
                                                                    if order_line.tax_id:
                                                                        taxes = int(order_line.tax_id.amount)
                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #     'price_subtotal': resultsubtotal,
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        #     'price_unit': on_order,
                                                                        #
                                                                        # }
                                                                        #
                                                                        # po_line.create(vals)
                                                            elif int(
                                                                    promotion_product.discount_max_amount) == 0:
                                                                po_line = self.env[
                                                                    'sale.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                on_order = -diskon_percentage
                                                                # taxes = order_line.tax_id.name
                                                                # if taxes:
                                                                #     taxes = taxes.rstrip(taxes[-1])

                                                                taxes = 0
                                                                if order_line.tax_id:
                                                                    taxes = int(order_line.tax_id.amount)
                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    # vals = {
                                                                    #     'order_id': self.id,
                                                                    #     'price_subtotal': resultsubtotal,
                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    #     'price_unit': on_order,
                                                                    #
                                                                    # }
                                                                    #
                                                                    # po_line.create(vals)

                                                    elif promotion_product.discount_type == 'fixed_amount':

                                                        po_line = self.env['sale.order.line'].sudo()
                                                        order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_fixed_amount})
                elif promotion_product.rule_partners_domain:
                    if promotion_product.rule_date_from and promotion_product.rule_date_to:
                        for customer_id in promotion_product.rule_partners_domain:
                            for order_line in self.order_line:
                                if customer_id.id == self.partner_id.id and ((promotion_product.rule_min_quantity > 0 and int(order_line.product_uom_qty) >= promotion_product.rule_min_quantity) or (promotion_product.rule_minimum_amount > 0 and order_line.price_subtotal  >= promotion_product.rule_minimum_amount )):

                                    date_order = datetime.strptime(str(self.date_order),
                                                                   "%Y-%m-%d %H:%M:%S")
                                    start_date = datetime.strptime(str(promotion_product.rule_date_from),
                                                                   "%Y-%m-%d %H:%M:%S")
                                    end_date = datetime.strptime(str(promotion_product.rule_date_to),
                                                                 "%Y-%m-%d %H:%M:%S")
                                    if date_order <= end_date and date_order >= start_date:
                                        if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':
                                            # print("TAX INCLUDED")
                                            # taxes = order_line.tax_id.name
                                            # if taxes:
                                            #     taxes = taxes.rstrip(taxes[-1])

                                            taxes = 0
                                            if order_line.tax_id:
                                                taxes = int(order_line.tax_id.amount)
                                            result = order_line.price_subtotal * int(taxes) / 100
                                            total = result + order_line.price_subtotal
                                            if total >= promotion_product.rule_minimum_amount:
                                                if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                    promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1
                                                    if promotion_product.discount_type == 'percentage':
                                                        if promotion_product.discount_apply_on == 'specific_products':

                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            result_ = -diskon_percentage
                                                            po_line = self.env['sale.order.line'].sudo()
                                                            # subtotal = order_line.price_subtotal * int(
                                                            #     taxes) / 100
                                                            # result_subt_total = order_line.price_subtotal + subtotal

                                                            for i in promotion_product.discount_specific_product_ids:
                                                                disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                if disc_product_id:
                                                                    if disc_product_id.id == order_line.product_id.id:
                                                                        if int(promotion_product.discount_max_amount) > 0:
                                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                            if order_line.price_unit > promotion_product.discount_max_amount:

                                                                                order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                                # vals = {
                                                                                #     'order_id': self.id,
                                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                #     'price_unit': promotion_product.discount_max_amount,
                                                                                #     # 'price_subtotal': result_subt_total,
                                                                                # }
                                                                                # if i.name not in self.order_line.mapped(
                                                                                #         'description_product'):
                                                                                #     po_line.create(vals)

                                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                                # vals = {
                                                                                #     'order_id': self.id,
                                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                #     'price_unit': result_,
                                                                                #     'price_subtotal': result_subt_total,
                                                                                # }
                                                                                # if i.name not in self.order_line.mapped(
                                                                                #         'description_product'):
                                                                                #     po_line.create(vals)
                                                                        elif int(
                                                                                promotion_product.discount_max_amount) == 0:


                                                                            order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            #     'price_unit': result_,
                                                                            #     # 'price_subtotal': result_subt_total,
                                                                            # }
                                                                            # if i.name not in self.order_line.mapped(
                                                                            #         'description_product'):
                                                                            #     po_line.create(vals)


                                                        elif promotion_product.discount_apply_on == 'cheapest_product':
                                                            min_price = min(self.order_line.mapped('price_unit'))
                                                            po_line = self.env['sale.order.line'].sudo()
                                                            product_min_price = self.order_line.filtered(
                                                                lambda r: r.price_unit == min_price)
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                    # subtotal = diskon_percentage * int(taxes) / 100
                                                                    # resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                    #     vals = {
                                                                    #         'order_id': self.id,
                                                                    #         # 'price_subtotal': resultsubtotal,
                                                                    #         'product_id': promotion_product.discount_line_product_id.id,
                                                                    #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    #         'price_unit': promotion_product.discount_max_amount,
                                                                    #
                                                                    #     }
                                                                    #
                                                                    # if i.product_id.name not in self.order_line.mapped(
                                                                    #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    #         'product_id').ids:
                                                                    #     po_line.create(vals)

                                                                elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    chepest_result = -diskon_percentage

                                                                    # subtotal = diskon_percentage * int(
                                                                    #     taxes) / 100
                                                                    # resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    #     vals = {
                                                                    #         'order_id': self.id,
                                                                    #         # 'price_subtotal': resultsubtotal,
                                                                    #         'product_id': promotion_product.discount_line_product_id.id,
                                                                    #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    #         'price_unit': chepest_result,
                                                                    #
                                                                    #     }
                                                                    #
                                                                    # if i.product_id.name not in self.order_line.mapped(
                                                                    #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    #     'product_id').ids:
                                                                    #     po_line.create(vals)

                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                chepest_result = -diskon_percentage

                                                                # subtotal = diskon_percentage * int(
                                                                #     taxes) / 100
                                                                # resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    i.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                #     vals = {
                                                                #         'order_id': self.id,
                                                                #         # 'price_subtotal': resultsubtotal,
                                                                #         'product_id': promotion_product.discount_line_product_id.id,
                                                                #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                #         'price_unit': chepest_result,
                                                                #
                                                                #     }
                                                                #
                                                                # if i.product_id.name not in self.order_line.mapped(
                                                                #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                #     'product_id').ids:
                                                                #     po_line.create(vals)

                                                        elif promotion_product.discount_apply_on == 'on_order':

                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if order_line.price_unit > promotion_product.discount_max_amount:
                                                                    po_line = self.env['sale.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage

                                                                    # subtotal = diskon_percentage * int(taxes) / 100
                                                                    # resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #     # 'price_subtotal': resultsubtotal,
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        #     'price_unit': promotion_product.discount_max_amount,
                                                                        #
                                                                        # }
                                                                        #
                                                                        # po_line.create(vals)
                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'sale.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    on_order = -diskon_percentage

                                                                    # subtotal = diskon_percentage * int(
                                                                    #     taxes) / 100
                                                                    # resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #     # 'price_subtotal': resultsubtotal,
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        #     'price_unit': on_order,
                                                                        #
                                                                        # }
                                                                        #
                                                                        # po_line.create(vals)
                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                po_line = self.env[
                                                                    'sale.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                on_order = -diskon_percentage

                                                                # subtotal = diskon_percentage * int(
                                                                #     taxes) / 100
                                                                # resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    # vals = {
                                                                    #     'order_id': self.id,
                                                                    #     # 'price_subtotal': resultsubtotal,
                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    #     'price_unit': on_order,
                                                                    #
                                                                    # }
                                                                    #
                                                                    # po_line.create(vals)

                                                    elif promotion_product.discount_type == 'fixed_amount':

                                                        po_line = self.env['sale.order.line'].sudo()
                                                        order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_fixed_amount})

                                                        # vals = {
                                                        #     'order_id': self.id,
                                                        #      'product_id': order_line.product_id.id,
                                                        #      'description_product': 'fixed amount' + ' ' + ' on product :' + ' ' + promotion_product.name,
                                                        #     'price_unit': promotion_product.discount_fixed_amount,
                                                        #
                                                        # }
                                                        # if promotion_product.name not in self.order_line.mapped(
                                                        #         'description_product'):
                                                        #     po_line.create(vals)

                                                else:
                                                    if promotion_product.discount_type == 'percentage':
                                                        if promotion_product.discount_apply_on == 'specific_products':
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            result_ = -diskon_percentage
                                                            po_line = self.env['sale.order.line'].sudo()
                                                            # subtotal = order_line.price_subtotal * int(
                                                            #     taxes) / 100
                                                            # result_subt_total = order_line.price_subtotal + subtotal

                                                            for i in promotion_product.discount_specific_product_ids:
                                                                disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                if disc_product_id:
                                                                    if disc_product_id.id == order_line.product_id.id:
                                                                        if int(promotion_product.discount_max_amount) > 0:
                                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                            if order_line.price_unit > promotion_product.discount_max_amount:

                                                                                order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                                # vals = {
                                                                                #     'order_id': self.id,
                                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                #     'price_unit': promotion_product.discount_max_amount,
                                                                                #     # 'price_subtotal': result_subt_total,
                                                                                # }
                                                                                # if i.name not in self.order_line.mapped(
                                                                                #         'description_product'):
                                                                                #     po_line.create(vals)

                                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                                # vals = {
                                                                                #     'order_id': self.id,
                                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                #     'price_unit': result_,
                                                                                #     # 'price_subtotal': result_subt_total,
                                                                                # }
                                                                                # if i.name not in self.order_line.mapped(
                                                                                #         'description_product'):
                                                                                #     po_line.create(vals)
                                                                        elif int(
                                                                                promotion_product.discount_max_amount) == 0:

                                                                            order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            #     'price_unit': result_,
                                                                            #     # 'price_subtotal': result_subt_total,
                                                                            # }
                                                                            # if i.name not in self.order_line.mapped(
                                                                            #         'description_product'):
                                                                            #     po_line.create(vals)

                                                        elif promotion_product.discount_apply_on == 'cheapest_product':
                                                            min_price = min(self.order_line.mapped('price_unit'))
                                                            po_line = self.env['sale.order.line'].sudo()
                                                            product_min_price = self.order_line.filtered(
                                                                lambda r: r.price_unit == min_price)
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                    # subtotal = diskon_percentage * int(taxes) / 100
                                                                    # resultsubtotal = subtotal + product_min_price.price_unit
                                                                    for i in product_min_price:
                                                                        i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                    #     vals = {
                                                                    #         'order_id': self.id,
                                                                    #         # 'price_subtotal': resultsubtotal,
                                                                    #         'product_id': promotion_product.discount_line_product_id.id,
                                                                    #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    #         'price_unit': promotion_product.discount_max_amount,
                                                                    #
                                                                    #     }
                                                                    #
                                                                    # if i.product_id.name not in self.order_line.mapped(
                                                                    #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    #         'product_id').ids:
                                                                    #     po_line.create(vals)

                                                                elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    chepest_result = -diskon_percentage

                                                                    # subtotal = diskon_percentage * int(
                                                                    #     taxes) / 100
                                                                    # resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    #     vals = {
                                                                    #         'order_id': self.id,
                                                                    #         # 'price_subtotal': resultsubtotal,
                                                                    #         'product_id': promotion_product.discount_line_product_id.id,
                                                                    #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    #         'price_unit': chepest_result,
                                                                    #
                                                                    #     }
                                                                    #
                                                                    # if i.product_id.name not in self.order_line.mapped(
                                                                    #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    #     'product_id').ids:
                                                                    #     po_line.create(vals)

                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                chepest_result = -diskon_percentage

                                                                # subtotal = diskon_percentage * int(
                                                                #     taxes) / 100
                                                                # resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                #     vals = {
                                                                #         'order_id': self.id,
                                                                #         # 'price_subtotal': resultsubtotal,
                                                                #         'product_id': promotion_product.discount_line_product_id.id,
                                                                #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                #         'price_unit': chepest_result,
                                                                #
                                                                #     }
                                                                #
                                                                # if i.product_id.name not in self.order_line.mapped(
                                                                #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                #     'product_id').ids:
                                                                #     po_line.create(vals)

                                                        elif promotion_product.discount_apply_on == 'on_order':

                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if order_line.price_unit > promotion_product.discount_max_amount:
                                                                    po_line = self.env['sale.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage
                                                                    # subtotal = diskon_percentage * int(taxes) / 100
                                                                    # resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #     # 'price_subtotal': resultsubtotal,
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        #     'price_unit': promotion_product.discount_max_amount,
                                                                        #
                                                                        # }
                                                                        #
                                                                        # po_line.create(vals)
                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'sale.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    on_order = -diskon_percentage

                                                                    # subtotal = diskon_percentage * int(
                                                                    #     taxes) / 100
                                                                    # resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #     # 'price_subtotal': resultsubtotal,
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        #     'price_unit': on_order,
                                                                        #
                                                                        # }
                                                                        #
                                                                        # po_line.create(vals)
                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                po_line = self.env[
                                                                    'sale.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                on_order = -diskon_percentage

                                                                # subtotal = diskon_percentage * int(
                                                                #     taxes) / 100
                                                                # resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    # vals = {
                                                                    #     'order_id': self.id,
                                                                    #     # 'price_subtotal': resultsubtotal,
                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    #     'price_unit': on_order,
                                                                    #
                                                                    # }
                                                                    #
                                                                    # po_line.create(vals)

                                                    elif promotion_product.discount_type == 'fixed_amount':

                                                        po_line = self.env['sale.order.line'].sudo()
                                                        order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_fixed_amount})

                                                        # vals = {
                                                        #     'order_id': self.id,
                                                        #      'product_id': order_line.product_id.id,
                                                        #      'description_product': 'fixed amount' + ' ' + ' on product :' + ' ' + promotion_product.name,
                                                        #     'price_unit': promotion_product.discount_fixed_amount,
                                                        #
                                                        # }
                                                        # if promotion_product.name not in self.order_line.mapped(
                                                        #         'description_product'):
                                                        #     po_line.create(vals)

                                        elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':

                                            total = order_line.price_subtotal
                                            if total >= promotion_product.rule_minimum_amount:
                                                if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                    promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1

                                                    if promotion_product.discount_type == 'percentage':
                                                        if promotion_product.discount_apply_on == 'specific_products':
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            result_ = -diskon_percentage
                                                            po_line = self.env['sale.order.line'].sudo()
                                                            subtotal = order_line.price_subtotal * int(
                                                                taxes) / 100
                                                            result_subt_total = order_line.price_subtotal + subtotal

                                                            for i in promotion_product.discount_specific_product_ids:
                                                                disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                if disc_product_id:
                                                                    if disc_product_id.id == order_line.product_id.id:
                                                                        if int(promotion_product.discount_max_amount) > 0:
                                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                            if order_line.price_unit > promotion_product.discount_max_amount:

                                                                                order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                                # vals = {
                                                                                #     'order_id': self.id,
                                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                #     'price_unit': promotion_product.discount_max_amount,
                                                                                #     # 'price_subtotal': result_subt_total,
                                                                                # }
                                                                                # if i.name not in self.order_line.mapped(
                                                                                #         'description_product'):
                                                                                #     po_line.create(vals)

                                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                                # vals = {
                                                                                #     'order_id': self.id,
                                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                #     'price_unit': result_,
                                                                                #     # 'price_subtotal': result_subt_total,
                                                                                # }
                                                                                # if i.name not in self.order_line.mapped(
                                                                                #         'description_product'):
                                                                                #     po_line.create(vals)
                                                                        elif int(
                                                                                promotion_product.discount_max_amount) == 0:


                                                                            order_line.write({'is_discount': True,'discount': promotion_product.discount_percentage})
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            #     'price_unit': result_,
                                                                            #
                                                                            # }
                                                                            # if i.name not in self.order_line.mapped(
                                                                            #         'description_product'):
                                                                            #     po_line.create(vals)


                                                        elif promotion_product.discount_apply_on == 'cheapest_product':

                                                            min_price = min(
                                                                self.order_line.mapped('price_unit'))
                                                            po_line = self.env['sale.order.line'].sudo()
                                                            product_min_price = self.order_line.filtered(
                                                                lambda r: r.price_unit == min_price)
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100


                                                                    for i in product_min_price:
                                                                        i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                    #     vals = {
                                                                    #         'order_id': self.id,
                                                                    #
                                                                    #         'product_id': promotion_product.discount_line_product_id.id,
                                                                    #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    #         'price_unit': promotion_product.discount_max_amount,
                                                                    #
                                                                    #     }
                                                                    #
                                                                    # if i.product_id.name not in self.order_line.mapped(
                                                                    #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    #     'product_id').ids:
                                                                    #     po_line.create(vals)

                                                                elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    chepest_result = -diskon_percentage

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    #     vals = {
                                                                    #         'order_id': self.id,
                                                                    #
                                                                    #         'product_id': promotion_product.discount_line_product_id.id,
                                                                    #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    #         'price_unit': chepest_result,
                                                                    #
                                                                    #     }
                                                                    #
                                                                    # if i.product_id.name not in self.order_line.mapped(
                                                                    #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    #     'product_id').ids:
                                                                    #     po_line.create(vals)

                                                            elif int(
                                                                    promotion_product.discount_max_amount) == 0:
                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                chepest_result = -diskon_percentage





                                                                for i in product_min_price:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                #     vals = {
                                                                #         'order_id': self.id,
                                                                #
                                                                #         'product_id': promotion_product.discount_line_product_id.id,
                                                                #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                #         'price_unit': chepest_result,
                                                                #
                                                                #     }
                                                                #
                                                                # if i.product_id.name not in self.order_line.mapped(
                                                                #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                #     'product_id').ids:
                                                                #     po_line.create(vals)

                                                        elif promotion_product.discount_apply_on == 'on_order':

                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if order_line.price_unit > promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'sale.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage


                                                                    for i in order_line:
                                                                        i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        #     'price_unit': promotion_product.discount_max_amount,
                                                                        #
                                                                        # }
                                                                        #
                                                                        # po_line.create(vals)
                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'sale.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    on_order = -diskon_percentage

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        #     'price_unit': on_order,
                                                                        #
                                                                        # }
                                                                        #
                                                                        # po_line.create(vals)
                                                            elif int(
                                                                    promotion_product.discount_max_amount) == 0:
                                                                po_line = self.env[
                                                                    'sale.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                on_order = -diskon_percentage





                                                                for i in order_line:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    # vals = {
                                                                    #     'order_id': self.id,
                                                                    #
                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    #     'price_unit': on_order,
                                                                    #
                                                                    # }
                                                                    #
                                                                    # po_line.create(vals)

                                                    elif promotion_product.discount_type == 'fixed_amount':

                                                        po_line = self.env['sale.order.line'].sudo()
                                                        order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_fixed_amount})

                                                        # vals = {
                                                        #     'order_id': self.id,
                                                        #     'product_id': order_line.product_id.id,
                                                        #      'description_product': 'fixed amount' + ' ' + ' on product :' + ' ' + promotion_product.name,
                                                        #     'price_unit': promotion_product.discount_fixed_amount,
                                                        #
                                                        # }
                                                        # if promotion_product.name not in self.order_line.mapped(
                                                        #         'description_product'):
                                                        #     po_line.create(vals)

                                                else:
                                                    if promotion_product.discount_type == 'percentage':
                                                        if promotion_product.discount_apply_on == 'specific_products':
                                                            # taxes = order_line.tax_id.name
                                                            # if taxes:
                                                            #     taxes = taxes.rstrip(taxes[-1])
                                                            taxes = 0
                                                            if order_line.tax_id:
                                                                taxes = int(order_line.tax_id.amount)
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            result_ = -diskon_percentage
                                                            po_line = self.env['sale.order.line'].sudo()
                                                            subtotal = order_line.price_subtotal * int(
                                                                taxes) / 100
                                                            result_subt_total = order_line.price_subtotal + subtotal

                                                            for i in promotion_product.discount_specific_product_ids:
                                                                disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                if disc_product_id:
                                                                    if disc_product_id.id == order_line.product_id.id:
                                                                        if int(promotion_product.discount_max_amount) > 0:
                                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                            if order_line.price_unit > promotion_product.discount_max_amount:

                                                                                order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                                # vals = {
                                                                                #     'order_id': self.id,
                                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                #     'price_unit': promotion_product.discount_max_amount,
                                                                                #
                                                                                # }
                                                                                # if i.name not in self.order_line.mapped(
                                                                                #         'description_product'):
                                                                                #     po_line.create(vals)

                                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                                # vals = {
                                                                                #     'order_id': self.id,
                                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                #     'price_unit': result_,
                                                                                #
                                                                                # }
                                                                                # if i.name not in self.order_line.mapped(
                                                                                #         'description_product'):
                                                                                #     po_line.create(vals)
                                                                        elif int(
                                                                                promotion_product.discount_max_amount) == 0:

                                                                            order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            #     'price_unit': result_,
                                                                            #
                                                                            # }
                                                                            # if i.name not in self.order_line.mapped(
                                                                            #         'description_product'):
                                                                            #     po_line.create(vals)


                                                        elif promotion_product.discount_apply_on == 'cheapest_product':
                                                            min_price = min(self.order_line.mapped('price_unit'))
                                                            po_line = self.env['sale.order.line'].sudo()
                                                            product_min_price = self.order_line.filtered(
                                                                lambda r: r.price_unit == min_price)
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if product_min_price.price_unit > promotion_product.discount_max_amount:
                                                                    # taxes = order_line.tax_id.name
                                                                    # if taxes:
                                                                    #     taxes = taxes.rstrip(taxes[-1])

                                                                    taxes = 0
                                                                    if order_line.tax_id:
                                                                        taxes = int(order_line.tax_id.amount)

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                    subtotal = diskon_percentage * int(taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                    #     vals = {
                                                                    #         'order_id': self.id,
                                                                    #         'price_subtotal': resultsubtotal,
                                                                    #         'product_id': promotion_product.discount_line_product_id.id,
                                                                    #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    #         'price_unit': promotion_product.discount_max_amount,
                                                                    #
                                                                    #     }
                                                                    # if i.product_id.name not in self.order_line.mapped(
                                                                    #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    #         'product_id').ids:
                                                                    #     po_line.create(vals)

                                                                elif product_min_price.price_unit < promotion_product.discount_max_amount:
                                                                    # taxes = order_line.tax_id.name
                                                                    # if taxes:
                                                                    #     taxes = taxes.rstrip(taxes[-1])

                                                                    taxes = 0
                                                                    if order_line.tax_id:
                                                                        taxes = int(order_line.tax_id.amount)

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    chepest_result = -diskon_percentage





                                                                    for i in product_min_price:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    #     vals = {
                                                                    #         'order_id': self.id,
                                                                    #
                                                                    #         'product_id': promotion_product.discount_line_product_id.id,
                                                                    #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    #         'price_unit': chepest_result,
                                                                    #
                                                                    #     }
                                                                    #
                                                                    # if i.product_id.name not in self.order_line.mapped(
                                                                    #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    #     'product_id').ids:
                                                                    #     po_line.create(vals)

                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                chepest_result = -diskon_percentage
                                                                # taxes = order_line.tax_id.name
                                                                # if taxes:
                                                                #     taxes = taxes.rstrip(taxes[-1])

                                                                taxes = 0
                                                                if order_line.tax_id:
                                                                    taxes = int(order_line.tax_id.amount)
                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                #     vals = {
                                                                #         'order_id': self.id,
                                                                #         'price_subtotal': resultsubtotal,
                                                                #         'product_id': promotion_product.discount_line_product_id.id,
                                                                #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                #         'price_unit': chepest_result,
                                                                #
                                                                #     }
                                                                #
                                                                # if i.product_id.name not in self.order_line.mapped(
                                                                #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                #     'product_id').ids:
                                                                #     po_line.create(vals)

                                                        elif promotion_product.discount_apply_on == 'on_order':

                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if order_line.price_unit > promotion_product.discount_max_amount:
                                                                    po_line = self.env['sale.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage


                                                                    for i in order_line:
                                                                        i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        #     'price_unit': promotion_product.discount_max_amount,
                                                                        #
                                                                        # }
                                                                        #
                                                                        # po_line.create(vals)
                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'sale.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    on_order = -diskon_percentage



                                                                    for i in order_line:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        #     'price_unit': on_order,
                                                                        #
                                                                        # }
                                                                        #
                                                                        # po_line.create(vals)
                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                po_line = self.env[
                                                                    'sale.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage



                                                                for i in order_line:
                                                                    i.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                    # vals = {
                                                                    #     'order_id': self.id,
                                                                    #
                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    #     'price_unit': on_order,
                                                                    #
                                                                    # }
                                                                    #
                                                                    # po_line.create(vals)

                                                    elif promotion_product.discount_type == 'fixed_amount':

                                                        po_line = self.env['sale.order.line'].sudo()
                                                        order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_fixed_amount})
                    else:
                        for customer_id in promotion_product.rule_partners_domain:
                            for order_line in self.order_line:
                                if customer_id.id == self.partner_id.id and ((promotion_product.rule_min_quantity > 0 and int(order_line.product_uom_qty) >= promotion_product.rule_min_quantity) or (promotion_product.rule_minimum_amount > 0 and order_line.price_subtotal  >= promotion_product.rule_minimum_amount )):

                                    if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':
                                        # taxes = order_line.tax_id.name
                                        # if taxes:
                                        #     taxes = taxes.rstrip(taxes[-1])

                                        taxes = 0
                                        if order_line.tax_id:
                                            taxes = int(order_line.tax_id.amount)
                                        result = order_line.price_subtotal * int(taxes) / 100
                                        total = result + order_line.price_subtotal
                                        if total >= promotion_product.rule_minimum_amount:
                                            if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1

                                                if promotion_product.discount_type == 'percentage':
                                                    if promotion_product.discount_apply_on == 'specific_products':
                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                        result_ = -diskon_percentage
                                                        po_line = self.env['sale.order.line'].sudo()
                                                        subtotal = order_line.price_subtotal * int(
                                                            taxes) / 100
                                                        result_subt_total = order_line.price_subtotal + subtotal

                                                        for i in promotion_product.discount_specific_product_ids:
                                                            disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                            if disc_product_id:
                                                                if disc_product_id.id == order_line.product_id.id:
                                                                    if int(promotion_product.discount_max_amount) > 0:
                                                                        calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        if order_line.price_unit > promotion_product.discount_max_amount:

                                                                            order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            #     'price_unit': promotion_product.discount_max_amount,
                                                                            #
                                                                            # }
                                                                            # if i.name not in self.order_line.mapped(
                                                                            #         'description_product'):
                                                                            #     po_line.create(vals)

                                                                        elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                            order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            #     'price_unit': result_,
                                                                            #
                                                                            # }
                                                                            # if i.name not in self.order_line.mapped(
                                                                            #         'description_product'):
                                                                            #     po_line.create(vals)
                                                                    elif int(
                                                                            promotion_product.discount_max_amount) == 0:

                                                                        order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                        #     'price_unit': result_,
                                                                        #
                                                                        # }
                                                                        # if i.name not in self.order_line.mapped(
                                                                        #         'description_product'):
                                                                        #     po_line.create(vals)


                                                    elif promotion_product.discount_apply_on == 'cheapest_product':
                                                        min_price = min(
                                                            self.order_line.mapped('price_unit'))
                                                        po_line = self.env['sale.order.line'].sudo()
                                                        product_min_price = self.order_line.filtered(
                                                            lambda r: r.price_unit == min_price)
                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                #     vals = {
                                                                #         'order_id': self.id,
                                                                #
                                                                #         'product_id': promotion_product.discount_line_product_id.id,
                                                                #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                #         'price_unit': promotion_product.discount_max_amount,
                                                                #
                                                                #     }
                                                                #
                                                                # if i.product_id.name not in self.order_line.mapped(
                                                                #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                #     'product_id').ids:
                                                                #     po_line.create(vals)

                                                            elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                chepest_result = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                #     vals = {
                                                                #         'order_id': self.id,
                                                                #
                                                                #         'product_id': promotion_product.discount_line_product_id.id,
                                                                #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                #         'price_unit': chepest_result,
                                                                #
                                                                #     }
                                                                #
                                                                # if i.product_id.name not in self.order_line.mapped(
                                                                #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                #     'product_id').ids:
                                                                #     po_line.create(vals)

                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                            additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                            # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                            dis_res = order_line.harga_satuan_baru
                                                            disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                            chepest_result = -diskon_percentage

                                                            subtotal = diskon_percentage * int(
                                                                taxes) / 100
                                                            resultsubtotal = subtotal + product_min_price.price_unit

                                                            for i in product_min_price:
                                                                # i.write({'discount': promotion_product.discount_percentage})
                                                                i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                            #     vals = {
                                                            #         'order_id': self.id,
                                                            #
                                                            #         'product_id': promotion_product.discount_line_product_id.id,
                                                            #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                            #         'price_unit': chepest_result,
                                                            #
                                                            #     }
                                                            #
                                                            # if i.product_id.name not in self.order_line.mapped(
                                                            #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                            #     'product_id').ids:
                                                            #     po_line.create(vals)

                                                    elif promotion_product.discount_apply_on == 'on_order':

                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if order_line.price_unit > promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'sale.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                    # vals = {
                                                                    #     'order_id': self.id,
                                                                    #
                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    #     'price_unit': promotion_product.discount_max_amount,
                                                                    #
                                                                    # }
                                                                    #
                                                                    # po_line.create(vals)
                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'sale.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                on_order = -diskon_percentage


                                                                for i in order_line:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    # vals = {
                                                                    #     'order_id': self.id,
                                                                    #
                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    #     'price_unit': on_order,
                                                                    #
                                                                    # }
                                                                    #
                                                                    # po_line.create(vals)
                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            po_line = self.env[
                                                                'sale.order.line'].sudo()
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                            # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                            dis_res = order_line.harga_satuan_baru
                                                            disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                            on_order = -diskon_percentage


                                                            for i in order_line:
                                                                # i.write({'discount': promotion_product.discount_percentage})
                                                                i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                # vals = {
                                                                #     'order_id': self.id,
                                                                #
                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                #     'price_unit': on_order,
                                                                #
                                                                # }
                                                                #
                                                                # po_line.create(vals)

                                                elif promotion_product.discount_type == 'fixed_amount':

                                                    po_line = self.env['sale.order.line'].sudo()
                                                    order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_fixed_amount})

                                                    # vals = {
                                                    #     'order_id': self.id,
                                                    #     'product_id': order_line.product_id.id,
                                                    #      'description_product': 'fixed amount' + ' ' + ' on product :' + ' ' + promotion_product.name,
                                                    #     'price_unit': promotion_product.discount_fixed_amount,
                                                    #
                                                    # }
                                                    # if promotion_product.name not in self.order_line.mapped(
                                                    #         'description_product'):
                                                    #     po_line.create(vals)

                                            else:
                                                if promotion_product.discount_type == 'percentage':
                                                    if promotion_product.discount_apply_on == 'specific_products':
                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                        result_ = -diskon_percentage
                                                        po_line = self.env['sale.order.line'].sudo()
                                                        subtotal = order_line.price_subtotal * int(
                                                            taxes) / 100
                                                        result_subt_total = order_line.price_subtotal + subtotal

                                                        for i in promotion_product.discount_specific_product_ids:
                                                            disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                            if disc_product_id:
                                                                if disc_product_id.id == order_line.product_id.id:
                                                                    if int(promotion_product.discount_max_amount) > 0:
                                                                        calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        if order_line.price_unit > promotion_product.discount_max_amount:

                                                                            order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            #     'price_unit': promotion_product.discount_max_amount,
                                                                            #
                                                                            # }
                                                                            # if i.name not in self.order_line.mapped(
                                                                            #         'description_product'):
                                                                            #     po_line.create(vals)

                                                                        elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                            order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            #     'price_unit': result_,
                                                                            #
                                                                            # }
                                                                            # if i.name not in self.order_line.mapped(
                                                                            #         'description_product'):
                                                                            #     po_line.create(vals)
                                                                    elif int(
                                                                            promotion_product.discount_max_amount) == 0:

                                                                        order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                        #     'price_unit': result_,
                                                                        #     'price_subtotal': result_subt_total,
                                                                        # }
                                                                        # if i.name not in self.order_line.mapped(
                                                                        #         'description_product'):
                                                                        #     po_line.create(vals)


                                                    elif promotion_product.discount_apply_on == 'cheapest_product':
                                                        min_price = min(
                                                            self.order_line.mapped('price_unit'))
                                                        po_line = self.env['sale.order.line'].sudo()
                                                        product_min_price = self.order_line.filtered(
                                                            lambda r: r.price_unit == min_price)
                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100


                                                                for i in product_min_price:
                                                                    i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                #     vals = {
                                                                #         'order_id': self.id,
                                                                #
                                                                #         'product_id': promotion_product.discount_line_product_id.id,
                                                                #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                #         'price_unit': promotion_product.discount_max_amount,
                                                                #
                                                                #     }
                                                                #
                                                                # if i.product_id.name not in self.order_line.mapped(
                                                                #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                #     'product_id').ids:
                                                                #     po_line.create(vals)

                                                            elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                chepest_result = -diskon_percentage



                                                                for i in product_min_price:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                #     vals = {
                                                                #         'order_id': self.id,
                                                                #
                                                                #         'product_id': promotion_product.discount_line_product_id.id,
                                                                #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                #         'price_unit': chepest_result,
                                                                #
                                                                #     }
                                                                #
                                                                # if i.product_id.name not in self.order_line.mapped(
                                                                #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                #     'product_id').ids:
                                                                #     po_line.create(vals)

                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                            additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                            # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                            dis_res = order_line.harga_satuan_baru
                                                            disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                            chepest_result = -diskon_percentage



                                                            for i in product_min_price:
                                                                # i.write({'discount': promotion_product.discount_percentage})
                                                                i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                            #     vals = {
                                                            #         'order_id': self.id,
                                                            #
                                                            #         'product_id': promotion_product.discount_line_product_id.id,
                                                            #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                            #         'price_unit': chepest_result,
                                                            #
                                                            #     }
                                                            #
                                                            # if i.product_id.name not in self.order_line.mapped(
                                                            #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                            #     'product_id').ids:
                                                            #     po_line.create(vals)

                                                    elif promotion_product.discount_apply_on == 'on_order':

                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if order_line.price_unit > promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'sale.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage



                                                                for i in order_line:
                                                                    i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                    # vals = {
                                                                    #     'order_id': self.id,
                                                                    #
                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    #     'price_unit': promotion_product.discount_max_amount,
                                                                    #
                                                                    # }
                                                                    #
                                                                    # po_line.create(vals)
                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'sale.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                on_order = -diskon_percentage


                                                                for i in order_line:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    # vals = {
                                                                    #     'order_id': self.id,
                                                                    #
                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    #     'price_unit': on_order,
                                                                    #
                                                                    # }
                                                                    #
                                                                    # po_line.create(vals)
                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            po_line = self.env[
                                                                'sale.order.line'].sudo()
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                            # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                            dis_res = order_line.harga_satuan_baru
                                                            disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                            on_order = -diskon_percentage


                                                            for i in order_line:
                                                                # i.write({'discount': promotion_product.discount_percentage})
                                                                i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                # vals = {
                                                                #     'order_id': self.id,
                                                                #
                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                #     'price_unit': on_order,
                                                                #
                                                                # }
                                                                #
                                                                # po_line.create(vals)

                                                elif promotion_product.discount_type == 'fixed_amount':

                                                    po_line = self.env['sale.order.line'].sudo()
                                                    order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_fixed_amount})

                                                    # vals = {
                                                    #     'order_id': self.id,
                                                    #      'product_id': order_line.product_id.id,
                                                    #      'description_product': 'fixed amount' + ' ' + ' on product :' + ' ' + promotion_product.name,
                                                    #     'price_unit': promotion_product.discount_fixed_amount,
                                                    #
                                                    # }
                                                    # if promotion_product.name not in self.order_line.mapped(
                                                    #         'description_product'):
                                                    #     po_line.create(vals)

                                    elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':
                                        total = order_line.price_subtotal
                                        if total >= promotion_product.rule_minimum_amount:
                                            if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1

                                                if promotion_product.discount_type == 'percentage':
                                                    if promotion_product.discount_apply_on == 'specific_products':
                                                        # diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                        # result_ = -diskon_percentage
                                                        # po_line = self.env['sale.order.line'].sudo()
                                                        # subtotal = order_line.price_subtotal * int(
                                                        #     taxes) / 100
                                                        # result_subt_total = order_line.price_subtotal + subtotal

                                                        for i in promotion_product.discount_specific_product_ids:
                                                            disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                            if disc_product_id:
                                                                if disc_product_id.id == order_line.product_id.id:
                                                                    if int(promotion_product.discount_max_amount) > 0:
                                                                        calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        if order_line.price_unit > promotion_product.discount_max_amount:

                                                                            order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            #     'price_unit': promotion_product.discount_max_amount,
                                                                            #
                                                                            # }
                                                                            # if i.name not in self.order_line.mapped(
                                                                            #         'description_product'):
                                                                            #     po_line.create(vals)

                                                                        elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                            order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            #     'price_unit': result_,
                                                                            #
                                                                            # }
                                                                            # if i.name not in self.order_line.mapped(
                                                                            #         'description_product'):
                                                                            #     po_line.create(vals)
                                                                    elif int(
                                                                            promotion_product.discount_max_amount) == 0:

                                                                        order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                        #     'price_unit': result_,
                                                                        #
                                                                        # }
                                                                        # if i.name not in self.order_line.mapped(
                                                                        #         'description_product'):
                                                                        #     po_line.create(vals)


                                                    elif promotion_product.discount_apply_on == 'cheapest_product':
                                                        min_price = min(
                                                            self.order_line.mapped('price_unit'))
                                                        po_line = self.env['sale.order.line'].sudo()
                                                        product_min_price = self.order_line.filtered(
                                                            lambda r: r.price_unit == min_price)
                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                # diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                #
                                                                # subtotal = diskon_percentage * int(
                                                                #     taxes) / 100
                                                                # resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                #     vals = {
                                                                #         'order_id': self.id,
                                                                #
                                                                #         'product_id': promotion_product.discount_line_product_id.id,
                                                                #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                #         'price_unit': promotion_product.discount_max_amount,
                                                                #
                                                                #     }
                                                                #
                                                                # if i.product_id.name not in self.order_line.mapped(
                                                                #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                #     'product_id').ids:
                                                                #     po_line.create(vals)

                                                            elif product_min_price.price_unit < promotion_product.discount_max_amount:
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res

                                                                # diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                # chepest_result = -diskon_percentage
                                                                #
                                                                # subtotal = diskon_percentage * int(
                                                                #     taxes) / 100
                                                                # resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                #     vals = {
                                                                #         'order_id': self.id,
                                                                #
                                                                #         'product_id': promotion_product.discount_line_product_id.id,
                                                                #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                #         'price_unit': chepest_result,
                                                                #
                                                                #     }
                                                                #
                                                                # if i.product_id.name not in self.order_line.mapped(
                                                                #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                #     'product_id').ids:
                                                                #     po_line.create(vals)

                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            # diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                            # chepest_result = -diskon_percentage
                                                            #
                                                            # subtotal = diskon_percentage * int(
                                                            #     taxes) / 100
                                                            # resultsubtotal = subtotal + product_min_price.price_unit

                                                            for i in product_min_price:
                                                                i.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                            #     vals = {
                                                            #         'order_id': self.id,
                                                            #
                                                            #         'product_id': promotion_product.discount_line_product_id.id,
                                                            #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                            #         'price_unit': chepest_result,
                                                            #
                                                            #     }
                                                            #
                                                            # if i.product_id.name not in self.order_line.mapped(
                                                            #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                            #     'product_id').ids:
                                                            #     po_line.create(vals)

                                                    elif promotion_product.discount_apply_on == 'on_order':

                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if order_line.price_unit > promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'sale.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage


                                                                for i in order_line:
                                                                    i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                    # vals = {
                                                                    #     'order_id': self.id,
                                                                    #
                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    #     'price_unit': promotion_product.discount_max_amount,
                                                                    #
                                                                    # }
                                                                    #
                                                                    # po_line.create(vals)
                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'sale.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                on_order = -diskon_percentage



                                                                for i in order_line:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    # vals = {
                                                                    #     'order_id': self.id,
                                                                    #
                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    #     'price_unit': on_order,
                                                                    #
                                                                    # }
                                                                    #
                                                                    # po_line.create(vals)
                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            po_line = self.env[
                                                                'sale.order.line'].sudo()
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                            # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                            dis_res = order_line.harga_satuan_baru
                                                            disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                            on_order = -diskon_percentage



                                                            for i in order_line:
                                                                # i.write({'discount': promotion_product.discount_percentage})
                                                                i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                # vals = {
                                                                #     'order_id': self.id,
                                                                #
                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                #     'price_unit': on_order,
                                                                #
                                                                # }
                                                                #
                                                                # po_line.create(vals)

                                                elif promotion_product.discount_type == 'fixed_amount':

                                                    po_line = self.env['sale.order.line'].sudo()
                                                    order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})

                                                    # vals = {
                                                    #     'order_id': self.id,
                                                    #      'product_id': order_line.product_id.id,
                                                    #      'description_product': 'fixed amount' + ' ' + ' on product :' + ' ' + promotion_product.name,
                                                    #     'price_unit': promotion_product.discount_fixed_amount,
                                                    #
                                                    # }
                                                    # if promotion_product.name not in self.order_line.mapped(
                                                    #         'description_product'):
                                                    #     po_line.create(vals)
                                            else:
                                                if promotion_product.discount_type == 'percentage':
                                                    if promotion_product.discount_apply_on == 'specific_products':
                                                        # diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                        # result_ = -diskon_percentage
                                                        # po_line = self.env['sale.order.line'].sudo()
                                                        # subtotal = order_line.price_subtotal * int(
                                                        #     taxes) / 100
                                                        # result_subt_total = order_line.price_subtotal + subtotal

                                                        for i in promotion_product.discount_specific_product_ids:
                                                            disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                            if disc_product_id:
                                                                if disc_product_id.id == order_line.product_id.id:
                                                                    if int(promotion_product.discount_max_amount) > 0:
                                                                        calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        if order_line.price_unit > promotion_product.discount_max_amount:

                                                                            order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            #     'price_unit': promotion_product.discount_max_amount,
                                                                            #
                                                                            # }
                                                                            # if i.name not in self.order_line.mapped(
                                                                            #         'description_product'):
                                                                            #     po_line.create(vals)

                                                                        elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                            order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            #     'price_unit': result_,
                                                                            #
                                                                            # }
                                                                            # if i.name not in self.order_line.mapped(
                                                                            #         'description_product'):
                                                                            #     po_line.create(vals)
                                                                    elif int(
                                                                            promotion_product.discount_max_amount) == 0:

                                                                        order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                        #     'price_unit': result_,
                                                                        #
                                                                        # }
                                                                        # if i.name not in self.order_line.mapped(
                                                                        #         'description_product'):
                                                                        #     po_line.create(vals)


                                                    elif promotion_product.discount_apply_on == 'cheapest_product':
                                                        min_price = min(
                                                            self.order_line.mapped('price_unit'))
                                                        po_line = self.env['sale.order.line'].sudo()
                                                        product_min_price = self.order_line.filtered(
                                                            lambda r: r.price_unit == min_price)
                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                # diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                #
                                                                # subtotal = diskon_percentage * int(
                                                                #     taxes) / 100
                                                                # resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                #     vals = {
                                                                #         'order_id': self.id,
                                                                #
                                                                #         'product_id': promotion_product.discount_line_product_id.id,
                                                                #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                #         'price_unit': promotion_product.discount_max_amount,
                                                                #
                                                                #     }
                                                                #
                                                                # if i.product_id.name not in self.order_line.mapped(
                                                                #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                #     'product_id').ids:
                                                                #     po_line.create(vals)

                                                            elif product_min_price.price_unit < promotion_product.discount_max_amount:
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res

                                                                # diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                # chepest_result = -diskon_percentage
                                                                #
                                                                # subtotal = diskon_percentage * int(
                                                                #     taxes) / 100
                                                                # resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                #     vals = {
                                                                #         'order_id': self.id,
                                                                #
                                                                #         'product_id': promotion_product.discount_line_product_id.id,
                                                                #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                #         'price_unit': chepest_result,
                                                                #
                                                                #     }
                                                                #
                                                                # if i.product_id.name not in self.order_line.mapped(
                                                                #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                #     'product_id').ids:
                                                                #     po_line.create(vals)

                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                            # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                            dis_res = order_line.harga_satuan_baru
                                                            disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                            # diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                            # chepest_result = -diskon_percentage
                                                            #
                                                            # subtotal = diskon_percentage * int(
                                                            #     taxes) / 100
                                                            # resultsubtotal = subtotal + product_min_price.price_unit

                                                            for i in product_min_price:
                                                                # i.write({'discount': promotion_product.discount_percentage})
                                                                i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                            #     vals = {
                                                            #         'order_id': self.id,
                                                            #
                                                            #         'product_id': promotion_product.discount_line_product_id.id,
                                                            #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                            #         'price_unit': chepest_result,
                                                            #
                                                            #     }
                                                            #
                                                            # if i.product_id.name not in self.order_line.mapped(
                                                            #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                            #     'product_id').ids:
                                                            #     po_line.create(vals)

                                                    elif promotion_product.discount_apply_on == 'on_order':

                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if order_line.price_unit > promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'sale.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage

                                                                for i in order_line:
                                                                    i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                    # vals = {
                                                                    #     'order_id': self.id,
                                                                    #
                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    #     'price_unit': promotion_product.discount_max_amount,
                                                                    #
                                                                    # }
                                                                    #
                                                                    # po_line.create(vals)
                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'sale.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                on_order = -diskon_percentage

                                                                for i in order_line:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    # vals = {
                                                                    #     'order_id': self.id,
                                                                    #
                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    #     'price_unit': on_order,
                                                                    #
                                                                    # }
                                                                    #
                                                                    # po_line.create(vals)
                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            po_line = self.env[
                                                                'sale.order.line'].sudo()
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                            # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                            dis_res = order_line.harga_satuan_baru
                                                            disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                            on_order = -diskon_percentage

                                                            for i in order_line:
                                                                # i.write({'discount': promotion_product.discount_percentage})
                                                                i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                # vals = {
                                                                #     'order_id': self.id,
                                                                #
                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                #     'price_unit': on_order,
                                                                #
                                                                # }
                                                                #
                                                                # po_line.create(vals)

                                                elif promotion_product.discount_type == 'fixed_amount':

                                                    po_line = self.env['sale.order.line'].sudo()
                                                    order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_fixed_amount})
                elif promotion_product.product_ids:
                    product_ids_update = []
                    for ids in promotion_product.product_ids:
                        product_ids_update.append(ids.id)
                    if promotion_product.rule_date_from and promotion_product.rule_date_to:
                        for product_ids_list in promotion_product.product_ids:
                            for order_line in self.order_line:
                                if product_ids_list.id == order_line.product_id.id and ((promotion_product.rule_min_quantity > 0 and int(order_line.product_uom_qty) >= promotion_product.rule_min_quantity) or (promotion_product.rule_minimum_amount > 0 and order_line.price_subtotal  >= promotion_product.rule_minimum_amount )):

                                    date_order = datetime.strptime(str(self.date_order),
                                                                   "%Y-%m-%d %H:%M:%S")
                                    start_date = datetime.strptime(str(promotion_product.rule_date_from),
                                                                   "%Y-%m-%d %H:%M:%S")
                                    end_date = datetime.strptime(str(promotion_product.rule_date_to),
                                                                 "%Y-%m-%d %H:%M:%S")
                                    if date_order <= end_date and date_order >= start_date:
                                        if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':
                                            # print("TAX INCLUDED")
                                            # taxes = order_line.tax_id.name
                                            # if taxes:
                                            #     taxes = taxes.rstrip(taxes[-1])

                                            taxes = 0
                                            if order_line.tax_id:
                                                taxes = int(order_line.tax_id.amount)
                                            result = order_line.price_subtotal * int(taxes) / 100
                                            total = result + order_line.price_subtotal
                                            if total >= promotion_product.rule_minimum_amount:
                                                if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                    promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1
                                                    if promotion_product.discount_type == 'percentage':
                                                        if promotion_product.discount_apply_on == 'specific_products':


                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            result_ = -diskon_percentage
                                                            po_line = self.env['sale.order.line'].sudo()
                                                            subtotal = order_line.price_subtotal * int(
                                                                taxes) / 100
                                                            result_subt_total = order_line.price_subtotal + subtotal

                                                            for i in promotion_product.discount_specific_product_ids:
                                                                disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                if disc_product_id:
                                                                    if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                        if int(promotion_product.discount_max_amount) > 0:
                                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                            if order_line.price_unit > promotion_product.discount_max_amount:

                                                                                order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                                # vals = {
                                                                                #     'order_id': self.id,
                                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                #     'price_unit': promotion_product.discount_max_amount,
                                                                                #
                                                                                # }
                                                                                # if i.name not in self.order_line.mapped(
                                                                                #         'description_product'):
                                                                                #     po_line.create(vals)

                                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                                # vals = {
                                                                                #     'order_id': self.id,
                                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                #     'price_unit': result_,
                                                                                #
                                                                                # }
                                                                                # if i.name not in self.order_line.mapped(
                                                                                #         'description_product'):
                                                                                #     po_line.create(vals)
                                                                        elif int(
                                                                                promotion_product.discount_max_amount) == 0:
                                                                            # print("DISKON amount 0")

                                                                            order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            #     'price_unit': result_,
                                                                            #
                                                                            # }
                                                                            # if i.name not in self.order_line.mapped(
                                                                            #         'description_product'):
                                                                            #     po_line.create(vals)


                                                        elif promotion_product.discount_apply_on == 'cheapest_product':
                                                            product_list_update = self.env['sale.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])
                                                            # min_price = min(
                                                            #     self.order_line.mapped('price_unit'))
                                                            min_price = min(
                                                                product_list_update.mapped('price_unit'))
                                                            po_line = self.env['sale.order.line'].sudo()
                                                            product_min_price = self.order_line.filtered(
                                                                lambda r: r.price_unit == min_price)
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                    subtotal = diskon_percentage * int(taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                    #     vals = {
                                                                    #         'order_id': self.id,
                                                                    #
                                                                    #         'product_id': promotion_product.discount_line_product_id.id,
                                                                    #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    #         'price_unit': promotion_product.discount_max_amount,
                                                                    #
                                                                    #     }
                                                                    #
                                                                    # if i.product_id.name not in self.order_line.mapped(
                                                                    #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    #     'product_id').ids:
                                                                    #     po_line.create(vals)

                                                                elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    chepest_result = -diskon_percentage



                                                                    for i in product_min_price:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    #     vals = {
                                                                    #         'order_id': self.id,
                                                                    #
                                                                    #         'product_id': promotion_product.discount_line_product_id.id,
                                                                    #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    #         'price_unit': chepest_result,
                                                                    #
                                                                    #     }
                                                                    #
                                                                    # if i.product_id.name not in self.order_line.mapped(
                                                                    #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    #     'product_id').ids:
                                                                    #     po_line.create(vals)

                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                chepest_result = -diskon_percentage


                                                                for i in product_min_price:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                #     vals = {
                                                                #         'order_id': self.id,
                                                                #
                                                                #         'product_id': promotion_product.discount_line_product_id.id,
                                                                #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                #         'price_unit': chepest_result,
                                                                #
                                                                #     }
                                                                #
                                                                # if i.product_id.name not in self.order_line.mapped(
                                                                #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                #     'product_id').ids:
                                                                #     po_line.create(vals)

                                                        elif promotion_product.discount_apply_on == 'on_order':

                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if order_line.price_unit > promotion_product.discount_max_amount:
                                                                    po_line = self.env['sale.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage



                                                                    for i in order_line:
                                                                        i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        #     'price_unit': promotion_product.discount_max_amount,
                                                                        #
                                                                        # }
                                                                        #
                                                                        # po_line.create(vals)
                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'sale.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    on_order = -diskon_percentage



                                                                    for i in order_line:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        #     'price_unit': on_order,
                                                                        #
                                                                        # }
                                                                        #
                                                                        # po_line.create(vals)
                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                po_line = self.env[
                                                                    'sale.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                on_order = -diskon_percentage



                                                                for i in order_line:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    # vals = {
                                                                    #     'order_id': self.id,
                                                                    #
                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    #     'price_unit': on_order,
                                                                    #
                                                                    # }
                                                                    #
                                                                    # po_line.create(vals)

                                                    elif promotion_product.discount_type == 'fixed_amount':

                                                        po_line = self.env['sale.order.line'].sudo()
                                                        order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_fixed_amount})

                                                        # vals = {
                                                        #     'order_id': self.id,
                                                        #     'product_id': order_line.product_id.id,
                                                        #      'description_product': 'fixed amount' + ' ' + ' on product :' + ' ' + promotion_product.name,
                                                        #     'price_unit': promotion_product.discount_fixed_amount,
                                                        #
                                                        # }
                                                        # if promotion_product.name not in self.order_line.mapped(
                                                        #         'description_product'):
                                                        #     po_line.create(vals)

                                                else:
                                                    if promotion_product.discount_type == 'percentage':
                                                        if promotion_product.discount_apply_on == 'specific_products':
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            result_ = -diskon_percentage
                                                            po_line = self.env['sale.order.line'].sudo()
                                                            subtotal = order_line.price_subtotal * int(
                                                                taxes) / 100
                                                            result_subt_total = order_line.price_subtotal + subtotal

                                                            for i in promotion_product.discount_specific_product_ids:
                                                                disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                if disc_product_id:
                                                                    if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                        if int(promotion_product.discount_max_amount) > 0:
                                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                            if order_line.price_unit > promotion_product.discount_max_amount:

                                                                                order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                                # vals = {
                                                                                #     'order_id': self.id,
                                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                #     'price_unit': promotion_product.discount_max_amount,
                                                                                #
                                                                                # }
                                                                                # if i.name not in self.order_line.mapped(
                                                                                #         'description_product'):
                                                                                #     po_line.create(vals)

                                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                                # vals = {
                                                                                #     'order_id': self.id,
                                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                #     'price_unit': result_,
                                                                                #
                                                                                # }
                                                                                # if i.name not in self.order_line.mapped(
                                                                                #         'description_product'):
                                                                                #     po_line.create(vals)
                                                                        elif int(
                                                                                promotion_product.discount_max_amount) == 0:

                                                                            order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            #     'price_unit': result_,
                                                                            #
                                                                            # }
                                                                            # if i.name not in self.order_line.mapped(
                                                                            #         'description_product'):
                                                                            #     po_line.create(vals)

                                                        elif promotion_product.discount_apply_on == 'cheapest_product':
                                                            product_list_update = self.env['sale.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])
                                                            # min_price = min(
                                                            #     self.order_line.mapped('price_unit'))
                                                            min_price = min(
                                                                product_list_update.mapped('price_unit'))
                                                            po_line = self.env['sale.order.line'].sudo()
                                                            product_min_price = self.order_line.filtered(
                                                                lambda r: r.price_unit == min_price)
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                    subtotal = diskon_percentage * int(taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit
                                                                    for i in product_min_price:
                                                                        i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                    #     vals = {
                                                                    #         'order_id': self.id,
                                                                    #
                                                                    #         'product_id': promotion_product.discount_line_product_id.id,
                                                                    #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    #         'price_unit': promotion_product.discount_max_amount,
                                                                    #
                                                                    #     }
                                                                    #
                                                                    # if i.product_id.name not in self.order_line.mapped(
                                                                    #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    #     'product_id').ids:
                                                                    #     po_line.create(vals)

                                                                elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    chepest_result = -diskon_percentage

                                                                    for i in product_min_price:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    #     vals = {
                                                                    #         'order_id': self.id,
                                                                    #
                                                                    #         'product_id': promotion_product.discount_line_product_id.id,
                                                                    #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    #         'price_unit': chepest_result,
                                                                    #
                                                                    #     }
                                                                    #
                                                                    # if i.product_id.name not in self.order_line.mapped(
                                                                    #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    #     'product_id').ids:
                                                                    #     po_line.create(vals)

                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                chepest_result = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                #     vals = {
                                                                #         'order_id': self.id,
                                                                #
                                                                #         'product_id': promotion_product.discount_line_product_id.id,
                                                                #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                #         'price_unit': chepest_result,
                                                                #
                                                                #     }
                                                                #
                                                                # if i.product_id.name not in self.order_line.mapped(
                                                                #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                #     'product_id').ids:
                                                                #     po_line.create(vals)

                                                        elif promotion_product.discount_apply_on == 'on_order':

                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if order_line.price_unit > promotion_product.discount_max_amount:
                                                                    po_line = self.env['sale.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage


                                                                    for i in order_line:
                                                                        i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        #     'price_unit': promotion_product.discount_max_amount,
                                                                        #
                                                                        # }
                                                                        #
                                                                        # po_line.create(vals)
                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'sale.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    on_order = -diskon_percentage

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #     'price_subtotal': resultsubtotal,
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        #     'price_unit': on_order,
                                                                        #
                                                                        # }
                                                                        #
                                                                        # po_line.create(vals)
                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                po_line = self.env[
                                                                    'sale.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                on_order = -diskon_percentage



                                                                for i in order_line:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    # vals = {
                                                                    #     'order_id': self.id,
                                                                    #
                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    #     'price_unit': on_order,
                                                                    #
                                                                    # }
                                                                    #
                                                                    # po_line.create(vals)

                                                    elif promotion_product.discount_type == 'fixed_amount':

                                                        po_line = self.env['sale.order.line'].sudo()
                                                        order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_fixed_amount})

                                                        # vals = {
                                                        #     'order_id': self.id,
                                                        #     'product_id': order_line.product_id.id,
                                                        #      'description_product': 'fixed amount' + ' ' + ' on product :' + ' ' + promotion_product.name,
                                                        #     'price_unit': promotion_product.discount_fixed_amount,
                                                        #
                                                        # }
                                                        # if promotion_product.name not in self.order_line.mapped(
                                                        #         'description_product'):
                                                        #     po_line.create(vals)

                                        elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':

                                            total = order_line.price_subtotal
                                            if total >= promotion_product.rule_minimum_amount:
                                                if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                    promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1

                                                    if promotion_product.discount_type == 'percentage':
                                                        if promotion_product.discount_apply_on == 'specific_products':
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            result_ = -diskon_percentage
                                                            po_line = self.env['sale.order.line'].sudo()
                                                            subtotal = order_line.price_subtotal * int(
                                                                taxes) / 100
                                                            result_subt_total = order_line.price_subtotal + subtotal

                                                            for i in promotion_product.discount_specific_product_ids:
                                                                disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                if disc_product_id:
                                                                    if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                        if int(promotion_product.discount_max_amount) > 0:
                                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                            if order_line.price_unit > promotion_product.discount_max_amount:
                                                                                order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})

                                                                                # vals = {
                                                                                #     'order_id': self.id,
                                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                #     'price_unit': promotion_product.discount_max_amount,
                                                                                #
                                                                                # }
                                                                                # if i.name not in self.order_line.mapped(
                                                                                #         'description_product'):
                                                                                #     po_line.create(vals)

                                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                                # vals = {
                                                                                #     'order_id': self.id,
                                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                #     'price_unit': result_,
                                                                                #
                                                                                # }
                                                                                # if i.name not in self.order_line.mapped(
                                                                                #         'description_product'):
                                                                                #     po_line.create(vals)
                                                                        elif int(
                                                                                promotion_product.discount_max_amount) == 0:
                                                                            # print("max amount kosong")

                                                                            order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            #     'price_unit': result_,
                                                                            #
                                                                            # }
                                                                            # if i.name not in self.order_line.mapped(
                                                                            #         'description_product'):
                                                                            #     po_line.create(vals)


                                                        elif promotion_product.discount_apply_on == 'cheapest_product':

                                                            product_list_update = self.env['sale.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])
                                                            # min_price = min(
                                                            #     self.order_line.mapped('price_unit'))
                                                            min_price = min(
                                                                product_list_update.mapped('price_unit'))
                                                            po_line = self.env['sale.order.line'].sudo()
                                                            product_min_price = self.order_line.filtered(
                                                                lambda r: r.price_unit == min_price)
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                    #     vals = {
                                                                    #         'order_id': self.id,
                                                                    #
                                                                    #         'product_id': promotion_product.discount_line_product_id.id,
                                                                    #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    #         'price_unit': promotion_product.discount_max_amount,
                                                                    #
                                                                    #     }
                                                                    #
                                                                    # if i.product_id.name not in self.order_line.mapped(
                                                                    #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    #     'product_id').ids:
                                                                    #     po_line.create(vals)

                                                                elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    chepest_result = -diskon_percentage

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    #     vals = {
                                                                    #         'order_id': self.id,
                                                                    #
                                                                    #         'product_id': promotion_product.discount_line_product_id.id,
                                                                    #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    #         'price_unit': chepest_result,
                                                                    #
                                                                    #     }
                                                                    #
                                                                    # if i.product_id.name not in self.order_line.mapped(
                                                                    #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    #     'product_id').ids:
                                                                    #     po_line.create(vals)

                                                            elif int(
                                                                    promotion_product.discount_max_amount) == 0:
                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                chepest_result = -diskon_percentage


                                                                for i in product_min_price:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                #     vals = {
                                                                #         'order_id': self.id,
                                                                #
                                                                #         'product_id': promotion_product.discount_line_product_id.id,
                                                                #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                #         'price_unit': chepest_result,
                                                                #
                                                                #     }
                                                                #
                                                                # if i.product_id.name not in self.order_line.mapped(
                                                                #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                #     'product_id').ids:
                                                                #     po_line.create(vals)

                                                        elif promotion_product.discount_apply_on == 'on_order':

                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if order_line.price_unit > promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'sale.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage



                                                                    for i in order_line:
                                                                        i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        #     'price_unit': promotion_product.discount_max_amount,
                                                                        #
                                                                        # }
                                                                        #
                                                                        # po_line.create(vals)
                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'sale.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    on_order = -diskon_percentage


                                                                    for i in order_line:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        #     'price_unit': on_order,
                                                                        #
                                                                        # }
                                                                        #
                                                                        # po_line.create(vals)
                                                            elif int(
                                                                    promotion_product.discount_max_amount) == 0:
                                                                po_line = self.env[
                                                                    'sale.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                on_order = -diskon_percentage



                                                                for i in order_line:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    # vals = {
                                                                    #     'order_id': self.id,
                                                                    #
                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    #     'price_unit': on_order,
                                                                    #
                                                                    # }
                                                                    #
                                                                    # po_line.create(vals)

                                                    elif promotion_product.discount_type == 'fixed_amount':

                                                        po_line = self.env['sale.order.line'].sudo()
                                                        order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_fixed_amount})

                                                        # vals = {
                                                        #     'order_id': self.id,
                                                        #     'product_id': order_line.product_id.id,
                                                        #      'description_product': 'fixed amount' + ' ' + ' on product :' + ' ' + promotion_product.name,
                                                        #     'price_unit': promotion_product.discount_fixed_amount,
                                                        #
                                                        # }
                                                        # if promotion_product.name not in self.order_line.mapped(
                                                        #         'description_product'):
                                                        #     po_line.create(vals)

                                                else:
                                                    if promotion_product.discount_type == 'percentage':
                                                        if promotion_product.discount_apply_on == 'specific_products':
                                                            # taxes = order_line.tax_id.name
                                                            # if taxes:
                                                            #     taxes = taxes.rstrip(taxes[-1])

                                                            taxes = 0
                                                            if order_line.tax_id:
                                                                taxes = int(order_line.tax_id.amount)
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            result_ = -diskon_percentage
                                                            po_line = self.env['sale.order.line'].sudo()
                                                            subtotal = order_line.price_subtotal * int(
                                                                taxes) / 100
                                                            result_subt_total = order_line.price_subtotal + subtotal

                                                            for i in promotion_product.discount_specific_product_ids:
                                                                disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                                if disc_product_id:
                                                                    if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                        if int(promotion_product.discount_max_amount) > 0:
                                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                            if order_line.price_unit > promotion_product.discount_max_amount:
                                                                                order_line.write({'discount_amount': promotion_product.discount_max_amount})

                                                                                # vals = {
                                                                                #     'order_id': self.id,
                                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                #     'price_unit': promotion_product.discount_max_amount,
                                                                                #
                                                                                # }
                                                                                # if i.name not in self.order_line.mapped(
                                                                                #         'description_product'):
                                                                                #     po_line.create(vals)

                                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                                order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                                # vals = {
                                                                                #     'order_id': self.id,
                                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                                #     'price_unit': result_,
                                                                                #
                                                                                # }
                                                                                # if i.name not in self.order_line.mapped(
                                                                                #         'description_product'):
                                                                                #     po_line.create(vals)
                                                                        elif int(
                                                                                promotion_product.discount_max_amount) == 0:

                                                                            order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            #     'price_unit': result_,
                                                                            #
                                                                            # }
                                                                            # if i.name not in self.order_line.mapped(
                                                                            #         'description_product'):
                                                                            #     po_line.create(vals)


                                                        elif promotion_product.discount_apply_on == 'cheapest_product':
                                                            product_list_update = self.env['sale.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])
                                                            # min_price = min(
                                                            #     self.order_line.mapped('price_unit'))
                                                            min_price = min(
                                                                product_list_update.mapped('price_unit'))
                                                            po_line = self.env['sale.order.line'].sudo()
                                                            product_min_price = self.order_line.filtered(
                                                                lambda r: r.price_unit == min_price)
                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if product_min_price.price_unit > promotion_product.discount_max_amount:
                                                                    # taxes = order_line.tax_id.name
                                                                    # if taxes:
                                                                    #     taxes = taxes.rstrip(taxes[-1])

                                                                    taxes = 0
                                                                    if order_line.tax_id:
                                                                        taxes = int(order_line.tax_id.amount)

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                    subtotal = diskon_percentage * int(taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                    #     vals = {
                                                                    #         'order_id': self.id,
                                                                    #
                                                                    #         'product_id': promotion_product.discount_line_product_id.id,
                                                                    #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    #         'price_unit': promotion_product.discount_max_amount,
                                                                    #
                                                                    #     }
                                                                    # if i.product_id.name not in self.order_line.mapped(
                                                                    #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    #     'product_id').ids:
                                                                    #     po_line.create(vals)

                                                                elif product_min_price.price_unit < promotion_product.discount_max_amount:
                                                                    # taxes = order_line.tax_id.name
                                                                    # if taxes:
                                                                    #     taxes = taxes.rstrip(taxes[-1])

                                                                    taxes = 0
                                                                    if order_line.tax_id:
                                                                        taxes = int(order_line.tax_id.amount)

                                                                    diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    chepest_result = -diskon_percentage

                                                                    subtotal = diskon_percentage * int(
                                                                        taxes) / 100
                                                                    resultsubtotal = subtotal + product_min_price.price_unit

                                                                    for i in product_min_price:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    #     vals = {
                                                                    #         'order_id': self.id,
                                                                    #
                                                                    #         'product_id': promotion_product.discount_line_product_id.id,
                                                                    #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                    #         'price_unit': chepest_result,
                                                                    #
                                                                    #     }
                                                                    #
                                                                    # if i.product_id.name not in self.order_line.mapped(
                                                                    #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                    #     'product_id').ids:
                                                                    #     po_line.create(vals)

                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                chepest_result = -diskon_percentage
                                                                # taxes = order_line.tax_id.name
                                                                # if taxes:
                                                                #     taxes = taxes.rstrip(taxes[-1])

                                                                taxes = 0
                                                                if order_line.tax_id:
                                                                    taxes = int(order_line.tax_id.amount)
                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                #     vals = {
                                                                #         'order_id': self.id,
                                                                #
                                                                #         'product_id': promotion_product.discount_line_product_id.id,
                                                                #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                #         'price_unit': chepest_result,
                                                                #
                                                                #     }
                                                                #
                                                                # if i.product_id.name not in self.order_line.mapped(
                                                                #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                #     'product_id').ids:
                                                                #     po_line.create(vals)

                                                        elif promotion_product.discount_apply_on == 'on_order':

                                                            if int(promotion_product.discount_max_amount) > 0:
                                                                calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                if order_line.price_unit > promotion_product.discount_max_amount:
                                                                    po_line = self.env['sale.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    on_order = -diskon_percentage



                                                                    for i in order_line:
                                                                        i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        #     'price_unit': promotion_product.discount_max_amount,
                                                                        #
                                                                        # }
                                                                        #
                                                                        # po_line.create(vals)
                                                                elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                    po_line = self.env[
                                                                        'sale.order.line'].sudo()
                                                                    diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                    additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                    # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                    dis_res = order_line.harga_satuan_baru
                                                                    disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                    on_order = -diskon_percentage

                                                                    # subtotal = diskon_percentage * int(
                                                                    #     taxes) / 100
                                                                    # resultsubtotal = subtotal + order_line.price_unit

                                                                    for i in order_line:
                                                                        # i.write({'discount': promotion_product.discount_percentage})
                                                                        i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                        #     'price_unit': on_order,
                                                                        #
                                                                        # }
                                                                        #
                                                                        # po_line.create(vals)
                                                            elif int(promotion_product.discount_max_amount) == 0:
                                                                po_line = self.env[
                                                                    'sale.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                on_order = -diskon_percentage

                                                                # subtotal = diskon_percentage * int(
                                                                #     taxes) / 100
                                                                # resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    # vals = {
                                                                    #     'order_id': self.id,
                                                                    #
                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    #     'price_unit': on_order,
                                                                    #
                                                                    # }
                                                                    #
                                                                    # po_line.create(vals)

                                                    elif promotion_product.discount_type == 'fixed_amount':

                                                        po_line = self.env['sale.order.line'].sudo()
                                                        order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_fixed_amount})
                    else:
                        for product_ids_list in promotion_product.product_ids:
                            for order_line in self.order_line:
                                if product_ids_list.id == order_line.product_id.id and ((promotion_product.rule_min_quantity > 0 and int(order_line.product_uom_qty) >= promotion_product.rule_min_quantity) or (promotion_product.rule_minimum_amount > 0 and order_line.price_subtotal  >= promotion_product.rule_minimum_amount )):
                                    if promotion_product.rule_minimum_amount_tax_inclusion == 'tax_included':
                                        # taxes = order_line.tax_id.name
                                        # if taxes:
                                        #     taxes = taxes.rstrip(taxes[-1])

                                        taxes = 0
                                        if order_line.tax_id:
                                            taxes = int(order_line.tax_id.amount)
                                        result = order_line.price_subtotal * int(taxes) / 100
                                        total = result + order_line.price_subtotal
                                        if total >= promotion_product.rule_minimum_amount:
                                            if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1

                                                if promotion_product.discount_type == 'percentage':
                                                    if promotion_product.discount_apply_on == 'specific_products':
                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                        result_ = -diskon_percentage
                                                        po_line = self.env['sale.order.line'].sudo()
                                                        subtotal = order_line.price_subtotal * int(
                                                            taxes) / 100
                                                        result_subt_total = order_line.price_subtotal + subtotal

                                                        for i in promotion_product.discount_specific_product_ids:
                                                            disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                            if disc_product_id:
                                                                if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                    if int(promotion_product.discount_max_amount) > 0:
                                                                        calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        if order_line.price_unit > promotion_product.discount_max_amount:
                                                                            order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})

                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            #     'price_unit': promotion_product.discount_max_amount,
                                                                            #     'price_subtotal': result_subt_total,
                                                                            # }
                                                                            # if i.name not in self.order_line.mapped(
                                                                            #         'description_product'):
                                                                            #     po_line.create(vals)

                                                                        elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                            order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            #     'price_unit': result_,
                                                                            #     'price_subtotal': result_subt_total,
                                                                            # }
                                                                            # if i.name not in self.order_line.mapped(
                                                                            #         'description_product'):
                                                                            #     po_line.create(vals)
                                                                    elif int(
                                                                            promotion_product.discount_max_amount) == 0:

                                                                        order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                        #     'price_unit': result_,
                                                                        #     'price_subtotal': result_subt_total,
                                                                        # }
                                                                        # if i.name not in self.order_line.mapped(
                                                                        #         'description_product'):
                                                                        #     po_line.create(vals)


                                                    elif promotion_product.discount_apply_on == 'cheapest_product':
                                                        product_list_update = self.env['sale.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])
                                                        # min_price = min(
                                                        #     self.order_line.mapped('price_unit'))
                                                        min_price = min(
                                                            product_list_update.mapped('price_unit'))
                                                        po_line = self.env['sale.order.line'].sudo()
                                                        product_min_price = self.order_line.filtered(
                                                            lambda r: r.price_unit == min_price)
                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                #     vals = {
                                                                #         'order_id': self.id,
                                                                #         'price_subtotal': resultsubtotal,
                                                                #         'product_id': promotion_product.discount_line_product_id.id,
                                                                #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                #         'price_unit': promotion_product.discount_max_amount,
                                                                #
                                                                #     }
                                                                #
                                                                # if i.product_id.name not in self.order_line.mapped(
                                                                #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                #     'product_id').ids:
                                                                #     po_line.create(vals)

                                                            elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                chepest_result = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                #     vals = {
                                                                #         'order_id': self.id,
                                                                #         'price_subtotal': resultsubtotal,
                                                                #         'product_id': promotion_product.discount_line_product_id.id,
                                                                #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                #         'price_unit': chepest_result,
                                                                #
                                                                #     }
                                                                #
                                                                # if i.product_id.name not in self.order_line.mapped(
                                                                #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                #     'product_id').ids:
                                                                #     po_line.create(vals)

                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                            additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                            # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                            dis_res = order_line.harga_satuan_baru
                                                            disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                            chepest_result = -diskon_percentage

                                                            subtotal = diskon_percentage * int(
                                                                taxes) / 100
                                                            resultsubtotal = subtotal + product_min_price.price_unit

                                                            for i in product_min_price:
                                                                # i.write({'discount': promotion_product.discount_percentage})
                                                                i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                            #     vals = {
                                                            #         'order_id': self.id,
                                                            #         'price_subtotal': resultsubtotal,
                                                            #         'product_id': promotion_product.discount_line_product_id.id,
                                                            #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                            #         'price_unit': chepest_result,
                                                            #
                                                            #     }
                                                            #
                                                            # if i.product_id.name not in self.order_line.mapped(
                                                            #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                            #     'product_id').ids:
                                                            #     po_line.create(vals)

                                                    elif promotion_product.discount_apply_on == 'on_order':

                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if order_line.price_unit > promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'sale.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                    # vals = {
                                                                    #     'order_id': self.id,
                                                                    #     'price_subtotal': resultsubtotal,
                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    #     'price_unit': promotion_product.discount_max_amount,
                                                                    #
                                                                    # }
                                                                    #
                                                                    # po_line.create(vals)
                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'sale.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                on_order = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    # vals = {
                                                                    #     'order_id': self.id,
                                                                    #     'price_subtotal': resultsubtotal,
                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    #     'price_unit': on_order,
                                                                    #
                                                                    # }
                                                                    #
                                                                    # po_line.create(vals)
                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            po_line = self.env[
                                                                'sale.order.line'].sudo()
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                            # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                            dis_res = order_line.harga_satuan_baru
                                                            disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                            on_order = -diskon_percentage

                                                            subtotal = diskon_percentage * int(
                                                                taxes) / 100
                                                            resultsubtotal = subtotal + order_line.price_unit

                                                            for i in order_line:
                                                                # i.write({'discount': promotion_product.discount_percentage})
                                                                i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                # vals = {
                                                                #     'order_id': self.id,
                                                                #     'price_subtotal': resultsubtotal,
                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                #     'price_unit': on_order,
                                                                #
                                                                # }
                                                                #
                                                                # po_line.create(vals)

                                                elif promotion_product.discount_type == 'fixed_amount':

                                                    po_line = self.env['sale.order.line'].sudo()
                                                    order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_fixed_amount})

                                                    # vals = {
                                                    #     'order_id': self.id,
                                                    #     'product_id': order_line.product_id.id,
                                                    #      'description_product': 'fixed amount' + ' ' + ' on product :' + ' ' + promotion_product.name,
                                                    #     'price_unit': promotion_product.discount_fixed_amount,
                                                    #
                                                    # }
                                                    # if promotion_product.name not in self.order_line.mapped(
                                                    #         'description_product'):
                                                    #     po_line.create(vals)

                                            else:
                                                if promotion_product.discount_type == 'percentage':
                                                    if promotion_product.discount_apply_on == 'specific_products':
                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                        result_ = -diskon_percentage
                                                        po_line = self.env['sale.order.line'].sudo()
                                                        subtotal = order_line.price_subtotal * int(
                                                            taxes) / 100
                                                        result_subt_total = order_line.price_subtotal + subtotal

                                                        for i in promotion_product.discount_specific_product_ids:
                                                            disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                            if disc_product_id:
                                                                if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                    if int(promotion_product.discount_max_amount) > 0:
                                                                        calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        if order_line.price_unit > promotion_product.discount_max_amount:
                                                                            order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})

                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            #     'price_unit': promotion_product.discount_max_amount,
                                                                            #
                                                                            # }
                                                                            # if i.name not in self.order_line.mapped(
                                                                            #         'description_product'):
                                                                            #     po_line.create(vals)

                                                                        elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                            order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            #     'price_unit': result_,
                                                                            #
                                                                            # }
                                                                            # if i.name not in self.order_line.mapped(
                                                                            #         'description_product'):
                                                                            #     po_line.create(vals)
                                                                    elif int(
                                                                            promotion_product.discount_max_amount) == 0:

                                                                        order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                        #     'price_unit': result_,
                                                                        #
                                                                        # }
                                                                        # if i.name not in self.order_line.mapped(
                                                                        #         'description_product'):
                                                                        #     po_line.create(vals)


                                                    elif promotion_product.discount_apply_on == 'cheapest_product':
                                                        product_list_update = self.env['sale.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])
                                                        # min_price = min(
                                                        #     self.order_line.mapped('price_unit'))
                                                        min_price = min(
                                                            product_list_update.mapped('price_unit'))
                                                        po_line = self.env['sale.order.line'].sudo()
                                                        product_min_price = self.order_line.filtered(
                                                            lambda r: r.price_unit == min_price)
                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                #     vals = {
                                                                #         'order_id': self.id,
                                                                #         'price_subtotal': resultsubtotal,
                                                                #         'product_id': promotion_product.discount_line_product_id.id,
                                                                #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                #         'price_unit': promotion_product.discount_max_amount,
                                                                #
                                                                #     }
                                                                #
                                                                # if i.product_id.name not in self.order_line.mapped(
                                                                #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                #     'product_id').ids:
                                                                #     po_line.create(vals)

                                                            elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                chepest_result = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                #     vals = {
                                                                #         'order_id': self.id,
                                                                #
                                                                #         'product_id': promotion_product.discount_line_product_id.id,
                                                                #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                #         'price_unit': chepest_result,
                                                                #
                                                                #     }
                                                                #
                                                                # if i.product_id.name not in self.order_line.mapped(
                                                                #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                #     'product_id').ids:
                                                                #     po_line.create(vals)

                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                            additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                            # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                            dis_res = order_line.harga_satuan_baru
                                                            disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                            chepest_result = -diskon_percentage

                                                            subtotal = diskon_percentage * int(
                                                                taxes) / 100

                                                            resultsubtotal = subtotal + product_min_price.price_unit

                                                            for i in product_min_price:
                                                                # i.write({'discount': promotion_product.discount_percentage})
                                                                i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                            #     vals = {
                                                            #         'order_id': self.id,
                                                            #
                                                            #         'product_id': promotion_product.discount_line_product_id.id,
                                                            #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                            #         'price_unit': chepest_result,
                                                            #
                                                            #     }
                                                            #
                                                            # if i.product_id.name not in self.order_line.mapped(
                                                            #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                            #     'product_id').ids:
                                                            #     po_line.create(vals)

                                                    elif promotion_product.discount_apply_on == 'on_order':

                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if order_line.price_unit > promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'sale.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                    # vals = {
                                                                    #     'order_id': self.id,
                                                                    #
                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    #     'price_unit': promotion_product.discount_max_amount,
                                                                    #
                                                                    # }
                                                                    #
                                                                    # po_line.create(vals)
                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'sale.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                on_order = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    # vals = {
                                                                    #     'order_id': self.id,
                                                                    #
                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    #     'price_unit': on_order,
                                                                    #
                                                                    # }
                                                                    #
                                                                    # po_line.create(vals)
                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            # print("O on order")
                                                            po_line = self.env[
                                                                'sale.order.line'].sudo()
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                            # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                            dis_res = order_line.harga_satuan_baru
                                                            disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                            on_order = -diskon_percentage

                                                            subtotal = diskon_percentage * int(
                                                                taxes) / 100
                                                            resultsubtotal = subtotal + order_line.price_unit

                                                            for i in order_line:
                                                                # i.write({'discount': promotion_product.discount_percentage})
                                                                i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                # vals = {
                                                                #     'order_id': self.id,
                                                                #
                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                #     'price_unit': on_order,
                                                                #
                                                                # }
                                                                #
                                                                # po_line.create(vals)

                                                elif promotion_product.discount_type == 'fixed_amount':

                                                    po_line = self.env['sale.order.line'].sudo()

                                                    order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_fixed_amount})

                                                    # vals = {
                                                    #     'order_id': self.id,
                                                    #     'product_id': order_line.product_id.id,
                                                    #      'description_product': 'fixed amount' + ' ' + ' on product :' + ' ' + promotion_product.name,
                                                    #     'price_unit': promotion_product.discount_fixed_amount,
                                                    #
                                                    # }
                                                    # if promotion_product.name not in self.order_line.mapped(
                                                    #         'description_product'):
                                                    #     po_line.create(vals)

                                    elif promotion_product.rule_minimum_amount_tax_inclusion == 'tax_excluded':
                                        # print("discount", order_line.price_subtotal)
                                        total = order_line.price_subtotal
                                        if total >= promotion_product.rule_minimum_amount:
                                            if promotion_product.remaining_use_promotion > 0 and promotion_product.maximum_use_number > 0:
                                                promotion_product.remaining_use_promotion = promotion_product.remaining_use_promotion - 1

                                                if promotion_product.discount_type == 'percentage':
                                                    if promotion_product.discount_apply_on == 'specific_products':
                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                        result_ = -diskon_percentage
                                                        po_line = self.env['sale.order.line'].sudo()
                                                        subtotal = order_line.price_subtotal * int(
                                                            taxes) / 100
                                                        result_subt_total = order_line.price_subtotal + subtotal

                                                        for i in promotion_product.discount_specific_product_ids:
                                                            disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                            if disc_product_id:
                                                                if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                    if int(promotion_product.discount_max_amount) > 0:
                                                                        calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        if order_line.price_unit > promotion_product.discount_max_amount:
                                                                            order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})

                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            #     'price_unit': promotion_product.discount_max_amount,
                                                                            #
                                                                            # }
                                                                            # if i.name not in self.order_line.mapped(
                                                                            #         'description_product'):
                                                                            #     po_line.create(vals)

                                                                        elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                            order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            #     'price_unit': result_,
                                                                            #
                                                                            # }
                                                                            # if i.name not in self.order_line.mapped(
                                                                            #         'description_product'):
                                                                            #     po_line.create(vals)
                                                                    elif int(
                                                                            promotion_product.discount_max_amount) == 0:

                                                                        order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                        #     'price_unit': result_,
                                                                        #
                                                                        # }
                                                                        # if i.name not in self.order_line.mapped(
                                                                        #         'description_product'):
                                                                        #     po_line.create(vals)


                                                    elif promotion_product.discount_apply_on == 'cheapest_product':
                                                        product_list_update = self.env['sale.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])
                                                        # min_price = min(
                                                        #     self.order_line.mapped('price_unit'))
                                                        min_price = min(
                                                            product_list_update.mapped('price_unit'))
                                                        min_price = min(
                                                            self.order_line.mapped('price_unit'))
                                                        po_line = self.env['sale.order.line'].sudo()
                                                        product_min_price = self.order_line.filtered(
                                                            lambda r: r.price_unit == min_price)
                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                #     vals = {
                                                                #         'order_id': self.id,
                                                                #
                                                                #         'product_id': promotion_product.discount_line_product_id.id,
                                                                #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                #         'price_unit': promotion_product.discount_max_amount,
                                                                #
                                                                #     }
                                                                #
                                                                # if i.product_id.name not in self.order_line.mapped(
                                                                #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                #     'product_id').ids:
                                                                #     po_line.create(vals)

                                                            elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                chepest_result = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + product_min_price.price_unit

                                                                for i in product_min_price:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                #     vals = {
                                                                #         'order_id': self.id,
                                                                #
                                                                #         'product_id': promotion_product.discount_line_product_id.id,
                                                                #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                #         'price_unit': chepest_result,
                                                                #
                                                                #     }
                                                                #
                                                                # if i.product_id.name not in self.order_line.mapped(
                                                                #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                #     'product_id').ids:
                                                                #     po_line.create(vals)

                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                            additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                            # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                            dis_res = order_line.harga_satuan_baru
                                                            disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                            chepest_result = -diskon_percentage

                                                            subtotal = diskon_percentage * int(
                                                                taxes) / 100
                                                            resultsubtotal = subtotal + product_min_price.price_unit

                                                            for i in product_min_price:
                                                                # i.write({'discount': promotion_product.discount_percentage})
                                                                i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                            #     vals = {
                                                            #         'order_id': self.id,
                                                            #
                                                            #         'product_id': promotion_product.discount_line_product_id.id,
                                                            #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                            #         'price_unit': chepest_result,
                                                            #
                                                            #     }
                                                            #
                                                            # if i.product_id.name not in self.order_line.mapped(
                                                            #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                            #     'product_id').ids:
                                                            #     po_line.create(vals)

                                                    elif promotion_product.discount_apply_on == 'on_order':

                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if order_line.price_unit > promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'sale.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                    # vals = {
                                                                    #     'order_id': self.id,
                                                                    #
                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    #     'price_unit': promotion_product.discount_max_amount,
                                                                    #
                                                                    # }
                                                                    #
                                                                    # po_line.create(vals)
                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'sale.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                on_order = -diskon_percentage

                                                                subtotal = diskon_percentage * int(
                                                                    taxes) / 100
                                                                resultsubtotal = subtotal + order_line.price_unit

                                                                for i in order_line:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    # vals = {
                                                                    #     'order_id': self.id,
                                                                    #
                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    #     'price_unit': on_order,
                                                                    #
                                                                    # }
                                                                    #
                                                                    # po_line.create(vals)
                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            po_line = self.env[
                                                                'sale.order.line'].sudo()
                                                            diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                            # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                            dis_res = order_line.harga_satuan_baru
                                                            disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                            on_order = -diskon_percentage



                                                            for i in order_line:
                                                                # i.write({'discount': promotion_product.discount_percentage})
                                                                i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                # vals = {
                                                                #     'order_id': self.id,
                                                                #
                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                #     'price_unit': on_order,
                                                                #
                                                                # }
                                                                #
                                                                # po_line.create(vals)

                                                elif promotion_product.discount_type == 'fixed_amount':
                                                    i.write({'is_discount': True, 'discount_amount': promotion_product.discount_fixed_amount})

                                                    # po_line = self.env['sale.order.line'].sudo()
                                                    #
                                                    # vals = {
                                                    #     'order_id': self.id,
                                                    #      'product_id': order_line.product_id.id,
                                                    #      'description_product': 'fixed amount' + ' ' + ' on product :' + ' ' + promotion_product.name,
                                                    #     'price_unit': promotion_product.discount_fixed_amount,
                                                    #
                                                    # }
                                                    # if promotion_product.name not in self.order_line.mapped(
                                                    #         'description_product'):
                                                    #     po_line.create(vals)

                                            else:
                                                if promotion_product.discount_type == 'percentage':
                                                    if promotion_product.discount_apply_on == 'specific_products':
                                                        diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                        result_ = -diskon_percentage
                                                        po_line = self.env['sale.order.line'].sudo()
                                                        # taxes = order_line.tax_id.name
                                                        # if taxes:
                                                        #     taxes = taxes.rstrip(taxes[-1])

                                                        taxes = 0
                                                        if order_line.tax_id:
                                                            taxes = int(order_line.tax_id.amount)
                                                        subtotal = order_line.price_subtotal * int(
                                                            taxes) / 100
                                                        result_subt_total = order_line.price_subtotal + subtotal

                                                        for i in promotion_product.discount_specific_product_ids:
                                                            disc_product_id = self.env['product.product'].search([('product_tmpl_id','=',i.id)], limit=1)
                                                            if disc_product_id:
                                                                if disc_product_id.id == product_ids_list.id and disc_product_id.id == order_line.product_id.id:
                                                                    if int(promotion_product.discount_max_amount) > 0:
                                                                        calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                        if order_line.price_unit > promotion_product.discount_max_amount:
                                                                            order_line.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})

                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            #     'price_unit': promotion_product.discount_max_amount,
                                                                            #
                                                                            # }
                                                                            # if i.name not in self.order_line.mapped(
                                                                            #         'description_product'):
                                                                            #     po_line.create(vals)

                                                                        elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                            order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                            # vals = {
                                                                            #     'order_id': self.id,
                                                                            #     'product_id': promotion_product.discount_line_product_id.id,
                                                                            #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                            #     'price_unit': result_,
                                                                            #
                                                                            # }
                                                                            # if i.name not in self.order_line.mapped(
                                                                            #         'description_product'):
                                                                            #     po_line.create(vals)
                                                                    elif int(
                                                                            promotion_product.discount_max_amount) == 0:

                                                                        order_line.write({'is_discount': True, 'discount': promotion_product.discount_percentage})
                                                                        # vals = {
                                                                        #     'order_id': self.id,
                                                                        #     'product_id': promotion_product.discount_line_product_id.id,
                                                                        #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                        #     'price_unit': result_,
                                                                        #
                                                                        # }
                                                                        # if i.name not in self.order_line.mapped(
                                                                        #         'description_product'):
                                                                        #     po_line.create(vals)


                                                    elif promotion_product.discount_apply_on == 'cheapest_product':
                                                        product_list_update = self.env['sale.order.line'].search([('product_id','in',list(set(product_ids_update))),('order_id','=',self.id)])
                                                        # min_price = min(
                                                        #     self.order_line.mapped('price_unit'))
                                                        min_price = min(
                                                            product_list_update.mapped('price_unit'))
                                                        po_line = self.env['sale.order.line'].sudo()
                                                        product_min_price = self.order_line.filtered(
                                                            lambda r: r.price_unit == min_price)
                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if product_min_price.price_unit > promotion_product.discount_max_amount:

                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100


                                                                for i in product_min_price:
                                                                    i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                #     vals = {
                                                                #         'order_id': self.id,
                                                                #
                                                                #         'product_id': promotion_product.discount_line_product_id.id,
                                                                #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                #         'price_unit': promotion_product.discount_max_amount,
                                                                #
                                                                #     }
                                                                #
                                                                # if i.product_id.name not in self.order_line.mapped(
                                                                #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                #     'product_id').ids:
                                                                #     po_line.create(vals)

                                                            elif product_min_price.price_unit < promotion_product.discount_max_amount:

                                                                diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                chepest_result = -diskon_percentage
                                                                taxes = order_line.tax_id.name


                                                                for i in product_min_price:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                #     vals = {
                                                                #         'order_id': self.id,
                                                                #
                                                                #         'product_id': promotion_product.discount_line_product_id.id,
                                                                #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                                #         'price_unit': chepest_result,
                                                                #
                                                                #     }
                                                                #
                                                                # if i.product_id.name not in self.order_line.mapped(
                                                                #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                                #     'product_id').ids:
                                                                #     po_line.create(vals)

                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            diskon_percentage = promotion_product.discount_percentage * product_min_price.price_unit / 100
                                                            additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                            # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                            dis_res = order_line.harga_satuan_baru
                                                            disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                            chepest_result = -diskon_percentage


                                                            for i in product_min_price:
                                                                # i.write({'discount': promotion_product.discount_percentage})
                                                                i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                            #     vals = {
                                                            #         'order_id': self.id,
                                                            #
                                                            #         'product_id': promotion_product.discount_line_product_id.id,
                                                            #         'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.name,
                                                            #         'price_unit': chepest_result,
                                                            #
                                                            #     }
                                                            #
                                                            # if i.product_id.name not in self.order_line.mapped(
                                                            #         'description_product') and promotion_product.discount_line_product_id not in self.order_line.mapped(
                                                            #     'product_id').ids:
                                                            #     po_line.create(vals)

                                                    elif promotion_product.discount_apply_on == 'on_order':

                                                        if int(promotion_product.discount_max_amount) > 0:
                                                            calculation = promotion_product.discount_percentage * order_line.price_unit / 100
                                                            if order_line.price_unit > promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'sale.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                on_order = -diskon_percentage


                                                                for i in order_line:
                                                                    i.write({'is_discount': True, 'discount_amount': promotion_product.discount_max_amount})
                                                                    # vals = {
                                                                    #     'order_id': self.id,
                                                                    #
                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    #     'price_unit': promotion_product.discount_max_amount,
                                                                    #
                                                                    # }
                                                                    #
                                                                    # po_line.create(vals)
                                                            elif order_line.price_unit < promotion_product.discount_max_amount:
                                                                po_line = self.env[
                                                                    'sale.order.line'].sudo()
                                                                diskon_percentage = promotion_product.discount_percentage * order_line.price_unit / 100
                                                                additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                                # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                                dis_res = order_line.harga_satuan_baru
                                                                disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                                on_order = -diskon_percentage


                                                                for i in order_line:
                                                                    # i.write({'discount': promotion_product.discount_percentage})
                                                                    i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                    # vals = {
                                                                    #     'order_id': self.id,
                                                                    #     'price_subtotal': resultsubtotal,
                                                                    #     'product_id': promotion_product.discount_line_product_id.id,
                                                                    #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                    #     'price_unit': on_order,
                                                                    #
                                                                    # }
                                                                    #
                                                                    # po_line.create(vals)
                                                        elif int(
                                                                promotion_product.discount_max_amount) == 0:
                                                            po_line = self.env[
                                                                'sale.order.line'].sudo()
                                                            diskon_percentage = promotion_product.discount_percentage * (order_line.price_subtotal/order_line.product_uom_qty) / 100
                                                            additional_margin = order_line.price_unit * order_line.additional_margin / 100
                                                            # dis_res = order_line.price_unit + order_line.product_margin_amount + additional_margin
                                                            dis_res = order_line.harga_satuan_baru
                                                            disc_amount = (promotion_product.discount_percentage/100)*dis_res
                                                            on_order = -diskon_percentage
                                                            # taxes = order_line.tax_id.name
                                                            # if taxes:
                                                            #     taxes = taxes.rstrip(taxes[-1])

                                                            taxes = 0
                                                            if order_line.tax_id:
                                                                taxes = int(order_line.tax_id.amount)
                                                            subtotal = diskon_percentage * int(
                                                                taxes) / 100
                                                            resultsubtotal = subtotal + order_line.price_unit

                                                            for i in order_line:
                                                                # i.write({'discount': promotion_product.discount_percentage})
                                                                i.write({'is_discount': True, 'discount_amount': disc_amount})
                                                                # vals = {
                                                                #     'order_id': self.id,
                                                                #     'price_subtotal': resultsubtotal,
                                                                #     'product_id': promotion_product.discount_line_product_id.id,
                                                                #     'description_product': promotion_product.discount_line_product_id.name + ' ' + ' Main product :' + ' ' + i.product_id.name,
                                                                #     'price_unit': on_order,
                                                                #
                                                                # }
                                                                #
                                                                # po_line.create(vals)

                                                elif promotion_product.discount_type == 'fixed_amount':

                                                    po_line = self.env['sale.order.line'].sudo()

                                                    for i in order_line:
                                                        i.write({'is_discount': True, 'discount_amount': promotion_product.discount_fixed_amount})

        self.order_line = product
        self.add_promotion = True

class action_promotion_so(models.Model):
    _inherit = 'sale.order.line'

    is_promotion = fields.Boolean(string="Is Promotion", default=False)
    is_discount = fields.Boolean(string="Is Promotion", default=False)
    is_promo = fields.Boolean(string="Is Promotion", default=False)


