odoo.define('ob_pos_multi_uom.TicketScreen', function (require) {
    'use strict';

    const Registries = require('point_of_sale.Registries');
    const TicketScreen = require('point_of_sale.TicketScreen');

    const TicketScreenUom = TicketScreen =>
        class extends TicketScreen {
        /**
         * Returns the corresponding toRefundDetail of the given orderline.
         * SIDE-EFFECT: Automatically creates a toRefundDetail object for
         * the given orderline if it doesn't exist and returns it.
         * @param {models.Orderline} orderline
         * @returns
         */
         _getToRefundDetail(orderline) {
            if (orderline.id in this.env.pos.toRefundLines) {
                return this.env.pos.toRefundLines[orderline.id];
            } else {
                const customer = orderline.order.get_client();
                const orderPartnerId = customer ? customer.id : false;
                const newToRefundDetail = {
                    qty: 0,
                    orderline: {
                        id: orderline.id,
                        productId: orderline.product.id,
                        price: orderline.price,
                        qty: orderline.quantity,
                        refundedQty: orderline.refunded_qty,
                        orderUid: orderline.order.uid,
                        orderBackendId: orderline.order.backendId,
                        orderPartnerId,
                        tax_ids: orderline.get_taxes().map(tax => tax.id),
                        discount: orderline.discount,
                        uom_id: orderline.uom_id,
                    },
                    destinationOrderUid: false,
                };
                this.env.pos.toRefundLines[orderline.id] = newToRefundDetail;
                return newToRefundDetail;
            }
        }
        /**
         * Prepares the options to add a refund orderline.
         *
         * @param {Object} toRefundDetail
         * @returns {Object}
         */
         _prepareRefundOrderlineOptions(toRefundDetail) {
            const { qty, orderline } = toRefundDetail;
            return {
                quantity: -qty,
                price: orderline.price,
                extras: { price_manually_set: true },
                merge: false,
                refunded_orderline_id: orderline.id,
                tax_ids: orderline.tax_ids,
                discount: orderline.discount,
                uom_id: orderline.uom_id,
            }
        }

    };

    Registries.Component.extend(TicketScreen, TicketScreenUom);
    return TicketScreen;

});
