odoo.define('bi_pos_product_list_view.product_list', function(require) {
	'use strict';

	const PosComponent = require('point_of_sale.PosComponent');
	const Registries = require('point_of_sale.Registries');

	class ProductListviews extends PosComponent {

		get imageUrl() {
			const product = this.props.product;
			return `/web/image?model=product.product&field=image_128&id=${product.id}&write_date=${product.write_date}&unique=1`;
		}
		get pricelist() {
			const current_order = this.env.pos.get_order();
			if (current_order) {
				return current_order.pricelist;
			}
			return this.env.pos.default_pricelist;
		}

		get price() {
			const formattedUnitPrice = this.env.pos.format_currency(
				this.props.product.get_price(this.pricelist, 1),
				'Product Price'
			);
			if (this.props.product.to_weight) {
				return `${formattedUnitPrice}/${
					this.env.pos.units_by_id[this.props.product.uom_id[0]].name
				}`;
			} else {
				return formattedUnitPrice;
			}
		}
	}
	ProductListviews.template = 'ProductListviews';
	Registries.Component.add(ProductListviews);
	return ProductListviews;
});
