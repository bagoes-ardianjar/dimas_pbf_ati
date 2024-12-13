odoo.define('ob_pos_payment_ref.PaymentScreen', function(require) {
    'use strict';

    const models = require('point_of_sale.models');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const {useListener} = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    var core = require('web.core');
    var _t = core._t;
    const {Gui} = require('point_of_sale.Gui');

    const PaymentPaymentRef = (PaymentScreen) => {
        class PaymentPaymentRef extends PaymentScreen {
            constructor() {
                super(...arguments);
                useListener('onclick-payment_ref', this.onClick);
            }
            async _isOrderValid(isForceValidate) {
            var result = super._isOrderValid(isForceValidate);
            const splitPayments = this.paymentLines.filter(payment => payment.payment_method.split_transactions)
            if (splitPayments.length && !splitPayments[0].payment_ref) {
                const { konfirm } = await this.showPopup('ConfirmPopup', {
                    title: this.env._t('Payment Reference'),
                    body: _.str.sprintf(this.env._t('Payment Reference is required for DEBIT CARD')),
                });
                if (konfirm) {
                    this.selectClient();
                }
                return false;
                }
            return result;
            }

            async onClick() {
            const {cid} = event.detail;
            const line = this.paymentLines.find((line) => line.cid === cid);
            line.payment_ref = $(".paymentline.selected").find(".payment_ref").val();
            Gui.showPopup('PaymentRefPopup',{
                    'title': _t('Enter Payment Reference'),
                    'payment_line': line
                    });
            }
            }
            return PaymentPaymentRef;
    };
    Registries.Component.extend(PaymentScreen, PaymentPaymentRef);

    var _super_paymentline = models.Paymentline.prototype;
    models.Paymentline = models.Paymentline.extend({
        initialize: function(attributes, options) {
            _super_paymentline.initialize.apply(this, arguments);
            this.payment_ref = "";
        },
        export_as_JSON: function() {
            var data = _super_paymentline.export_as_JSON.apply(this, arguments);
            data.payment_ref = this.payment_ref;
            return data;
        }
    });
});