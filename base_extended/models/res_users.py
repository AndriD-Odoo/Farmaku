from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

import pytz
import logging

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    def check_mandatory_fields(self, mandatory_fields, val):
        need_fields = []
        for mandatory_field in mandatory_fields:
            if not val.get(mandatory_field):
                need_fields.append(mandatory_field)
        if need_fields:
            raise ValidationError(_(f'Mandatory fields are not correctly set: {", ".join(need_fields)}'))

    def date2datetime(self, date2convert=False, date_type='start_date', format='string'):
        self.ensure_one()
        user_tz = self.env.user.tz or 'Asia/Jakarta'
        if not date2convert:
            date2convert = datetime.now().date()
        tz_diff = datetime.now(pytz.timezone(user_tz)).strftime('%z')
        tz_diff = int(tz_diff.replace('+', '').replace('0', ''))
        if type(date2convert) is not str:
            date2convert = date2convert.strftime('%Y-%m-%d')
        date2convert = datetime.strptime(date2convert + ' 00:00:00', '%Y-%m-%d %H:%M:%S')
        if date_type == 'start_date':
            date2convert = date2convert - timedelta(hours=tz_diff)
        else:
            date2convert = date2convert + timedelta(days=1)
            date2convert = date2convert - timedelta(hours=tz_diff)
        if format == 'string':
            date2convert = date2convert.strftime('%Y-%m-%d %H:%M:%S')
        return date2convert

    def datetime2date(self, current_datetime):
        if not current_datetime:
            return ''
        return pytz.UTC.localize(current_datetime).astimezone(pytz.timezone(self.env.user.tz or 'Asia/Jakarta')).date()
