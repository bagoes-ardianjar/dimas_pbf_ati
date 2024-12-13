odoo.define('ob_pos_payment_ref.models', function (require) {
    "use strict";
    var models = require('point_of_sale.models');
    models.load_fields("pos.payment.method", ['enable_payment_ref']);

});