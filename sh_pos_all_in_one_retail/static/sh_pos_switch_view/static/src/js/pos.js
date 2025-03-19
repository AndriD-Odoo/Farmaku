odoo.define("sh_pos_switch_view.action_button", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const ProductList = require("point_of_sale.ProductList")
    const ProductScreen = require("point_of_sale.ProductScreen");
    const { useListener } = require("web.custom_hooks");
    const Registries = require("point_of_sale.Registries");
    const ProductsWidgetControlPanel = require("point_of_sale.ProductsWidgetControlPanel");
    const Chrome = require("point_of_sale.Chrome");
    var core = require('web.core');
    var QWeb = core.qweb;

    var models = require("point_of_sale.models");

    // models.load_fields("product.product", ["type","qty_available", "virtual_available"]);

    class ProductListItem extends PosComponent {
    	constructor() {
            super(...arguments);
            useListener("Add_Product", this.Add_Product);
        }
    	get imageUrl() {
            const product = this.props.product;
            return `/web/image?model=product.product&field=image_128&id=${product.id}&write_date=${product.write_date}&unique=1`;
        }
        get pricelist() {
            const current_order = this.env.pos.get_order();
            if (current_order) {
                return current_order.pricelist;
            }
            return this.env.pos.default_pricelist;
        }
        get price() {
            const formattedUnitPrice = this.env.pos.format_currency(
                this.props.product.get_price(this.pricelist, 1),
                'Product Price'
            );
            if (this.props.product && this.props.product.to_weight && this.props.product.uom_id && this.props.product[0]) {
                return `${formattedUnitPrice}/${
                    this.env.pos.units_by_id[this.props.product.uom_id[0]].name
                }`;
            } else {
                return formattedUnitPrice;
            }
        }
        Add_Product(e) {
            var qty_val = 0;
            const product = e.detail;
            let { confirmed, payload } = this.showPopup("ProductQtybagPopup", {
                qty_val: qty_val,
                title: 'Add Bags',
                product: product,
            });
            if (confirmed) {
            } else {
                return;
            }
        }
    }
    ProductListItem.template = 'ProductListItem';

    Registries.Component.add(ProductListItem);

    
    const PosChrome = (Chrome) =>
    class extends Chrome {
        constructor() {
            super(...arguments);
            useListener('change-view', this.change_view);
        }
        change_view(){
            this.render()
        }
    };
    Registries.Component.extend(Chrome, PosChrome);



    const PosProductsWidgetControlPanel = (ProductsWidgetControlPanel) =>
    class extends ProductsWidgetControlPanel {
        constructor(){
            super(...arguments);
            useListener('click-product-grid-view', this.onClickProductGridView)
            useListener('click-product-list-view', this.onClickProductListView)


        }
        mounted(){
            super.mounted();
            if(this.env.pos.config.sh_pos_switch_view == false){
                $('.sh_switch_view_icon').hide()
            }else{
                if(this.env.pos.config.sh_default_view == 'grid_view'){
                    $('.product_grid_view').addClass('highlight');
                    $('.product_list').hide()
                    $(".rightpane").removeClass("sh_right_pane");
                    this.env.pos.product_view = 'grid'
                }else if(this.env.pos.config.sh_default_view == 'list_view'){
                    $('.product_list_view').addClass('highlight');
                    $('.product_grid').hide()
                    $(".rightpane").addClass("sh_right_pane");
                    this.env.pos.product_view = 'list'
                }
            }
        }
        onClickProductGridView(event){
            if($('.product_list_view').hasClass('highlight')){
            	$('.product_list_view').removeClass('highlight')
            	$('.product_grid_view').addClass('highlight')
            	$(".rightpane").removeClass("sh_right_pane");
            }
            this.env.pos.product_view = 'grid'
            $('.product_grid').show()
            $('.product_list').hide()
            this.trigger('change-view')
            
        }
        onClickProductListView(){
        	if($('.product_grid_view').hasClass('highlight')){
            	$('.product_grid_view').removeClass('highlight')
            	$('.product_list_view').addClass('highlight')
            	$(".rightpane").addClass("sh_right_pane");
            }
            this.env.pos.product_view = 'list'
            $('.product_grid').hide()
            $('.product_list').show()
            this.trigger('change-view')

        }
    };
    Registries.Component.extend(ProductsWidgetControlPanel, PosProductsWidgetControlPanel);

    const PosProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            constructor() {
                super(...arguments);
                this.env.pos.product_view;
                if(this.env.pos.config.sh_pos_switch_view == false){
                    $('.sh_switch_view_icon').hide()
                }else{
                	if(this.env.pos.config.sh_default_view == 'grid_view'){
                		$('.product_grid_view').addClass('highlight');
                		$('.product_list').hide()
                        this.env.pos.product_view = 'grid'
                	}else if(this.env.pos.config.sh_default_view == 'list_view'){
                		$('.product_list_view').addClass('highlight');
                		$('.product_grid').hide()
                        this.env.pos.product_view = 'list'
                	}
                }
            }
            mounted(){
            	super.mounted();
            	if(this.env.pos.config.sh_default_view == 'grid_view'){
                		$('.product_list').hide()
                	}else if(this.env.pos.config.sh_default_view == 'list_view'){
                		$('.product_grid').hide()
                	}
            }
            switchPane() {
                if (this.env.pos.config.sh_pos_switch_view == false) {
                    $(".sh_switch_view_icon").hide();
                } else {
                    if (this.env.pos.config.sh_default_view == "grid_view") {
                        $(".product_grid_view").addClass("highlight");
                        $(".product_list").hide();
                        $(".rightpane").removeClass("sh_right_pane");
                        this.env.pos.product_view = "grid";
                    } else if (this.env.pos.config.sh_default_view == "list_view") {
                        $(".product_list_view").addClass("highlight");
                        $(".product_grid").hide();
                        $(".rightpane").addClass("sh_right_pane");
                        this.env.pos.product_view = "list";
                    }
                }
                super.switchPane();
            }
        };
    Registries.Component.extend(ProductScreen, PosProductScreen);
});
