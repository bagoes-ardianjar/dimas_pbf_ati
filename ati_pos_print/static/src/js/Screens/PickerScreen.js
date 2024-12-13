odoo.define('ati_pos_print.PickerScreen', function (require) {
    'use strict';

    const ReceiptScreen = require('point_of_sale.ReceiptScreen');
    const Registries = require('point_of_sale.Registries');

    const PickerScreen = (ReceiptScreen) => {
        class PickerScreen extends ReceiptScreen {
            confirm() {
                this.props.resolve({ confirmed: true, payload: null });
                this.trigger('close-temp-screen');
            }
            whenClosing() {
                this.confirm();
            }
            /**
             * @override
             */
            async printReceipt() {
                await super.printReceipt();
                this.currentOrder._printed = false;
            }
        }
        PickerScreen.template = 'PickerScreen';
        return PickerScreen;
    };

    Registries.Component.addByExtending(PickerScreen, ReceiptScreen);

    return PickerScreen;
});
