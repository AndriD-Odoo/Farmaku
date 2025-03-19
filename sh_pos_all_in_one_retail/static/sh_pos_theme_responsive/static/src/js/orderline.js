odoo.define("sh_pos_theme_responsive.orderline", function (require) {
    "use strict";

    const Orderline = require("point_of_sale.Orderline");
    const Registries = require("point_of_sale.Registries");
    const { useBarcodeReader } = require("point_of_sale.custom_hooks");
    const { useListener } = require("web.custom_hooks");
    const ProductsWidget = require("point_of_sale.ProductsWidget");

    const PosOrderlineScreen = (Orderline) =>
        class extends Orderline {
            constructor() {
                super(...arguments);
                useListener("click-remove-line-icon", this.on_remove_line_icon);
            }
            async on_remove_line_icon(event) {
                var self = this;
                this.trigger('select-line', { orderline: this.props.line });
                
                self.env.pos.get_order().remove_orderline(self.env.pos.get_order().get_selected_orderline())
            }
            imageUrl(product) {
                return `/web/image?model=product.product&field=image_128&id=${product.id}&write_date=${product.write_date}&unique=1`;
            }
            mounted(){
            	
	           	 $("li.orderline").mouseover(function () {
	           		 
	           		$(this).find('.sh_orderline_icons').slideDown("slow", function(){
          				 $(this).find('.sh_orderline_icons').addClass('selected')
              		 });
	           		 
	                });
	           	 $( "li.orderline" ).mouseleave(function() {
	           		 if(!$(this).hasClass('selected')){
//	           			 $(this).find('.sh_orderline_icons').removeClass('selected')
	           			$(this).find('.sh_orderline_icons').slideUp("slow", function(){
	           				 $(this).find('.sh_orderline_icons').removeClass('selected')
	               		 });
	           		 }
	           		 
	           	 });
	           	 super.mounted()
           }
           selectLine() {
            	$('li.orderline.selected').find('.sh_orderline_icons').slideUp()
                super.selectLine();
            }
        };

    Registries.Component.extend(Orderline, PosOrderlineScreen);
});