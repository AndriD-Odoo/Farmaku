from odoo.fields import Many2one
from odoo.exceptions import MissingError


def convert_to_read_new(self, value, record, use_name_get=True):
    if use_name_get and value:
        # evaluate name_get() as superuser, because the visibility of a
        # many2one field value (id and name) depends on the current record's
        # access rights, and not the value's access rights.
        try:
            # performance: value.sudo() prefetches the same records as value
            return value.id, value.display_name
            # return value.sudo().name_get()[0][1]
        except MissingError:
            # Should not happen, unless the foreign key is missing.
            return False, False
    else:
        return value.id, False


Many2one.convert_to_read_new = convert_to_read_new
