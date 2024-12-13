odoo.define('point_of_sale.ProductLists', function(require) {
    'use strict';

    const { useState, useRef } = owl.hooks;
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    var models = require('point_of_sale.models');
    var added_products=[];
    var flag=0;
    var update_qty_of_products=[];
    var utils = require('web.utils');

    // formerly TextInputPopupWidget
    class ProductLists extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
           this.state = useState({ inputValue: this.props.startingValue })
           var all_products=this.env.pos.db.product_by_id;

           var all_products_category=this.env.pos.db.product_by_category_id[0];
           var all_pos_products=[];
           for(var i=0;i<all_products_category.length;i++){
                   all_pos_products.push(all_products[all_products_category[i]]);
           }
          this.all_products_pos=all_pos_products;
          this.already_selected_combo=this.props.selected_combo;
          this.already_product_inside_combo=this.props.product_inside_combo;
          this.qty_updated_dict=this.props.qty_dict;
          this.total_charge = this.props.total_charge_added;
          this.additional_charge = this.props.additional_charge_added;
        }

       _onClickAdd(combo_product,prd_combo){
             var order_lines = this.env.pos.get_order().get_orderlines();
                   var total_charge_list = []
                   var total_charge_dict = {}
                   var data_list = []
                   var dict_pr = {}
                   for (var i = 0; i < combo_product.length; i++) {
                             var  qnty=this.qty_updated_dict[combo_product[i].id];
                             dict_pr = {
                                            'product_id':combo_product[i].id,
                                            'product_name':combo_product[i].display_name,
                                            'price':combo_product[i].lst_price,
                                            'combo_product_id':prd_combo.id,
                                            'quantity':qnty,
                                            'uom':combo_product[i].uom_id[0]


                                  }
                                  data_list.push(dict_pr)
                   }
                    for(var j=0;j<added_products.length;j++){
                             var qnty=$("input[data-booking_td=" + added_products[j].id + "]").val();
                             dict_pr = {
                                            'product_id':added_products[j].id,
                                            'product_name':added_products[j].display_name,
                                            'price':added_products[j].lst_price,
                                            'combo_product_id':prd_combo.id,
                                            'quantity':qnty,
                                            'uom':added_products[j].uom_id[0]


                                  }
                                  data_list.push(dict_pr)

                       }
                       if (this.additional_charge){
                           var total_price_combo = $("a[data-total_price=" + prd_combo.id + "]").html();
                           var total_charge = parseFloat(this.additional_charge) + parseFloat(total_price_combo);
                         }
                       else{
                           var total_charge = $("a[data-total_price=" + prd_combo.id + "]").html();
                        }

                      total_charge_dict = {'total_charge': total_charge}
                      total_charge_list.push(total_charge_dict)
                      this.env.pos.get_order().add_product(prd_combo,{combo_products_ordered: data_list,total_charge_list:total_charge_list});


             this.trigger('close-popup');
        }
        cancel() {
			this.trigger('close-popup');
		}

         _onClickAddMore(add_id,add_product,name,uom,price,already_selected_combo){
            for(var i=0;i<add_product.length;i++){
                      if(add_product[i].id==add_id){
                            added_products.push(add_product[i]);
                      }
           }
           var prqty=$("input[data-booking_td=" + add_id + "]").val();
            $('.added').append(name ,"(",prqty,uom,"at ",this.env.pos.format_currency(price),"/",uom," ) , \n");
            var total_price_combo = $("a[data-total_price=" + already_selected_combo.id + "]").html();
            var total_added_price = parseFloat(prqty) * parseFloat(price);
            var total = parseFloat(total_price_combo) + parseFloat(total_added_price);
            if(already_selected_combo.combo_sale_price != "product"){
                    $("a[data-total_price=" + already_selected_combo.id + "]").html(total);
                    $("span[data-total_price=" + already_selected_combo.id + "]").html(this.env.pos.format_currency(total));
               }
         }
         _onClickQtyAdd(current_product){
                  var qty= $("input[data-booking_td=" + current_product + "]").val();
                  var j=0;
                    qty++;
                    $("input[data-booking_td=" + current_product + "]").val(qty);
                    if(flag==0){
                        update_qty_of_products.push(current_product);
                    }
                    else{
                        for(var i=0;i<update_qty_of_products.length;i++){
                                 if(current_product==update_qty_of_products[i]){
                                          j=1;
                                 }
                        }
                        if(j==0){
                            update_qty_of_products.push(current_product);
                        }
                    }
                    flag++;
         }
         _onClicQtyMinus(current_product) {
		     var qty= $("input[data-booking_td=" + current_product + "]").val();
		     var j=0;
		     qty--;
		     $("input[data-booking_td=" + current_product + "]").val(qty);
		     if(flag==0){
		        update_qty_of_products.push(current_product);
		     }
		     else{
		        for(var i=0;i<update_qty_of_products.length;i++){
		                 if(current_product==update_qty_of_products[i]){
		                          j=1;
		                 }
		        }
		        if(j==0){
		            update_qty_of_products.push(current_product);
		        }
		    }
             flag++;
		}

        updateComboProducts(event) {
            if (event.key === 'Enter') {
                var word = event.target.value
                try {
                    word = word.replace(/[\[\]\(\)\+\*\?\.\-\!\&\^\$\|\~\_\{\}\:\,\\\/]/g,'.');
                    word = word.replace(/ /g,'.+');
                } catch(e) {
                    return [];
                }

                var new_all_products_pos = [];
                for(var i = 0; i < this.all_products_pos.length; i++){
                    var str = this.all_products_pos[i].display_name.toLowerCase();
                    if(str.indexOf(word) >= 0) {
                        new_all_products_pos.push(this.all_products_pos[i].id);
                    }

                }
                if (new_all_products_pos) {
                    for(var i = 0; i < this.all_products_pos.length; i++){
                        if (!new_all_products_pos.includes(this.all_products_pos[i].id)){
                            $('[data-booking_tr='+this.all_products_pos[i].id+']').hide()
                        } else {
                            $('[data-booking_tr='+this.all_products_pos[i].id+']').show()
                        }
                    }
                }
            }
        }

    }
    ProductLists.template = 'ProductLists';
    ProductLists.defaultProps = {
        confirmText: 'Save',
        cancelText: 'Cancel',
        title: '',
        body: '',
        document: '',
        startingValue: '',
        startingValue: '',
    };

    Registries.Component.add(ProductLists);
    return ProductLists;

});