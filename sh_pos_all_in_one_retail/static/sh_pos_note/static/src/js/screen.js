odoo.define("sh_pos_note.screen", function (require) {
    "use strict";

    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");
    var core = require("web.core");
    const PaymentScreen = require("point_of_sale.PaymentScreen");
    const { useListener } = require("web.custom_hooks");
    const { parse } = require("web.field_utils");
    const { useErrorHandlers } = require("point_of_sale.custom_hooks");
    const NumberBuffer = require("point_of_sale.NumberBuffer");
    const { onChangeOrder } = require("point_of_sale.custom_hooks");

    const PosResPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            constructor() {
                super(...arguments);
            }
            async validateOrder(isForceValidate) {
                var self = this;
                if ($("#payment_note_textarea") && $("#payment_note_textarea")[0]) {
                    self.env.pos.get_order().set_global_note($("#payment_note_textarea")[0].value);
                }

                super.validateOrder(isForceValidate);
            }
        };
    Registries.Component.extend(PaymentScreen, PosResPaymentScreen);
    //    return PosResPaymentScreen;
    class AllNoteScreen extends PosComponent {
        constructor() {
            super(...arguments);
            var self = this;
            this.state = {
                query: null,
                selectedTemplate: this.props.template,
            };
            useErrorHandlers();
            useListener("save-changes", this.allpredfinenotecontents1);
            useListener("click-global-note", this.onClickTemplateLoad);
        }
        onClickTemplateLoad() {
            let { confirmed, payload } = this.showPopup("CreateNotePopupWidget");
            if (confirmed) {
            } else {
                return;
            }
        }
        mounted() {
            // call _tableLongpolling once then set interval of 5sec.
            this._noteLongpolling();
            setInterval(this._noteLongpolling.bind(this), 5000);
        }
        async _noteLongpolling() {
            if (this.state.isEditMode) {
                return;
            }
        }
        updateNoteList(event) {
            this.state.query = event.target.value;
            this.render();
        }
        async allpredfinenotecontents1() {
            var self = this;
            this.render();
        }
        get allpredfinenotecontents() {
            var self = this;
            if (this.state.query && this.state.query.trim() !== "") {
                var templates = this.get_note_by_name(this.state.query.trim());
                return templates;
            } else {
                return this.env.pos.db.all_note;
            }
        }
        get_note_by_name(name) {
            return _.filter(this.env.pos.db.all_note, function (template) {
                if (template["display_name"]) {
                    if (template["display_name"].indexOf(name) > -1) {
                        return true;
                    } else {
                        return false;
                    }
                }
            });
        }
        back() {
            this.trigger("close-temp-screen");
        }
    }
    AllNoteScreen.template = "AllNoteScreen";
    Registries.Component.add(AllNoteScreen);

    class TemplatePreDefineNoteLine extends PosComponent {
        constructor() {
            super(...arguments);

            this.state = {
                detailIsShown: true,
            };
        }

        get_order_by_uid(uid) {
            var orders = this.env.pos.get_order_list();
            for (var i = 0; i < orders.length; i++) {
                if (orders[i].uid === uid) {
                    return orders[i];
                }
            }
            return undefined;
        }
        async edit_note(event) {
            var self = this;
            var note_id = $(event.currentTarget).data("id");
            $(event.currentTarget).closest("tr").find(".input_name")[0].classList.add("show_input_name");
            $(event.currentTarget).closest("tr").find(".note_name")[0].classList.add("hide_note_name");
            self.state.detailIsShown = false;
            this.trigger("save-changes");
        }

        async delete_note(event) {
            var self = this;
            var note_id = $(event.currentTarget).data("id");
            var note = self.env.pos.db.note_by_uid[note_id];

            if (note_id) {
                var offline_removed_notes = self.env.pos.db.get_removed_notes();
                offline_removed_notes.push(note);
                self.env.pos.db.save("removed_notes", offline_removed_notes);

                self.env.pos.db.remove_note_by_uid(note_id);

                try {
                    self.env.pos.delete_notes();
                } catch (error) {
                    if (error instanceof Error) {
                        throw error;
                    } else {
                        self.env.pos.set_synch(self.env.pos.get("failed") ? "error" : "disconnected");
                        self._handlePushOrderError(error);
                    }
                }
            }

            this.trigger("save-changes");
        }

        async save_note(event) {
            var self = this;
            var new_note_list = [];
            var note_id = $(event.currentTarget).data("id");
            var all_note = this.env.pos.db.all_note;
            _.each(all_note, function (each_note) {
                if (each_note.uid == note_id) {
                    if ($(event.currentTarget).closest("tr").find(".input_tag_name")[0].value) {
                        each_note["name"] = $(event.currentTarget).closest("tr").find(".input_tag_name")[0].value;
                        each_note["display_name"] = $(event.currentTarget).closest("tr").find(".input_tag_name")[0].value;
                    } /*else{
                		alert("Please write new Note name")
                		return
                	}*/
                }
            });
            $(event.currentTarget).closest("tr").find(".input_name")[0].classList.remove("show_input_name");
            $(event.currentTarget).closest("tr").find(".note_name")[0].classList.remove("hide_note_name");
            self.state.detailIsShown = true;
            if (note_id) {
                var note = self.env.pos.db.note_by_uid[note_id];
                var offline_notes = self.env.pos.db.get_notes();
                offline_notes.push(note);
                self.env.pos.db.save("notes", offline_notes);

                try {
                    self.env.pos.load_new_notes();
                } catch (error) {
                    if (error instanceof Error) {
                        throw error;
                    } else {
                        self.env.pos.set_synch(self.env.pos.get("failed") ? "error" : "disconnected");
                        self._handlePushOrderError(error);
                    }
                }
            }

            this.trigger("save-changes");
        }
    }
    TemplatePreDefineNoteLine.template = "TemplatePreDefineNoteLine";
    Registries.Component.add(TemplatePreDefineNoteLine);

    return {
        AllNoteScreen,
        TemplatePreDefineNoteLine,
        PosResPaymentScreen,
    };
});
