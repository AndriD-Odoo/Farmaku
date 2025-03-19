odoo.define("sh_pos_theme_responsive.client_list_screen", function (require) {
    "use strict";
    
    const ClientListScreen = require("point_of_sale.ClientListScreen");
    const Registries = require("point_of_sale.Registries");

    const PosClientListScreen = (ClientListScreen) =>
        class extends ClientListScreen {
        	constructor() {
                super(...arguments);
                
            }
        	mounted() {
        		if(this.env.isMobile){
                	$('.pos-content').addClass('sh_client_pos_content')
                }else{
                }
        	}
        	back() {
        		
        		if(this.state.detailIsShown) {
                    this.state.detailIsShown = false;
                    this.render();
                } else {
                    this.props.resolve({ confirmed: false, payload: false });
                    if($('.pos-content').hasClass('sh_client_pos_content')){
                    	$('.pos-content').removeClass('sh_client_pos_content')
                    }
                    this.trigger('close-temp-screen');
                }
        	}
        };

    Registries.Component.extend(ClientListScreen, PosClientListScreen);
});