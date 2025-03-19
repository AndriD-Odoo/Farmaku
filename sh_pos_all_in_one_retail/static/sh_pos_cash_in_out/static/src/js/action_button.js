odoo.define("sh_pos_cash_in_out.ActionButton", function (require) {
    "use strict";
        
    const PosComponent = require("point_of_sale.PosComponent");
    const { useListener } = require("web.custom_hooks");
    const Registries = require("point_of_sale.Registries");
    const ProductScreen = require("point_of_sale.ProductScreen");
    const rpc = require("web.rpc");
    
    class CashInOutButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener("click-cash-control", this.onClickTemplateLoad);
        }
        onClickTemplateLoad() {
            let { confirmed, payload } = this.showPopup("CashInOutOptionPopupWidget");
            if (confirmed) {
            } else {
                return;
            }
        }
    }
    CashInOutButton.template = "CashInOutButton";
    ProductScreen.addControlButton({
        component: CashInOutButton,
        condition: function () {
            return this.env.pos.config.sh_is_cash_in_out && this.env.pos.config.cash_control;
        },
    });
    Registries.Component.add(CashInOutButton);
    
    class CashInOutStatementButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener("click-cash-in-out-statement", this.onClickTemplateLoad);
        }
        async onClickTemplateLoad() {
        	var self = this
            let { confirmed, payload } = this.showPopup("CashInOutOptionStatementPopupWidget");
            if (confirmed) {
            } else {
                return;
            }
        }
    }
    CashInOutStatementButton.template = "CashInOutStatementButton";
    ProductScreen.addControlButton({
        component: CashInOutStatementButton,
        condition: function () {
            return this.env.pos.config.sh_is_cash_in_out && this.env.pos.config.cash_control;
        },
    });
    Registries.Component.add(CashInOutStatementButton);
    
    return {
    	CashInOutButton,
    	CashInOutStatementButton,
    };
    
});
