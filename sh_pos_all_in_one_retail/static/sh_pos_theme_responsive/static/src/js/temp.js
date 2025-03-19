odoo.define("sh_pos_theme_responsive.temp", function (require) {
    "use strict";
    
		
	const PosComponent = require("point_of_sale.PosComponent");
	const { useListener } = require("web.custom_hooks");
    const Registries = require("point_of_sale.Registries");
    const ProductScreen = require("point_of_sale.ProductScreen");

    class AddSignatureButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener("click-add-signature", this.onClickTemplateLoad);
        }
        onClickTemplateLoad() {
        }
    }
    AddSignatureButton.template = "AddSignatureButton";
    ProductScreen.addControlButton({
        component: AddSignatureButton,
        condition: function () {
            return true;
        },
    });
    Registries.Component.add(AddSignatureButton);
    
    
    class AddSignatureButton1 extends PosComponent {
        constructor() {
            super(...arguments);
            useListener("click-add-signature", this.onClickTemplateLoad);
        }
        onClickTemplateLoad() {
        }
    }
    AddSignatureButton1.template = "AddSignatureButton1";
    ProductScreen.addControlButton({
        component: AddSignatureButton1,
        condition: function () {
            return true;
        },
    });
    Registries.Component.add(AddSignatureButton1);
    
    class AddSignatureButton2 extends PosComponent {
        constructor() {
            super(...arguments);
            useListener("click-add-signature", this.onClickTemplateLoad);
        }
        onClickTemplateLoad() {
        }
    }
    AddSignatureButton2.template = "AddSignatureButton2";
    ProductScreen.addControlButton({
        component: AddSignatureButton2,
        condition: function () {
            return true;
        },
    });
    Registries.Component.add(AddSignatureButton2);
    
    class AddSignatureButton3 extends PosComponent {
        constructor() {
            super(...arguments);
            useListener("click-add-signature", this.onClickTemplateLoad);
        }
        onClickTemplateLoad() {
        }
    }
    AddSignatureButton3.template = "AddSignatureButton3";
    ProductScreen.addControlButton({
        component: AddSignatureButton3,
        condition: function () {
            return true;
        },
    });
    Registries.Component.add(AddSignatureButton3);

    class AddSignatureButton4 extends PosComponent {
        constructor() {
            super(...arguments);
            useListener("click-add-signature", this.onClickTemplateLoad);
        }
        onClickTemplateLoad() {
        }
    }
    AddSignatureButton4.template = "AddSignatureButton4";
    ProductScreen.addControlButton({
        component: AddSignatureButton4,
        condition: function () {
            return true;
        },
    });
    Registries.Component.add(AddSignatureButton4);
    
    class AddSignatureButton5 extends PosComponent {
        constructor() {
            super(...arguments);
            useListener("click-add-signature", this.onClickTemplateLoad);
        }
        onClickTemplateLoad() {
        }
    }
    AddSignatureButton5.template = "AddSignatureButton5";
    ProductScreen.addControlButton({
        component: AddSignatureButton5,
        condition: function () {
            return true;
        },
    });
    Registries.Component.add(AddSignatureButton5);
    
    class AddSignatureButton6 extends PosComponent {
        constructor() {
            super(...arguments);
            useListener("click-add-signature", this.onClickTemplateLoad);
        }
        onClickTemplateLoad() {
        }
    }
    AddSignatureButton6.template = "AddSignatureButton6";
    ProductScreen.addControlButton({
        component: AddSignatureButton6,
        condition: function () {
            return true;
        },
    });
    Registries.Component.add(AddSignatureButton6);
    
    return {
        AddSignatureButton,
        AddSignatureButton1,
        AddSignatureButton2,
        AddSignatureButton3,
        AddSignatureButton4,
        AddSignatureButton5,
        AddSignatureButton6,
    };
	
});