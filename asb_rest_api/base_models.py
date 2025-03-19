from odoo.models import BaseModel
from odoo.exceptions import MissingError
from odoo.fields import Many2one
import logging


_logger = logging.getLogger(__name__)


def read_new(self, fields=None):
    # check access rights
    self.check_access_rights('read')
    fields = self.check_field_access_rights('read', fields)

    # split fields into stored and computed fields
    stored, inherited, computed = [], [], []
    for name in fields:
        field = self._fields.get(name)
        if field:
            if field.store:
                stored.append(name)
            elif field.base_field.store:
                inherited.append(name)
            else:
                computed.append(name)
        else:
            _logger.warning(
                "%s.read() with unknown field '%s'", self._name, name)

    # fetch stored fields from the database to the cache; this should feed
    # the prefetching of secondary records
    self._read_from_database(stored, inherited)

    # retrieve results from records; this takes values from the cache and
    # computes remaining fields
    result = []
    name_fields = [(name, self._fields[name])
                   for name in (stored + inherited + computed)]
    for record in self:
        try:
            values = {'id': record.id}
            for name, field in name_fields:
                if isinstance(field, Many2one):
                    values[name], values[name +
                                         "_name"] = field.convert_to_read_new(record[name], record, True)
                else:
                    values[name] = field.convert_to_read(
                        record[name], record, True)
            result.append(values)
        except MissingError:
            pass

    return result


BaseModel.read_new = read_new
