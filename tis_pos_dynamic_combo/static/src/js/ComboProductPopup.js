odoo.define('point_of_sale.ComboProductPopup', function(require) {
    'use strict';

    const { useState, useRef } = owl.hooks;
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    var models = require('point_of_sale.models');
    var a=[];
    var flag=0;

    var update_qty_of_products=[];
    // formerly TextInputPopupWidget
    class ComboProductPopup extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            this.state = useState({ inputValue: this.props.startingValue });
            this.product =this.props.product;
            this.combo_products = this.env.pos.product_combo
            var j=0;
            var params = [];
            for (var i = 0; i < this.combo_products.length; i++) {
                j= this.combo_products[i].product_id;
                if (j[0]==this.props.product.product_tmpl_id){
                  params.push(this.combo_products[i]);
                }

            }
            var sum=0.00;
            if (this.props.product.combo_sale_price == "product"){
                      this.total_product_price = this.props.product.lst_price;

            }
            else{
                   for(var k=0; k<params.length;k++){
                        sum=params[k].price+sum
                    }
                    this.total_product_price = sum
                }
            this.combo_line_products=params


        }

    //Add products in combo at orderline
        add(products,combo_line){
                   var self = this;
                   var order = this.env.pos.get_order()
                   var data_list = []
                   var dict_pr = {}
                   var total_charge_list = []
                   var total_charge_dict = {}
                   const additional_charge=$("input[data-booking_td=" +products.id + "]").val();
                   var total_prd_price = $("a[data-total_price=" + products.id + "]").html();
                   if (additional_charge){
                        var total_charge = parseFloat(additional_charge) + parseFloat(total_prd_price);
                   }
                   else{
                        var total_charge = total_prd_price ;
                   }
                    for (var i = 0; i < combo_line.length; i++) {
                         var p=0;
                         var o=0;
                         let combo_lines = combo_line[i];
                         for(var j=0;j<a.length;j++){

                               if(a[j]==combo_lines.combo_product_id[0]){
                                      p=1;
                               }
                         }
                         if(p==0){

                                  var quantity=$("input[data-booking_td=" + combo_lines.combo_product_id[0] + "]").val();

                                  dict_pr = {
                                            'product_id':combo_lines.combo_product_id[0],
                                            'product_name':combo_lines.combo_product_id[1],
                                            'price':combo_lines.price,
                                            'combo_product_id':combo_lines.product_id[0],
                                            'quantity':quantity,
                                            'uom':combo_lines.uom[0]


                                  }
                                  data_list.push(dict_pr)

                           }


                    }
                    total_charge_dict = {'total_charge': total_charge}
                    total_charge_list.push(total_charge_dict)
                    this.env.pos.get_order().add_product(products,{combo_products_ordered: data_list,total_charge_list:total_charge_list});

              this.trigger('close-popup');
        }
      async addmore(combo_products,add_combo_products) {
               var dict={};
               var products_list=[];
               var total_pr_popup = $("a[data-total_price=" + combo_products.id + "]").html();
               var additional_cmb_charge = $("input[data-booking_td=" +combo_products.id + "]").val();
               for (var i = 0; i < add_combo_products.length; i++) {
                         var p=0;
                         let combo_lines = add_combo_products[i];
                         for(var j=0;j<a.length;j++){

                               if(a[j]==combo_lines.combo_product_id[0]){
                                      p=1;
                               }
                         }
                         if(p==0){
                                 var quantity=$("input[data-booking_td=" + combo_lines.combo_product_id[0] + "]").val();
                                 dict[combo_lines.combo_product_id[0]]=quantity;
                                 products_list.push(this.env.pos.db.get_product_by_id(combo_lines.combo_product_id[0]));
                         }
                      }
              await this.showPopup('ProductLists', {
              confirmText: 'Ok',
              cancelText: 'Cancel',
              title: '',
              document: '',
              body: '',
              startingValue: '',
              selected_combo:combo_products,
              product_inside_combo:products_list,
              qty_dict:dict,
              total_charge_added:total_pr_popup,
              additional_charge_added:additional_cmb_charge,
              });

		}
        cancel() {
			this.trigger('close-popup');
		}
		_onClickRemove(remove_id,unit_pr,product_passed) {
		     $("button[data-checkout_n=" + remove_id + "]").hide();
             $("tr[data-booking_tr=" + remove_id + "]").hide();
             var total_price_combo = $("a[data-total_price=" + product_passed.id + "]").html();
             var qty = $("input[data-booking_td=" + remove_id + "]").val();
             var total= Number(qty)*Number(unit_pr);
             var total_added_price = parseFloat(total_price_combo) - parseFloat(total);
             if(product_passed.combo_sale_price != "product"){
                    $("span[data-total_price=" + product_passed.id + "]").html(this.env.pos.format_currency(total_added_price));
                    $("a[data-total_price=" + product_passed.id + "]").html(total_added_price);
                }
             a.push(remove_id);

		}
        _onClickQtyAdd(current_product,price,product_passed){
           var qty= $("input[data-booking_td=" + current_product + "]").val();
           var total_price_combo = $("a[data-total_price=" + product_passed.id + "]").html();
           var j=0;
		   qty++;
		   var total= Number(qty)*Number(price);
		   $("input[data-booking_td=" + current_product + "]").val(qty);
		   $("td[data-total_id=" + current_product + "]").html(this.env.pos.format_currency(total));
		   $("span[data-total_id=" + current_product + "]").html(total);
           var total_added_price = parseFloat(total_price_combo) + parseFloat(price);
           if(product_passed.combo_sale_price != "product"){
		            $("span[data-total_price=" + product_passed.id + "]").html(this.env.pos.format_currency(total_added_price));
		            $("a[data-total_price=" + product_passed.id + "]").html(total_added_price);
		        }
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
		_onChange(current_product,price,product_passed){
		    var qty= $("input[data-booking_td=" + current_product + "]").val();
		    var total_price_combo = $("a[data-total_price=" + product_passed.id + "]").html();
		    var total_change_price = $("span[data-total_id=" + current_product + "]").html();
		    var j=0;
		    var total=qty*price;
		    $("td[data-total_id=" + current_product + "]").html(this.env.pos.format_currency(total));
		    $("span[data-total_id=" + current_product + "]").html(total);
		    var change = parseFloat(total_price_combo) - parseFloat(total_change_price)
		    var added_change = qty*price;
		    var total_added_price = parseFloat(change) + parseFloat(added_change);
		    if(product_passed.combo_sale_price != "product"){
		            $("span[data-total_price=" + product_passed.id + "]").html(this.env.pos.format_currency(total_added_price));
		            $("a[data-total_price=" + product_passed.id + "]").html(total_added_price);
		        }
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

		_onClicQtyMinus(current_product,price,product_passed) {
		     var qty= $("input[data-booking_td=" + current_product + "]").val();
		     var total_price_combo = $("a[data-total_price=" + product_passed.id + "]").html();
		     var j=0;
		     qty--;
		     var total=qty*price;
		     $("input[data-booking_td=" + current_product + "]").val(qty);
		     $("td[data-total_id=" + current_product + "]").html(this.env.pos.format_currency(total));
		     $("span[data-total_id=" + current_product + "]").html(total);
		     var total_added_price = parseFloat(total_price_combo) - parseFloat(price);
		     if(product_passed.combo_sale_price != "product"){
		            $("span[data-total_price=" + product_passed.id + "]").html(this.env.pos.format_currency(total_added_price));
		            $("a[data-total_price=" + product_passed.id + "]").html(total_added_price);
		        }
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


    }
    ComboProductPopup.template = 'ComboProductPopup';
    ComboProductPopup.defaultProps = {
        confirmText: 'Save',
        cancelText: 'Cancel',
        title: '',
        body: '',
        startingValue: '',
    };

    Registries.Component.add(ComboProductPopup);

    return ComboProductPopup;

});