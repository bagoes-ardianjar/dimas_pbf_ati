odoo.define('tis_pos_dynamic_combo.ComboProduct', function (require) {
    'use strict';

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require('web.custom_hooks');
    const { _t } = require('web.core');
    const { parse } = require('web.field_utils');
    const NumberBuffer = require('point_of_sale.NumberBuffer');

        const ComProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            async _clickProduct(event) {
                 if (!this.currentOrder) {
                this.env.pos.add_new_order();
            }
            const product = event.detail;
            const options = await this._getAddProductOptions(product);
             if(product.combo_pack ==1){
                     const {
                confirmed,
                payload: inputDoc
              } = await this.showPopup('ComboProductPopup', {
              confirmText: 'Ok',
              cancelText: 'Cancel',
              title: '',
              document: '',
              body: '',
              startingValue: '',
              product:product,
              });

               }
            else{


            // Do not add product if options is undefined.
            if (!options) return;
            // Add the product after having the extra information.
            this.currentOrder.add_product(product, options);
            NumberBuffer.reset();


            }
            }

          };
         Registries.Component.extend(ProductScreen, ComProductScreen);
         return ProductScreen;
});
