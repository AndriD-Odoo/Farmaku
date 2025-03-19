odoo.define("sh_pos_theme_responsive.models", function (require) {
	
	var models = require("point_of_sale.models");

    models.load_models({
        model: "sh.pos.theme.settings",
        loaded: function (self, pos_theme_settings) {
            self.pos_theme_settings_data = [];
            self.pos_theme_settings_data = pos_theme_settings;
        },
    });
});
