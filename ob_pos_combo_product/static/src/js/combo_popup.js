odoo.define('ob_pos_combo_product.combo_popup', function(require) {
    'use strict';

    const Popup = require('point_of_sale.ConfirmPopup');
    const Registries = require('point_of_sale.Registries');

    class ComboPopup extends Popup {
        constructor() {
            super(...arguments);
        }
        confirm() {
            this.props.resolve({
                confirmed: true,
                payload: { props: this.props},
            });
            this.trigger('close-popup');
        }
        get productImageUrl () {
            const product = this.product;
            return `/web/image?model=product.product&field=image_128&id=${product.id}&write_date=${product.write_date}&unique=1`;
        }
        choose_products(e){
            var self = this;
            this.selected = [];
            var $target = $(e.currentTarget);
            var combo = $target.data('combo-id');
            var category = $target.data('category-id');
            var product = $target.data('product-id');
            _.each(this.props.optional, function (category_option) {
                if (category_option['id'] === combo && category_option['category'] === category){
                    var selection_count = 0;
                    _.each(category_option.combo_products, function (combo_product) {
                        if (combo_product.selected){
                            selection_count += 1;
                        }
                    });
                    _.each(category_option.combo_products, function (combo_product) {
                        if(combo_product['id'] === product){
                            if (combo_product['selected']){
                                combo_product['selected'] = false;
                                $target.find('.combo-select').hide();
                                var index = self.selected.indexOf(combo_product);
                                if (index > -1) {
                                   self.selected.splice(index, 1);
                                }
                            }
                            else if (selection_count < category_option.limit){
                                combo_product['selected'] = true;
                                $target.find('.combo-select').text("Selected").show('fast');
                                self.selected.push(combo_product);
                            }
                            else{
                                alert("Already selected enough options for this category");
                            }
                        }
                    });
                }
            });
        }
        go_back_screen() {
            this.showScreen('ProductScreen');
            this.trigger('close-popup');
        }
        click_on_bag_product(event) {
            var self = this;
            var bag_id = parseInt(event.currentTarget.dataset['productId'])
            self.env.pos.get_order().add_product(self.env.pos.db.product_by_id[bag_id]);
            self.trigger('close-popup');
        }
    };
    ComboPopup.template = 'ComboPopup';
    Registries.Component.add(ComboPopup);
    return ComboPopup;
});
