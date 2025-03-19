odoo.define("sh_pos_note.ActionButton", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const { useListener } = require("web.custom_hooks");
    const Registries = require("point_of_sale.Registries");
    const ProductScreen = require("point_of_sale.ProductScreen");

    class GlobalNoteButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener("click-global-note", this.onClickTemplateLoad);
        }
        onClickTemplateLoad() {
            if (this.env.pos.get_order().get_selected_orderline()) {
                let { confirmed, payload } = this.showPopup("TemplateGlobalNotePopupWidget");
                if (confirmed) {
                } else {
                    return;
                }
            } else {
                alert("Please select the product !");
            }
        }
    }
    GlobalNoteButton.template = "GlobalNoteButton";
    ProductScreen.addControlButton({
        component: GlobalNoteButton,
        condition: function () {
            return this.env.pos.config.enable_order_note;
        },
    });
    Registries.Component.add(GlobalNoteButton);

    class AllNoteButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener("click-all-note-list", this.onClickTemplateLoad);
        }
        async onClickTemplateLoad() {
            const { confirmed, payload } = await this.showTempScreen("AllNoteScreen");
            if (confirmed) {
            }
        }
    }
    AllNoteButton.template = "AllNoteButton";
    ProductScreen.addControlButton({
        component: AllNoteButton,
        condition: function () {
            return this.env.pos.config.enable_order_note || this.env.pos.config.enable_orderline_note;
        },
    });
    Registries.Component.add(AllNoteButton);


    const ProductLineNote = (ProductScreen) =>
        class extends ProductScreen {
            constructor() {
                super(...arguments);
                useListener("click-note-icon", this.on_click_line_note_icon);
            }
            async on_click_line_note_icon(event) {
                if (this.env.pos.get_order().get_selected_orderline()) {
                    let { confirmed, payload } = this.showPopup("TemplateLineNotePopupWidget");
                    if (confirmed) {
                    } else {
                        return;
                    }
                } else {
                    alert("Please select the product !");
                }
            }
        };

    Registries.Component.extend(ProductScreen, ProductLineNote);



    return {
        GlobalNoteButton,
        AllNoteButton,
    };
});
