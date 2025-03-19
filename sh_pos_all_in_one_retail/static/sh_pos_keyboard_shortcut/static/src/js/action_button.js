odoo.define("sh_pos_keyboard_shortcut.ActionButton", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const { useListener } = require("web.custom_hooks");
    const Registries = require("point_of_sale.Registries");
    const ProductScreen = require("point_of_sale.ProductScreen");
   

    class ShortcutListTips extends PosComponent {
        constructor() {
            super(...arguments);
        }
        onClickShortcutTips(){
            
            let { confirmed, payload } = this.showPopup("ShortcutTipsPopupWidget");
            if (confirmed) {
            } else {
                return;
            }
        }
        
    }
    ShortcutListTips.template = "ShortcutListTips";

    Registries.Component.add(ShortcutListTips);

    return {
        ShortcutListTips,
    };
});
