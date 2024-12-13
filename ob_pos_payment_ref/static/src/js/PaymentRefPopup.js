odoo.define('point_of_sale.PaymentRefPopup', function(require) {
    'use strict';

    const { useState } = owl.hooks;
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');

    class PaymentRefPopup extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
        }
        async confirm() {
            var payment_ref = $('#pos_payment_ref').val()
            if(payment_ref.length){
                this.props.payment_line.payment_ref = payment_ref
                this.trigger('close-popup');
            }
        }
    }
    PaymentRefPopup.template = 'PaymentRefPopup';
    PaymentRefPopup.defaultProps = {
        confirmText: 'Ok',
        cancelText: 'Cancel',
        title: 'Payment Reference',
        body: '',
    };

    Registries.Component.add(PaymentRefPopup);

    return PaymentRefPopup;
});
