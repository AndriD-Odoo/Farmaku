odoo.define("sh_pos_theme_responsive.action_pad_widget", function (require) {
	
	const ActionpadWidget = require("point_of_sale.ActionpadWidget");
    const Registries = require("point_of_sale.Registries");
    const { useBarcodeReader } = require("point_of_sale.custom_hooks");
    const { useListener } = require("web.custom_hooks");
    const ProductsWidget = require("point_of_sale.ProductsWidget");

    const PosActionpadWidget = (ActionpadWidget) =>
        class extends ActionpadWidget {
            constructor() {
                super(...arguments);
                useListener("click-slide-down", this.on_slide_icon);
            }
            async on_slide_icon(event) {
                var self = this;
                $("div.numpad").slideToggle("slow", function(){
                	if($('.slide_toggle_button').find('.fa')){
                		if($('.slide_toggle_button').find('.fa').hasClass('fa-chevron-down')){
                			$('.slide_toggle_button').find('.fa').removeClass('fa-chevron-down')
                			$('.slide_toggle_button').find('.fa').addClass('fa-chevron-up')
                		}
                		else if($('.slide_toggle_button').find('.fa').hasClass('fa-chevron-up')){
                			$('.slide_toggle_button').find('.fa').removeClass('fa-chevron-up')
                			$('.slide_toggle_button').find('.fa').addClass('fa-chevron-down')
                		}
                	}
                });
                
            }
        };

    Registries.Component.extend(ActionpadWidget, PosActionpadWidget);
	
});