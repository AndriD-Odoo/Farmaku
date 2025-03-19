odoo.define('sh_pos_product_variant.variant_pos', function (require, factory) {
    'use strict';

    const Registries = require("point_of_sale.Registries");
    const AbstractAwaitablePopup = require("point_of_sale.AbstractAwaitablePopup");
    const { useListener } = require("web.custom_hooks");
    const { Gui } = require("point_of_sale.Gui");
    var utils = require('web.utils');
    var models = require('point_of_sale.models')

    class variantPopup extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            useListener('click-product', this._clickProduct1);
            this.alternative_products = arguments[1].alternative_products
            this.product_variants = arguments[1].product_variants
            this.attributes_name = arguments[1].attributes_name
            this.attibute_list = []
        }
        updateSearch(event) {
            this.searchWord = event.target.value;
            this.render()
        }
        async _clickProduct1(event) {
        	
            var product = event.detail
            var self = this
            if(self.env.pos.config.enable_product_bundle){    
            	if(product && product.product_tmpl_id && product.sh_is_bundle){            		
            		var product_tmpl_id = product.product_tmpl_id;
            		if(product_tmpl_id){            			
            			let bundle_by_product_id = this.env.pos.db.bundle_by_product_id[product_tmpl_id];
            			if(bundle_by_product_id && bundle_by_product_id.length > 0){            				
            				const { confirmed } = await self.showPopup('ConfirmPopup', {
                                title: this.env._t('Confirmation'),
                                body: _.str.sprintf(
                                  this.env._t('%s have Bundle. Do you want to see it ?'),
                                  product.display_name
                                ),
                            });
                            if (!confirmed){
                            	var currentOrder = this.env.pos.get_order()
                                currentOrder.add_product(product)
                                if (!this.env.pos.config.sh_close_popup_after_single_selection ) {
                                	if (self.product_variants.length > 1) {
					                    if (!self.env.pos.config.sh_pos_variants_group_by_attribute && self.env.pos.config.sh_pos_enable_product_variants) {
					                        if (self.product_variants.length > 6 && this.product_variants.length < 15) {
					                        	Gui.showPopup("variantPopup", { 'title': 'Product Variants', 'morevariant_class': 'sh_lessthan_8_variants', product_variants: this.product_variants, alternative_products: this.alternative_products })
					                        }
					                        else if (self.product_variants.length > 15) {
					                            Gui.showPopup("variantPopup", { 'title': 'Product Variants', 'morevariant_class': ' sh_morethan_15_variants', product_variants: this.product_variants, alternative_products: this.alternative_products })
					                        }
					                        else {
					                            Gui.showPopup("variantPopup", { 'title': 'Product Variants', product_variants: this.product_variants, alternative_products: this.alternative_products })
					                        }
					                    
					                    }
					                    else if (self.env.pos.config.sh_pos_variants_group_by_attribute && self.env.pos.config.sh_pos_enable_product_variants) {
					                        self.Attribute_names = []
					                        _.each(event.detail.attribute_line_ids, function (each_attribute) {
					                            self.Attribute_names.push(self.env.pos.db.product_temlate_attribute_line_by_id[each_attribute])
					                        })
					                        if (self.Attribute_names.length > 0) {
					                         
					                            Gui.showPopup("variantPopup", { 'title': 'Product Variants', attributes_name: this.Attribute_names, alternative_products: this.alternative_products })
					                        } 
					                    }
					                }
                                }
                            	return;
                            }else{
                            	
                            	var table_html =
                                    '<table width="100%" class="wh_qty" id="bundle_product_table"><thead><tr><th width="10%" class="head_td">No</th><th width="55%" class="head_td">Product</th><th width="15%" class="head_td">Qty</th><th width="20%" class="head_td">UOM</th></tr></thead>';
                                var total_price = 0.0;
                                var count = 1;
                                $.each(bundle_by_product_id, function (key, value) {
                                    var subtotal = value[1] * value[3];
                                    total_price += subtotal;
                                    table_html += '<tr class="data_tr" data-id="' + value[0][0] + '"><td class="data_td">' + count + '</td><td class="data_td">' + value[0][1] + "</td>";
                                    table_html += '<td class="data_td"><input type="hidden" class="hidden_qty" value="' + value[1] + '"/><input type="text" class="qty_input" value="' + value[1] + '"/></td><td class="data_td">' + value[2][1] + "</td>";
                                    table_html += "</tr>";
                                    count += 1;
                                });
                                
                                const { confirmed } = await Gui.showPopup('ProductBundleQtyPopup', {
                                    title: product.display_name,
                                    body: table_html,
                                    price: product.lst_price.toFixed(2),
                                });

                                if (confirmed) {
                                    var input_qty = $("#product_qty").val();
                                    var lst_price = $("#product_price").val();

                                    // get bundle products
                                    _.each($("#bundle_product_table").find("tr.data_tr"), function (row) {
                                        _.each($(row).find("input.qty_input"), function ($input) {
                                            var product_options = {};
                                            product_options["price"] = 0.0;
                                            product_options["quantity"] = $($input).val();
                                            var product = self.env.pos.db.product_by_id[$(row).data("id")];
                                            self.env.pos.get_order().add_product(product, product_options);
                                            var lines = self.env.pos.get_order().get_orderlines();
                                            for (var i = 0; i < lines.length; i++) {
                                                if (lines[i].get_product() === product) {
                                                    lines[i].set_unit_price(0.0);
                                                    lines[i].price_manually_set = true;
                                                    return;
                                                }
                                            }
                                        });
                                    });

                                    // Add main product
                                    var main_product = self.env.pos.db.product_by_id[product.id];
                                    var product_options = {};
                                    product_options["quantity"] = input_qty;
                                    product_options["price"] = lst_price;
                                    self.env.pos.get_order().add_product(main_product, product_options);

                                    if (!self.env.pos.config.sh_close_popup_after_single_selection ) {
                                    	if (!self.env.pos.config.sh_pos_variants_group_by_attribute && self.env.pos.config.sh_pos_enable_product_variants) {
                                            if (self.product_variants.length > 6 && self.product_variants.length < 15) {
                                                Gui.showPopup("variantPopup", { 'title': 'Product Variants', 'morevariant_class': 'sh_lessthan_8_variants', product_variants: self.product_variants, alternative_products: self.alternative_products })
                                            }
                                            else if (self.product_variants.length > 15) {
                                                Gui.showPopup("variantPopup", { 'title': 'Product Variants', 'morevariant_class': ' sh_morethan_15_variants', product_variants: self.product_variants, alternative_products: self.alternative_products })
                                            }
                                            else {
                                                Gui.showPopup("variantPopup", { 'title': 'Product Variants', product_variants: self.product_variants, alternative_products: self.alternative_products })
                                            }
                                        
                                        }
                                        else if (self.env.pos.config.sh_pos_variants_group_by_attribute && self.env.pos.config.sh_pos_enable_product_variants) {
                                            if (self.attributes_name.length > 0) {
                                             
                                                Gui.showPopup("variantPopup", { 'title': 'Product Variants', attributes_name: self.attributes_name, alternative_products: self.alternative_products })
                                            } 
                                        }
                                    }
                                    var lines = self.env.pos.get_order().get_orderlines();
                                    for (var i = 0; i < lines.length; i++) {
                                        if (lines[i].get_product() === product) {
                                            lines[i].set_unit_price(lst_price);
                                            lines[i].price_manually_set = true;
                                            return;
                                        }
                                    }
                                } else {
                                	
                                	if (!self.env.pos.config.sh_close_popup_after_single_selection ) {
                                    	if (!self.env.pos.config.sh_pos_variants_group_by_attribute && self.env.pos.config.sh_pos_enable_product_variants) {
                                            if (self.product_variants.length > 6 && self.product_variants.length < 15) {
                                                Gui.showPopup("variantPopup", { 'title': 'Product Variants', 'morevariant_class': 'sh_lessthan_8_variants', product_variants: self.product_variants, alternative_products: self.alternative_products })
                                            }
                                            else if (self.product_variants.length > 15) {
                                                Gui.showPopup("variantPopup", { 'title': 'Product Variants', 'morevariant_class': ' sh_morethan_15_variants', product_variants: self.product_variants, alternative_products: self.alternative_products })
                                            }
                                            else {
                                                Gui.showPopup("variantPopup", { 'title': 'Product Variants', product_variants: self.product_variants, alternative_products: self.alternative_products })
                                            }
                                        
                                        }
                                        else if (self.env.pos.config.sh_pos_variants_group_by_attribute && self.env.pos.config.sh_pos_enable_product_variants) {
                                            if (self.attributes_name.length > 0) {
                                             
                                                Gui.showPopup("variantPopup", { 'title': 'Product Variants', attributes_name: self.attributes_name, alternative_products: self.alternative_products })
                                            } 
                                        }
                                    }
                                    return;
                                }
                            }
            			}
            		}
            	}
            }
            
            
            var currentOrder = this.env.pos.get_order()
            currentOrder.add_product(product)
            if (this.env.pos.config.sh_close_popup_after_single_selection ) {
                this.trigger("close-popup");
            }
        }
        async Confirm() {
            var self = this
            var lst = []
            var currentOrder = this.env.pos.get_order()
            if ($('#attribute_value.highlight')) {
                _.each($('#attribute_value.highlight'), function (each) {
                    lst.push(parseInt($(each).attr('data-id')))
                })
            }
            var added_product = false;
            _.each(self.env.pos.db.product_by_id, async function (product) {

                if(product.product_template_attribute_value_ids.length > 0 && JSON.stringify(product.product_template_attribute_value_ids)===JSON.stringify(lst)) {
                    
                	if(self.env.pos.config.enable_product_bundle){    
                    	if(product && product.product_tmpl_id && product.sh_is_bundle){            		
                    		var product_tmpl_id = product.product_tmpl_id;
                    		if(product_tmpl_id){            			
                    			let bundle_by_product_id = self.env.pos.db.bundle_by_product_id[product_tmpl_id];
                    			if(bundle_by_product_id && bundle_by_product_id.length > 0){            				
                    				const { confirmed } = await self.showPopup('ConfirmPopup', {
                                        title: self.env._t('Confirmation'),
                                        body: _.str.sprintf(
                                          self.env._t('%s have Bundle. Do you want to see it ?'),
                                          product.display_name
                                        ),
                                    });
                                    if (!confirmed){
                                    	currentOrder.add_product(product)
                                        if (!self.env.pos.config.sh_close_popup_after_single_selection ) {
                                        	if (self.attributes_name.length > 0) {
        					                    if (!self.env.pos.config.sh_pos_variants_group_by_attribute && self.env.pos.config.sh_pos_enable_product_variants) {
        					                        if (self.product_variants.length > 6 && self.product_variants.length < 15) {
        					                        	Gui.showPopup("variantPopup", { 'title': 'Product Variants', 'morevariant_class': 'sh_lessthan_8_variants', product_variants: self.product_variants, alternative_products: self.alternative_products })
        					                        }
        					                        else if (self.product_variants.length > 15) {
        					                            Gui.showPopup("variantPopup", { 'title': 'Product Variants', 'morevariant_class': ' sh_morethan_15_variants', product_variants: self.product_variants, alternative_products: self.alternative_products })
        					                        }
        					                        else {
        					                            Gui.showPopup("variantPopup", { 'title': 'Product Variants', product_variants: self.product_variants, alternative_products: self.alternative_products })
        					                        }
        					                    
        					                    }
        					                    else if (self.env.pos.config.sh_pos_variants_group_by_attribute && self.env.pos.config.sh_pos_enable_product_variants) {
        					                        if (self.attributes_name.length > 0) {
        					                            Gui.showPopup("variantPopup", { 'title': 'Product Variants', attributes_name: self.attributes_name, alternative_products: self.alternative_products })
        					                        } 
        					                    }
        					                }
                                        }
                                    	return;
                                    }else{
                                    	
                                    	var table_html =
                                            '<table width="100%" class="wh_qty" id="bundle_product_table"><thead><tr><th width="10%" class="head_td">No</th><th width="55%" class="head_td">Product</th><th width="15%" class="head_td">Qty</th><th width="20%" class="head_td">UOM</th></tr></thead>';
                                        var total_price = 0.0;
                                        var count = 1;
                                        $.each(bundle_by_product_id, function (key, value) {
                                            var subtotal = value[1] * value[3];
                                            total_price += subtotal;
                                            table_html += '<tr class="data_tr" data-id="' + value[0][0] + '"><td class="data_td">' + count + '</td><td class="data_td">' + value[0][1] + "</td>";
                                            table_html += '<td class="data_td"><input type="hidden" class="hidden_qty" value="' + value[1] + '"/><input type="text" class="qty_input" value="' + value[1] + '"/></td><td class="data_td">' + value[2][1] + "</td>";
                                            table_html += "</tr>";
                                            count += 1;
                                        });
                                        const { confirmed } = await Gui.showPopup('ProductBundleQtyPopup', {
                                            title: product.display_name,
                                            body: table_html,
                                            price: product.lst_price.toFixed(2),
                                        });

                                        if (confirmed) {
                                            // on confirm added all cart products in cart
                                            var input_qty = $("#product_qty").val();
                                            var lst_price = $("#product_price").val();

                                            // get bundle products
                                            _.each($("#bundle_product_table").find("tr.data_tr"), function (row) {
                                                _.each($(row).find("input.qty_input"), function ($input) {
                                                    var product_options = {};
                                                    product_options["price"] = 0.0;
                                                    product_options["quantity"] = $($input).val();
                                                    var product = self.env.pos.db.product_by_id[$(row).data("id")];
                                                    self.env.pos.get_order().add_product(product, product_options);
                                                    var lines = self.env.pos.get_order().get_orderlines();
                                                    for (var i = 0; i < lines.length; i++) {
                                                        if (lines[i].get_product() === product) {
                                                            lines[i].set_unit_price(0.0);
                                                            lines[i].price_manually_set = true;
                                                            return;
                                                        }
                                                    }
                                                });
                                            });

                                            // Add main product
                                            var main_product = self.env.pos.db.product_by_id[product.id];
                                            var product_options = {};
                                            product_options["quantity"] = input_qty;
                                            product_options["price"] = lst_price;
                                            self.env.pos.get_order().add_product(main_product, product_options);
                                            if (!self.env.pos.config.sh_close_popup_after_single_selection ) {
                                            	if (!self.env.pos.config.sh_pos_variants_group_by_attribute && self.env.pos.config.sh_pos_enable_product_variants) {
                                                    if (self.product_variants.length > 6 && self.product_variants.length < 15) {
                                                        Gui.showPopup("variantPopup", { 'title': 'Product Variants', 'morevariant_class': 'sh_lessthan_8_variants', product_variants: self.product_variants, alternative_products: self.alternative_products })
                                                    }
                                                    else if (self.product_variants.length > 15) {
                                                        Gui.showPopup("variantPopup", { 'title': 'Product Variants', 'morevariant_class': ' sh_morethan_15_variants', product_variants: self.product_variants, alternative_products: self.alternative_products })
                                                    }
                                                    else {
                                                        Gui.showPopup("variantPopup", { 'title': 'Product Variants', product_variants: self.product_variants, alternative_products: self.alternative_products })
                                                    }
                                                
                                                }
                                                else if (self.env.pos.config.sh_pos_variants_group_by_attribute && self.env.pos.config.sh_pos_enable_product_variants) {
                                                    if (self.attributes_name.length > 0) {
                                                     
                                                        Gui.showPopup("variantPopup", { 'title': 'Product Variants', attributes_name: self.attributes_name, alternative_products: self.alternative_products })
                                                    } 
                                                }
                                            }
                                            var lines = self.env.pos.get_order().get_orderlines();
                                            for (var i = 0; i < lines.length; i++) {
                                                if (lines[i].get_product() === product) {
                                                    lines[i].set_unit_price(lst_price);
                                                    lines[i].price_manually_set = true;
                                                    return;
                                                }
                                            }
                                        } else {
                                        	if (!self.env.pos.config.sh_close_popup_after_single_selection ) {
                                            	if (!self.env.pos.config.sh_pos_variants_group_by_attribute && self.env.pos.config.sh_pos_enable_product_variants) {
                                                    if (self.product_variants.length > 6 && self.product_variants.length < 15) {
                                                        Gui.showPopup("variantPopup", { 'title': 'Product Variants', 'morevariant_class': 'sh_lessthan_8_variants', product_variants: self.product_variants, alternative_products: self.alternative_products })
                                                    }
                                                    else if (self.product_variants.length > 15) {
                                                        Gui.showPopup("variantPopup", { 'title': 'Product Variants', 'morevariant_class': ' sh_morethan_15_variants', product_variants: self.product_variants, alternative_products: self.alternative_products })
                                                    }
                                                    else {
                                                        Gui.showPopup("variantPopup", { 'title': 'Product Variants', product_variants: self.product_variants, alternative_products: self.alternative_products })
                                                    }
                                                
                                                }
                                                else if (self.env.pos.config.sh_pos_variants_group_by_attribute && self.env.pos.config.sh_pos_enable_product_variants) {
                                                    if (self.attributes_name.length > 0) {
                                                     
                                                        Gui.showPopup("variantPopup", { 'title': 'Product Variants', attributes_name: self.attributes_name, alternative_products: self.alternative_products })
                                                    } 
                                                }
                                            }
                                            return;
                                        }
                                    }
                    			}
                    		}
                    	}
                    }
                	added_product = product
                	currentOrder.add_product(product)
                	
                }
            })
            if(!added_product){
                alert("This selected attribute are excluded.")
            }
            if(this.props.attributes_name.length > $('.highlight').length){
                alert('Please Select Variant')
            }else{
                if(self.env.pos.config.sh_close_popup_after_single_selection){
                    this.trigger("close-popup");
                }else{
                    $('.sh_group_by_attribute').find('.highlight').removeClass('highlight')
                }
            }
        }
        
        mounted() {
            if(this.env.pos.config.sh_pos_variants_group_by_attribute && !this.env.pos.config.sh_pos_display_alternative_products){
                
                $('.main').addClass('sh_product_attr_no_alternative')
                $('.sh_product_variants_popup').addClass('sh_attr_no_alternative_popup')
            }
            if(this.VariantProductToDisplay && this.VariantProductToDisplay.length > 0 && this.AlternativeProducts.length > 0 ){
            	$('.main').addClass('sh_both_product')
            }
            super.mounted();
        }
        get VariantProductToDisplay() {
            if (this.searchWord) {
                var searched = this.env.pos.db.search_variants(this.props.product_variants, this.searchWord);
                return searched
            } else {
                return this.props.product_variants;
            }
        }
        get GetProductVariant(){
            return this.props.product_variants;
        }
        get AlternativeProducts() {
            return this.props.alternative_products
        }
        get Attribute_names(){
            return this.props.attributes_name
        }
        Select_attribute_value(event) {
            _.each($('.'+$(event.currentTarget).attr('class')), function (each) {
                $(each).removeClass('highlight')
            })

            if($('.sh_attribute_value').hasClass('highlight')){
                $('.sh_attribute_value').removeClass('highlight')
            }
            if ($(event.currentTarget).hasClass('highlight')) {
                $(event.currentTarget).removeClass('highlight')

            } else {
                $(event.currentTarget).addClass('highlight')
            }
        }
    }
    variantPopup.template = "variantPopup";

    Registries.Component.add(variantPopup);


});
