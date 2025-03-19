odoo.define("sh_pos_theme_responsive.product_screen", function (require) {
    "use strict";
    
    const ProductScreen = require("point_of_sale.ProductScreen");
    const Registries = require("point_of_sale.Registries");
    const ControlButtonsMixin = require('point_of_sale.ControlButtonsMixin');
    
    const PosProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            constructor() {
                super(...arguments);
                var self = this;
                
                setTimeout(() => {
                	var owl = $('#owl-demo-product-screen');
		            owl.owlCarousel({
		                loop:false,
		                nav:true,
		                margin:10,
		                responsive:{
		                    0:{
		                        items:1
		                    },
		                    600:{
		                        items:3
		                    },            
		                    960:{
		                        items:5
		                    },
		                    1200:{
		                        items:5
		                    }
		                }
		            });
		            owl.on('mousewheel', '.owl-stage', function (e) {
		                if (e.originalEvent.wheelDelta > 0) {
		                    owl.trigger('next.owl');
		                } else {
		                    owl.trigger('prev.owl');
		                }
		                e.preventDefault();
		            });
                    owl.find('.owl-nav').hide()
                    owl.find('.owl-dots').hide()
                }, 20);

            }
            mounted() {
            	super.mounted();
                
                if($('.pos-content').hasClass('sh_client_pos_content')){
                	$('.pos-content').removeClass('sh_client_pos_content')
                }
                var control_button_length = this.constructor.controlButtons
                    .filter((cb) => {
                        return cb.condition.bind(this)();
                    })
                    .map((cb) =>
                        Object.assign({}, cb, { component: Registries.Component.get(cb.component) })
                    );
                if(control_button_length && control_button_length.length == 0){
                	if($('.screen-full-width')){
                		$('.screen-full-width').addClass('not_control_button')
                	}
                	
                }
                if(this.env.pos.pos_theme_settings_data && this.env.pos.pos_theme_settings_data[0] && this.env.pos.pos_theme_settings_data[0].sh_cart_total_sticky){
                    if($('.summary')){
                        $('.summary').addClass('sticky_total')
                    }
                }
                if(this.env.isMobile){
                	if(this.env.pos.pos_theme_settings_data[0].sh_mobile_start_screen == "product_screen"){
                    	$(".leftpane").css("display","none");
                        $(".rightpane").css("display","flex");
                        
                        $(".sh_product_management").removeClass('hide_cart_screen_show');
                        $(".sh_cart_management").removeClass('hide_product_screen_show');
                        
                        $(".sh_cart_management").css("display","none");
                        $(".sh_product_management").css("display","block");
                        
                    }
                    if(this.env.pos.pos_theme_settings_data[0].sh_mobile_start_screen == "cart_screen"){
//                    	this.mobile_pane = this.props.mobile_pane || 'left';
                    	
                        $(".rightpane").css("display","none");
                        $(".leftpane").css("display","flex");
                        
                        $(".sh_product_management").removeClass('hide_cart_screen_show');
                        $(".sh_cart_management").removeClass('hide_product_screen_show');
                        
                        $(".sh_product_management").css("display","none");
                        $(".sh_cart_management").css("display","block");
                        $(".search-box").css("display","none");
                    }
                    if(this.env.pos.pos_theme_settings_data[0].sh_mobile_start_screen == "product_with_cart"){
                    	
                    	$(".sh_product_management").removeClass('hide_cart_screen_show');
                    	$(".sh_cart_management").removeClass('hide_product_screen_show');
                    	
                    	$('.sh_product_management').css("display","none")
                    }
                } 
            }
        };

    Registries.Component.extend(ProductScreen, PosProductScreen);
});