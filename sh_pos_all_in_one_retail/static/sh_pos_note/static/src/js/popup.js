odoo.define("sh_pos_note.Popup", function (require) {
    "use strict";

    const Registries = require("point_of_sale.Registries");
    const AbstractAwaitablePopup = require("point_of_sale.AbstractAwaitablePopup");

    class TemplateLineNotePopupWidget extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
        }
        async confirm() {
            var self = this;
            this.props.resolve({ confirmed: true, payload: await this.getPayload() });
            this.env.pos.get_order().get_selected_orderline().set_line_note($("#textarea_note").val());
            this.trigger("close-popup");
            if ($("#store_checkbox")[0].checked) {
                var value = $("#textarea_note").val();
                var added_note = $("#textarea_note").val().split(",");
                _.each(added_note, function (each_added_note) {
                    if (!self.env.pos.all_note_name.includes(each_added_note)) {
                        var currentNote = self.env.pos.get_note();
                        self.env.pos.add_new_note();
                        var currentNote = self.env.pos.get_note();
                        currentNote.set_name(each_added_note);

                        var all_note = self.env.pos.db.all_note;
                        self.env.pos.db.remove_all_notes();
                        all_note.push(currentNote.export_as_JSON());
                        self.env.pos.db.add_notes(all_note);

                        var offline_notes = self.env.pos.db.get_notes();
                        offline_notes.push(currentNote.export_as_JSON());
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
                });
            }
        }
        async click_line_note_button(event) {
            var added_note;

            // pre define note
            var value = $(event.currentTarget).data("value");
            if ($(event.currentTarget).hasClass("selected")) {
                $(event.currentTarget).removeClass("selected");
                added_note = $("#textarea_note")[0].value.split(",");
                for (var i = 0; i < added_note.length; i++) {
                    if (added_note[i] == value) {
                        added_note.splice(i, 1);
                    }
                }
                if (added_note.length > 0) {
                    if (added_note.length == 1) {
                        $("#textarea_note").val(added_note[0]);
                    } else {
                        var new_line_note = "";
                        var added_note_length = added_note.length;
                        for (var i = 0; i < added_note.length; i++) {
                            if (i + 1 == added_note_length) {
                                new_line_note += added_note[i];
                            } else {
                                new_line_note += added_note[i] + ",";
                            }
                        }

                        $("#textarea_note").val(new_line_note);
                    }
                } else {
                    $("#textarea_note").val("");
                }
            } else {
                $(event.currentTarget).addClass("selected");
                if ($("#textarea_note").val()) {
                    $("#textarea_note").val($("#textarea_note").val() + "," + value);
                } else {
                    $("#textarea_note").val(value);
                }
            }
            //finish
        }
    }

    TemplateLineNotePopupWidget.template = "TemplateLineNotePopupWidget";
    Registries.Component.add(TemplateLineNotePopupWidget);

    class TemplateGlobalNotePopupWidget extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
        }
        async confirm() {
            var self = this;
            this.props.resolve({ confirmed: true, payload: await this.getPayload() });
            this.trigger("close-popup");
            var value = $("#textarea_note").val();
            this.env.pos.get_order().set_global_note(value);
            if ($("#store_checkbox")[0].checked) {
                var value = $("#textarea_note").val();
                var added_note = $("#textarea_note").val().split(",");
                _.each(added_note, function (each_added_note) {
                    if (!self.env.pos.all_note_name.includes(each_added_note)) {
                        var currentNote = self.env.pos.get_note();
                        self.env.pos.add_new_note();
                        var currentNote = self.env.pos.get_note();
                        currentNote.set_name(each_added_note);

                        var all_note = self.env.pos.db.all_note;
                        self.env.pos.db.remove_all_notes();
                        all_note.push(currentNote.export_as_JSON());
                        self.env.pos.db.add_notes(all_note);

                        var offline_notes = self.env.pos.db.get_notes();
                        offline_notes.push(currentNote.export_as_JSON());
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
                });
            }
        }

        async click_global_note_button(event) {
            var added_note;
            var value = $(event.currentTarget).data("value");
            if ($(event.currentTarget).hasClass("selected")) {
                $(event.currentTarget).removeClass("selected");
                added_note = $("#textarea_note")[0].value.split(",");
                for (var i = 0; i < added_note.length; i++) {
                    if (added_note[i] == value) {
                        added_note.splice(i, 1);
                    }
                }
                if (added_note.length > 0) {
                    if (added_note.length == 1) {
                        $("#textarea_note").val(added_note[0]);
                    } else {
                        var new_line_note = "";
                        var added_note_length = added_note.length;
                        for (var i = 0; i < added_note.length; i++) {
                            if (i + 1 == added_note_length) {
                                new_line_note += added_note[i];
                            } else {
                                new_line_note += added_note[i] + ",";
                            }
                        }

                        $("#textarea_note").val(new_line_note);
                    }
                } else {
                    $("#textarea_note").val("");
                }
            } else {
                $(event.currentTarget).addClass("selected");
                if ($("#textarea_note").val()) {
                    $("#textarea_note").val($("#textarea_note").val() + "," + value);
                } else {
                    $("#textarea_note").val(value);
                }
            }
        }
    }

    TemplateGlobalNotePopupWidget.template = "TemplateGlobalNotePopupWidget";
    Registries.Component.add(TemplateGlobalNotePopupWidget);

    class CreateNotePopupWidget extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
        }
        async confirm() {
            var self = this;
            this.props.resolve({ confirmed: true, payload: await this.getPayload() });
            var value = $("#textarea_note").val();
            if (value) {
                this.trigger("close-popup");

                var each_added_note = $("#textarea_note").val();

                var currentNote = self.env.pos.get_note();
                self.env.pos.add_new_note();
                var currentNote = self.env.pos.get_note();
                currentNote.set_name(each_added_note);

                var all_note = self.env.pos.db.all_note;
                self.env.pos.db.remove_all_notes();
                all_note.push(currentNote.export_as_JSON());
                self.env.pos.db.add_notes(all_note);

                var offline_notes = self.env.pos.db.get_notes();
                offline_notes.push(currentNote.export_as_JSON());
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
            } else {
                alert("Name should not be Blank.");
                $("#textarea_note")[0].classList.add("name_not_valid");
            }
        }
    }

    CreateNotePopupWidget.template = "CreateNotePopupWidget";
    Registries.Component.add(CreateNotePopupWidget);

    return {
        TemplateLineNotePopupWidget,
        TemplateGlobalNotePopupWidget,
        CreateNotePopupWidget,
    };
});
