odoo.define("sh_pos_theme_responsive.product_widget_control_panel", function (require) {
	
	const ProductsWidgetControlPanel = require("point_of_sale.ProductsWidgetControlPanel");
    const Registries = require("point_of_sale.Registries");
    
    const PosProductsWidgetControlPanel = (ProductsWidgetControlPanel) =>
    class extends ProductsWidgetControlPanel {
    	constructor() {
            super(...arguments);
            this.hide_searchbar = true;
    	}
    	sh_search_input() {
    		if(this.hide_searchbar){
    			this.hide_searchbar = false;
    			$('.icon').addClass('sh_open_search_bar')
    			this.render();
    		}else{
    			this.hide_searchbar = true;
    			$('.icon').removeClass('sh_open_search_bar')
    			this.render();
    		}
    	}
    };
    Registries.Component.extend(ProductsWidgetControlPanel, PosProductsWidgetControlPanel);
	
});