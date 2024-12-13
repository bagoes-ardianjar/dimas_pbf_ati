odoo.define('bi_pos_product_list_view.pos_product_list_view', function(require) {
"use strict";


	var core = require('web.core');
	var QWeb = core.qweb;
	const { useListener } = require('web.custom_hooks');
	var ProductsWidget = require('point_of_sale.ProductsWidget');
	const Registries = require('point_of_sale.Registries');
	const PosComponent = require('point_of_sale.PosComponent');
	var model = require('point_of_sale.models');
	var flag = false;

	model.load_fields("product.product",['qty_available','virtual_available','default_code','list_price','name','uom_id','type'],);



	const ProductListView = (ProductsWidget) =>
		class extends ProductsWidget {
			constructor() {
				super(...arguments);
				
				useListener('listview', this.Changeview);
			}

			get productsToDisplay() {
				this.Changeview()
				if (this.searchWord !== '') {
					return this.env.pos.db.search_product_in_category(
						this.selectedCategoryId,
						this.searchWord
					);
				} else {
				    var product =this.env.pos.db.get_product_by_category(this.selectedCategoryId);
				    if(flag == true){
				        $('.product-list').hide()
				    }
					return product;
				}
			}
			Changeview(){
				var self = this;

				$('.code').click(function(){
					var table, i, x, y,dir,switchcount=0;;
					table = document.getElementById("id01");
					var switching = true;
					dir = "asc";
					while (switching){
						switching = false;
						var rows = table.rows;
						for (i = 1; i < (rows.length - 1); i++){
							var Switch = false;
							x = rows[i].getElementsByClassName("product_code")[0];
							y = rows[i + 1].getElementsByClassName("product_code")[0];
							if(dir== "asc"){
								if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()){

									Switch = true;
									break;
								}
							}
							else if (dir == "desc") {
								if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {
									Switch = true;
									break;
								}
							}
						}
						if (Switch) {
							rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
							switching = true;
							switchcount ++;
						} else {
							if (switchcount == 0 && dir == "asc") {
								dir = "desc";
								switching = true;
							}
						}
					}
				});

				$('.name').click(function(){
					var table, i, x, y,dir,switchcount=0;;
					table = document.getElementById("id01");
					var switching = true;
					dir = "asc";
					while (switching){
						switching = false;
						var rows = table.rows;
						for (i = 1; i < (rows.length - 1); i++){
							var Switch = false;
							x = rows[i].getElementsByClassName("product_name")[0];
							y = rows[i + 1].getElementsByClassName("product_name")[0];
							if(dir== "asc"){
								if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()){
									Switch = true;
									break;
								}
							}
							else if (dir == "desc") {
								if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {
									Switch = true;
									break;
								}
							}
						}
						if (Switch) {
							rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
							switching = true;
							switchcount ++;
						} else {
							if (switchcount == 0 && dir == "asc") {
								dir = "desc";
								switching = true;
							}
						}
					}
				});

				$('.type').click(function(){
					var table, i, x, y,dir,switchcount=0;;
					table = document.getElementById("id01");
					var switching = true;
					dir = "asc";
					while (switching){
						switching = false;
						var rows = table.rows;
						for (i = 1; i < (rows.length - 1); i++){
							var Switch = false;
							x = rows[i].getElementsByClassName("product_type")[0];
							y = rows[i + 1].getElementsByClassName("product_type")[0];
							if(dir== "asc"){
								if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()){
									Switch = true;
									break;
								}
							}
							else if (dir == "desc") {
								if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {
									Switch = true;
									break;
								}
							}
						}
						if (Switch) {
							rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
							switching = true;
							switchcount ++;
						} else {
							if (switchcount == 0 && dir == "asc") {
								dir = "desc";
								switching = true;
							}
						}
					}
				});				

				$('.uom').click(function(){
					var table, i, x, y,dir,switchcount=0;;
					table = document.getElementById("id01");
					var switching = true;
					dir = "asc";
					while (switching){
						switching = false;
						var rows = table.rows;
						for (i = 1; i < (rows.length - 1); i++){
							var Switch = false;
							x = rows[i].getElementsByClassName("product_uom")[0];
							y = rows[i + 1].getElementsByClassName("product_uom")[0];
							if(dir== "asc"){
								if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()){
									Switch = true;
									break;
								}
							}
							else if (dir == "desc") {
								if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {

									Switch = true;
									break;
								}
							}
						}
						if (Switch) {
							rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
							switching = true;
							switchcount ++;
						} else {
							if (switchcount == 0 && dir == "asc") {
								dir = "desc";
								switching = true;
							}
						}
					}
				});

				$('.price').click(function(){
					var table, i, x, y,dir,switchcount=0;
					table = document.getElementById("id01");
					var switching = true;
					dir = "asc";
					while (switching){
						switching = false;
						var rows = table.rows;
						for (i = 1; i < (rows.length - 1); i++){
							var Switch = false;
							x = rows[i].getElementsByClassName("product_price")[0];
							y = rows[i + 1].getElementsByClassName("product_price")[0];
							if(dir== "asc"){

								if (parseFloat(x.innerHTML.split(" ").join(",").split("/").join(",").split(",")[1]) > parseFloat(y.innerHTML.split(" ").join(",").split("/").join(",").split(",")[1])){
									Switch = true;
									break;
								}
							}
							else if (dir == "desc") {
								if (parseFloat(x.innerHTML.split(" ").join(",").split("/").join(",").split(",")[1]) < parseFloat(y.innerHTML.split(" ").join(",").split("/").join(",").split(",")[1])) {
									Switch = true;
									break;
								}
							}
						}
						if (Switch) {
							rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
							switching = true;
							switchcount ++;
						} else {
							if (switchcount == 0 && dir == "asc") {
								dir = "desc";
								switching = true;
							}
						}
					}

				});

				$('.qty').click(function(){
					var table, i, x, y ,dir,switchcount=0;
					table = document.getElementById("id01");
					var switching = true;
					dir = "asc";
					while (switching){
						switching = false;
						var rows = table.rows;
						for (i = 1; i < (rows.length - 1); i++){
							var Switch = false;
							x = rows[i].getElementsByClassName("on_hand_qty")[0];
							y = rows[i + 1].getElementsByClassName("on_hand_qty")[0];
							if(dir== "asc"){
								if (parseInt(x.innerHTML) > parseInt(y.innerHTML)){

									Switch = true;
									break;
								}
							}
							else if (dir == "desc") {
								if (parseInt(x.innerHTML) < parseInt(y.innerHTML)) {

									Switch = true;
									break;
								}
							}
						}
						if (Switch) {
							rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
							switching = true;
							switchcount ++;
						} else {
							if (switchcount == 0 && dir == "asc") {
								dir = "desc";
								switching = true;
							}
						}
					}
				});

				$('.fqty').click(function(){
					var table, i, x, y ,dir,switchcount=0;
					table = document.getElementById("id01");
					var switching = true;
					dir = "asc";
					while (switching){
						switching = false;
						var rows = table.rows;
						for (i = 1; i < (rows.length - 1); i++){
							var Switch = false;
							x = rows[i].getElementsByClassName("forecast_qty")[0];
							y = rows[i + 1].getElementsByClassName("forecast_qty")[0];
							if(dir== "asc"){
								if (parseInt(x.innerHTML) > parseInt(y.innerHTML)){

									Switch = true;
									break;
								}
							}
							else if (dir == "desc") {
								if (parseInt(x.innerHTML) < parseInt(y.innerHTML)) {

									Switch = true;
									break;
								}
							}
						}
						if (Switch) {
							rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
							switching = true;
							switchcount ++;
						} else {
							if (switchcount == 0 && dir == "asc") {
								dir = "desc";
								switching = true;
							}
						}
					}
				});

				if(this.env.pos.config.default_product_view === 'list' && this.env.pos.config.enable_list_view){
					flag=true;
					$('.product-list').hide()
					$('.product-list-container-view').show()

				}
			    if(flag == false){
                    $('.product-list-container-view').hide();

                }
				$('.js-category-list').click(function(){
				    flag = true;
					$('.product-list-container-view').show()
					$('.product-list').hide()
				});
				$('.js-category-switch').click(function(){
				    flag = false;
					$('.product-list').show()
					$('.product-list-container-view').hide()
				});

				

			}
		}
	Registries.Component.extend(ProductsWidget, ProductListView);
	return ProductsWidget;
});

