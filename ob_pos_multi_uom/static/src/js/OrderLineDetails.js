odoo.define('ob_pos_multi_uom.OrderLineDetails', function (require) {
    'use strict';

    const Registries = require('point_of_sale.Registries');
    const OrderLineDetails = require('point_of_sale.OrderlineDetails');
    const { format } = require('web.field_utils');
    const { round_precision: round_pr } = require('web.utils');

    const OrderLineDetailsUom = OrderLineDetails =>
        class extends OrderLineDetails {

            get line() {
                const line = this.props.line;
                const formatQty = (line) => {
                    const quantity = line.get_quantity();
                    const unit = line.get_unit();
                    const decimals = this.env.pos.dp['Product Unit of Measure'];
                    const rounding = Math.max(unit.rounding, Math.pow(10, -decimals));
                    const roundedQuantity = round_pr(quantity, rounding);
                    return format.float(roundedQuantity, { digits: [69, decimals] });
                };
                return {
                    productName: line.get_full_product_name(),
                    totalPrice: line.get_price_with_tax(),
                    quantity: formatQty(line),
                    unit: line.get_custom_unit().name,
                    unitPrice: line.get_unit_price(),
                };
            }

    };

    Registries.Component.extend(OrderLineDetails, OrderLineDetailsUom);
    return OrderLineDetails;

});
