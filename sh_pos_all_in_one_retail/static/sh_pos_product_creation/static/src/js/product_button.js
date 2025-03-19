odoo.define("sh_pos_product_creation.Product_Button", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const ProductScreen = require("point_of_sale.ProductScreen");
    const { useListener } = require("web.custom_hooks");
    const Registries = require("point_of_sale.Registries");
  

    const Chrome = require("point_of_sale.Chrome");

    const PosResChrome = (Chrome) =>
    class extends Chrome {
        constructor(){
            super(...arguments);
            useListener('click-product-button', this.onClickProductCreate)
        }
        onClickProductCreate(){
            let { confirmed, payload } = this.showPopup("Product_popup", {
                title: 'Add Product',
            });
            if (confirmed) {
            } 
        }
    };

    const PosMercuryProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            constructor() {
                super(...arguments);
                if(this.env.pos.config.create_pos_product == false){
                    $('.create_product').hide()
                }
            }
        };
    Registries.Component.extend(ProductScreen, PosMercuryProductScreen);

    Registries.Component.extend(Chrome, PosResChrome);

    return {
        Chrome,
        ProductScreen
    }
});
