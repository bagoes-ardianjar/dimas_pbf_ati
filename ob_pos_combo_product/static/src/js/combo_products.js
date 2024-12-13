odoo.define('ob_pos_combo_product.combo_products', function (require) {
"use strict";

    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');

    var models = require('point_of_sale.models');

    models.load_models({
        model:  'combo.product',
        fields: [],
        loaded: function(self, combo_list){
            self.combo_list = combo_list;
            _.each(combo_list, function(item){
                self.combo_item_id[item.id] = item;
            });
        },
    });

    models.load_fields("product.product", ["is_combo", "combo_items"]);

    var _super_pos = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function() {
            var self = this;
            _super_pos.initialize.apply(this, arguments);
            this.combo_item_id = {};
        },
        enable_combo: function () {
            var self = this;
            $('.product-list').find('.combo-tag').each(function () {
                var $product = $(this).parents('.product');
                var id = parseInt($product.attr('data-product-id'));
                var product = self.db.get_product_by_id(id);
                if (! product.is_combo){
                    $(this).hide();
                }
                else{
                    $(this).text("Combo Product").show('fast');
                }
            });
        },
    });


    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function(attr, options) {
            _super_orderline.initialize.call(this,attr,options);
            this.combo_items = this.combo_items || [];
        },
        init_from_JSON: function(json) {
            _super_orderline.init_from_JSON.apply(this,arguments);
            this.combo_items = json.combo_items || [];
        },
        export_as_JSON: function () {
            var json = _super_orderline.export_as_JSON.call(this);
            json.combo_items = this.combo_items || [];
            return json;
        },
        export_for_printing: function () {
            var result = _super_orderline.export_for_printing.apply(this, arguments);
            var combo_items = this.combo_items;
            if (combo_items) {
                result.combo_items = combo_items
                }
                return result;
        },
        can_be_merged_with: function(orderline) {
            if (orderline.product.is_combo) {
                return false;
            } else {
                return _super_orderline.can_be_merged_with.apply(this,arguments);
            }
        },
        get_combo_items: function(combo_product){
            var self = this;
            var required = [];
            var optional = [];
            var combo_selection = false;
            _.each(combo_product.combo_items, function(item){
                var combo_item = self.pos.combo_item_id[item];
                var combo_products = [];
                _.each(combo_item.products, function(product_id){
                    var product = self.pos.db.product_by_id[product_id];
                    combo_products.push({
                        'id': product['id'],
                        'name':product['display_name'],
                        'selected': false
                    })
                });
                var combo_item_data = {
                    'id': combo_item.id,
                    'category': combo_item.category[0],
                    'name':combo_item.category[1],
                    'limit': combo_item.item_count,
                    'combo_products': combo_products
                }
                if(!combo_item.is_required){
                    combo_selection = true;
                    optional.push(combo_item_data);
                }
                else{
                    required.push(combo_item_data);
                }
            });
            return {
                'required': required,
                'optional': optional,
                'combo_selection': combo_selection
            };
        }
    });

        var _super_pos_order = models.Order.prototype;
        models.Order = models.Order.extend({

            add_product: function(product, options){
                _super_pos_order.add_product.apply(this, arguments);
                var line = this.get_selected_orderline();
                if(options.combo_items !== undefined){
                        line.combo_items = options.combo_items;
                }
            }

    });

    const ComboProductWidget = (ProductScreen) =>
            class extends ProductScreen {
                get_combo_items(combo_product) {
                    var self = this.env;
                    var required = [];
                    var optional = [];
                    var combo_selection = false;
                    _.each(combo_product.combo_items, function(item){
                        var combo_item = self.pos.combo_item_id[item];
                        var combo_products = [];
                        _.each(combo_item.products, function(product_id){
                            var product = self.pos.db.product_by_id[product_id];
                            combo_products.push({
                                'id': product['id'],
                                'name':product['display_name'],
                                'selected': false
                            })
                        });
                        var combo_item_data = {
                            'id': combo_item.id,
                            'category': combo_item.category[0],
                            'name':combo_item.category[1],
                            'limit': combo_item.item_count,
                            'combo_products': combo_products
                        }
                        if(!combo_item.is_required){
                            combo_selection = true;
                            optional.push(combo_item_data);
                        }
                        else{
                            required.push(combo_item_data);
                        }
                    });
                    return {
                        'required': required,
                        'optional': optional,
                        'combo_selection': combo_selection
                    };
                }
                async _clickProduct(event) {
                    let self = this;
                    const product = event.detail;
                    self.selected = [];
                    var result = self.get_combo_items(product);
                    if (product.is_combo) {
                       const { confirmed, payload } = await self.showPopup('ComboPopup', {
                       'product_name': product.display_name,
                       'selected': self.selected,
                       'required': result['required'],
                       'optional': result['optional'],
                       });
                       if (confirmed) {
                            var execute = true;
                            var selected_line = product;
                            _.each(payload.props.required, function (category_option) {
                                payload.props.selected.push(...category_option.combo_products);
                            });
                            _.each(payload.props.optional, function (category_option) {
                                payload.props.selected.push(...category_option.combo_products.filter(combo_products => combo_products.selected === true));
                            });
                            _.each(payload.props.optional, function (category_option) {
                                if (execute){
                                    var selection_count = 0;
                                    _.each(category_option.combo_products, function (combo_product) {
                                        if (combo_product.selected){
                                            selection_count += 1;
                                        }
                                    });
                                    if (category_option.limit != selection_count){
                                        alert("Please choose your optional products");
                                        execute = false;
                                    }
                                }
                            });
                            if (! execute){
                                return false;
                            }
                            this.currentOrder.add_product(product, {
                                lst_price: product.lst_price,
                                quantity: 1,
                                combo_items: payload.props.selected,
                            });
                            return;
                    } else {
                        // We don't proceed on adding product.
                        return;
                    }

                    }
                    super._clickProduct(event);
                }
            };

    Registries.Component.extend(ProductScreen, ComboProductWidget);

    return ProductScreen;

});
