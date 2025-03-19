odoo.define('sh_pos_theme_responsive.HeaderButton', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const { isRpcError } = require('point_of_sale.utils');
    const Chrome = require("point_of_sale.Chrome");

    class CartIconButton extends PosComponent {
        async onClick() {
        	if(this.env.pos.pos_theme_settings_data[0].sh_mobile_start_screen == 'product_with_cart'){
        		$(".rightpane").css("display","flex");
        	}else{
        		$(".rightpane").css("display","none");
        	}
        	if(this.env.pos.pos_theme_settings_data[0].sh_mobile_start_screen == 'cart_screen' || this.env.pos.pos_theme_settings_data[0].sh_mobile_start_screen == 'product_screen'){
        		$(".search-box").css("display","none");
        	}
            $(".leftpane").css("display","flex");
            $(".sh_product_management").css("display","none");
            $(".sh_cart_management").css("display","block");
        }
    }
    CartIconButton.template = 'CartIconButton';

    Registries.Component.add(CartIconButton);
    
    class ProductIconButton extends PosComponent {
    	get startScreen() {
            return { name: 'ProductScreen',props: {'mobile_pane':'right'} };
        }
        async onClick() {
        	
        	
            $(".leftpane").css("display","none");
            $(".rightpane").css("display","flex");
            $(".sh_cart_management").css("display","none");
            $(".sh_product_management").css("display","block");
            $('.cart_screen_show').css("display","inline-block")
            $(".search-box").css("display","flex");
        }
    }
    ProductIconButton.template = 'ProductIconButton';

    Registries.Component.add(ProductIconButton);

    return {CartIconButton,ProductIconButton};
});