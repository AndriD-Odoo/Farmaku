odoo.define("sh_pos_bag_charges.bag_charges_button", function (require) {

    const PosComponent = require("point_of_sale.PosComponent");
    const { useListener } = require("web.custom_hooks");
    const Registries = require("point_of_sale.Registries");
    const ProductScreen = require("point_of_sale.ProductScreen");
    const AbstractAwaitablePopup = require("point_of_sale.AbstractAwaitablePopup");
    var rpc = require("web.rpc");


    class BagChargesBtn extends PosComponent {
        constructor() {
            super(...arguments)
            useListener('click-bag_qty-button', this.onClickButton)
        }
        onClickButton() {
            var product_length = this.env.pos.db.get_product_by_category(this.env.pos.config.sh_carry_bag_category[0])
            if (product_length.length <= 0) {
                alert("There is no Carry Bag Found !")
            }
            else {
            	this.env.pos.old_view = this.env.pos.product_view;
            	this.env.pos.product_view = 'grid'
                this.showPopup("BagCategory_list_popup", {
                    title: 'Carry Bag List',
                });
            }
        }
    }
    BagChargesBtn.template = 'bag_qty_button';
    ProductScreen.addControlButton({
        component: BagChargesBtn,
        condition: function () {
            return this.env.pos.config.sh_pos_bag_charges && this.env.pos.config.sh_carry_bag_category;
        }
    })
    Registries.Component.add(BagChargesBtn)

    class BagCategory_list_popup extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            useListener('click-product', this._clickProduct1);
        }
        _clickProduct1(event) {
            var product = event.detail
            var currentOrder = this.env.pos.get_order()
            // currentOrder.add_product(product)
            currentOrder.add_product(product, {
                quantity: 1,
            });
            this.env.pos.product_view = this.env.pos.old_view
            this.trigger("close-popup");
        }
        mounted() {
            super.mounted();
        }
        
        cancel (){
        	this.env.pos.product_view = this.env.pos.old_view
        	super.cancel()
        }
        get BagsProductToDisplay(){
        	if(this.env.pos.config.sh_carry_bag_category && this.env.pos.config.sh_carry_bag_category[0]){
        		var rec_category = this.env.pos.db.get_product_by_category(this.env.pos.config.sh_carry_bag_category[0]);
        		if(rec_category){        		
        			return rec_category;
        		}else {
        			return [];
        		}
        	}else{
        		return [];
        	}
    	}
    }
    BagCategory_list_popup.template = "bag_category_list_popup";

    Registries.Component.add(BagCategory_list_popup);

    return {
        BagChargesBtn,
        BagCategory_list_popup,
    }
});
