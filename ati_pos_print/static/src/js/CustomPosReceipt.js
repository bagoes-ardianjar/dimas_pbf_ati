odoo.define('ati_pos_print.CustomPosReceipt', function(require) {
    "use strict";

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');

    class PickerReceiptButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click', this.onClick);
        }
        async onClick() {
            const order = this.env.pos.get_order();
            console.log("Ini order : ", order)
            if (order.get_orderlines().length > 0) {
                this.trigger('close-popup');
                await this.showTempScreen('PickerScreen');
            } else {
                await this.showPopup('ErrorPopup', {
                    title: this.env._t('Nothing to Print'),
                    body: this.env._t('There are no order lines'),
                });
            }
        }
    }
    PickerReceiptButton.template = 'PickerReceiptButton';

    ProductScreen.addControlButton({
        component: PickerReceiptButton,
        condition: function() {
            return true;
        },
    });

    Registries.Component.add(PickerReceiptButton);

    return PickerReceiptButton;

});
