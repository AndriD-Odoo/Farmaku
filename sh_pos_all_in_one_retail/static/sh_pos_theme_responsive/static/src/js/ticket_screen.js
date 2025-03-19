odoo.define("sh_pos_theme_responsive.ticket_screen", function (require) {
    "use strict";
    
    const Registries = require("point_of_sale.Registries");
    const TicketScreen = require("point_of_sale.TicketScreen");
    const OrderSummary = require("point_of_sale.OrderSummary");
    
    const PosTicketScreen = (TicketScreen) =>
    class extends TicketScreen {
    	constructor() {
            super(...arguments);            
        }
    	mounted() {
            super.mounted()
    		if(this.env.isMobile){
            	$('.pos-content').addClass('sh_client_pos_content')
            	$('.sh_product_management').addClass('hide_cart_screen_show')
            	$('.sh_cart_management').addClass('hide_product_screen_show')
            }
    	}
    };

    Registries.Component.extend(TicketScreen, PosTicketScreen);

    const PosOrderSummary = (OrderSummary) =>
    class extends OrderSummary {
    	mounted(){
    		super.mounted();
    		if(this.env.pos.pos_theme_settings_data && this.env.pos.pos_theme_settings_data[0] && this.env.pos.pos_theme_settings_data[0].sh_cart_total_sticky){
                if($('.summary')){
                    $('.summary').addClass('sticky_total')
                }
            }
    	}
    };

    Registries.Component.extend(OrderSummary, PosOrderSummary);
    
});