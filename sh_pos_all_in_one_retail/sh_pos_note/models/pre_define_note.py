# Copyright (C) Softhealer Technologies.
from odoo import fields, models, api


class PreDefineNote(models.Model):
    _name = 'pre.define.note'
    _description = 'Pre Define Note'

    name = fields.Char('Note')
    sequence_number = fields.Integer(
        string='Sequence Number', help='A session-unique sequence number for the order', default=1)
    uid = fields.Char(string='Number')

    @api.model
    def create(self, vals):
        if not vals.get('uid'):
            vals.update(
                {'uid': self.env['ir.sequence'].next_by_code('sh.pos.note')})
        return super(PreDefineNote, self).create(vals)

    @api.model
    def remove_from_ui(self, notes):
        if notes:
            for note in notes:
                if note:
                    note_id = note.get('uid', False)
                    if note_id:  # Modifying existing note
                        note_rec = self.search([('uid', '=', str(note_id))])
                        note_rec.unlink()
        return

    @api.model
    def create_from_ui(self, notes):
        if notes:
            # image is a dataurl, get the data after the comma
            for note in notes:
                if note:
                    note_id = note.get('uid', False)
                    if note_id:  # Modifying existing note
                        note_rec = self.search([('uid', '=', str(note_id))])
                        if note_rec:
                            note_rec.write(note)
                        else:
                            note_id = self.create(note).id
                    else:
                        note_id = self.create(note).id
                    return note_id
