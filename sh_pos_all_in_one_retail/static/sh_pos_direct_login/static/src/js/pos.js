odoo.define("sh_pos_direct_login.pos", function (require) {
    "use strict";

    var framework = require("web.framework");
    var models = require("point_of_sale.models");
    const Registries = require("point_of_sale.Registries");
    var core = require("web.core");
    const HeaderButton = require("point_of_sale.HeaderButton");

    models.load_fields("res.users", ["sh_is_direct_logout"]);

    const PosHeaderButton = (HeaderButton) =>
        class extends HeaderButton {
            onClick() {
                if (!this.confirmed) {
                    this.state.label = "Confirm";
                    this.confirmed = setTimeout(() => {
                        this.state.label = "Close";
                        this.confirmed = null;
                    }, 2000);
                } else {
                    if (this.env.pos.user && this.env.pos.user.sh_is_direct_logout) {
                        framework.redirect("/web/session/logout");
                    } else {
                        this.trigger("close-pos");
                    }
                }
            }
        };
    Registries.Component.extend(HeaderButton, PosHeaderButton);
});
