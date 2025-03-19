import pytz
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil import parser
from odoo.tools import format_datetime
from odoo.addons.ms_rest_api.models.common import (
    _logger,
    success_response,
    error_response,
    authentication,
    check_mandatory_fields
)


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    def new_check_validity(self, employee_id, check_in, check_out):
        if isinstance(check_in, str):
            check_in = datetime.strptime(check_in, '%Y-%m-%d %H:%M:%S')
        if isinstance(check_out, str):
            check_out = datetime.strptime(check_out, '%Y-%m-%d %H:%M:%S')
        last_attendance_before_check_in = self.env['hr.attendance'].search([
            ('employee_id', '=', employee_id.id),
            ('check_in', '<=', check_in),
        ], order='check_in desc', limit=1)
        if last_attendance_before_check_in and last_attendance_before_check_in.check_out and last_attendance_before_check_in.check_out > check_in:
            raise ValidationError(
                _("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
                    'empl_name': employee_id.name,
                    'datetime': format_datetime(self.env, check_in, dt_format=False),
                })

        if not check_out:
            # if our attendance is "open" (no check_out), we verify there is no other "open" attendance
            no_check_out_attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', employee_id.id),
                ('check_out', '=', False),
            ], order='check_in desc', limit=1)
            if no_check_out_attendances:
                raise ValidationError(
                    _("Cannot create new attendance record for %(empl_name)s, the employee hasn't checked out since %(datetime)s") % {
                        'empl_name': employee_id.name,
                        'datetime': format_datetime(self.env, no_check_out_attendances.check_in, dt_format=False),
                    })
        else:
            # we verify that the latest attendance with check_in time before our check_out time
            # is the same as the one before our check_in time computed before, otherwise it overlaps
            last_attendance_before_check_out = self.env['hr.attendance'].search([
                ('employee_id', '=', employee_id.id),
                ('check_in', '<', check_out),
            ], order='check_in desc', limit=1)
            if last_attendance_before_check_out and last_attendance_before_check_in != last_attendance_before_check_out:
                raise ValidationError(
                    _("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
                        'empl_name': employee_id.name,
                        'datetime': format_datetime(self.env, last_attendance_before_check_out.check_in,
                                                    dt_format=False),
                    })

    def create_attendance(self, vals):
        try:
            user_tz = self.env.user.tz or 'Asia/Jakarta'
            attendance_ids = []
            failed = []
            for val in vals:
                reference_id = val.get('reference_id')
                try:
                    barcode = val.get('barcode')
                    employee_id = self.env['hr.employee'].search([
                        ('barcode', '=', barcode)
                    ], limit=1)
                    if not employee_id:
                        raise ValidationError(_(f'Employee with badge ID {barcode} not found.'))
                    check_in = val.get('check_in')
                    check_out = val.get('check_out')
                    if check_in:
                        check_in = parser.isoparse(check_in)
                        check_in = pytz.timezone(user_tz).localize(check_in).astimezone(pytz.UTC)
                        check_in = check_in.strftime('%Y-%m-%d %H:%M:%S')
                    if check_out:
                        check_out = parser.isoparse(check_out)
                        check_out = pytz.timezone(user_tz).localize(check_out).astimezone(pytz.UTC)
                        check_out = check_out.strftime('%Y-%m-%d %H:%M:%S')
                    self.new_check_validity(employee_id, check_in, check_out)
                    attendance_id = self.create({
                        'employee_id': employee_id.id,
                        'check_in': check_in,
                        'check_out': check_out,
                    })
                    attendance_ids.append(attendance_id.id)
                except Exception as e:
                    failed.append({
                        'reference_id': reference_id,
                        'reason': f"{e}",
                    })
        except Exception as e:
            return {
                "code": 400,
                "message": f"{e}",
            }
        return {
            "code": 200,
            "message": f"successfully ({len(attendance_ids)}), failed ({len(failed)})",
            "record_ids": attendance_ids,
            "failed_detail": failed,
        }

    def _create_missing_attendances(self):
        user_tz = self.env.user.tz or 'Asia/Jakarta'
        current_date = pytz.UTC.localize(datetime.now()).astimezone(pytz.timezone(user_tz))
        current_date = current_date.date()
        yesterday_date = current_date - timedelta(days=1)
        start_date = self.env.user.date2datetime(date2convert=yesterday_date, date_type='start_date', format='string')
        end_date = self.env.user.date2datetime(date2convert=yesterday_date, date_type='end_date', format='string')
        domain = [
            ('check_in', '>=', start_date),
            ('check_in', '<=', end_date),
        ]
        attendance_ids = self.env['hr.attendance'].search(domain)
        checked_employee_ids = attendance_ids.mapped('employee_id')
        employee_admin_id = self.env.ref('hr.employee_admin')
        employee_ids = self.env['hr.employee'].search([
            ('id', 'not in', checked_employee_ids.ids),
            ('id', '!=', employee_admin_id.id),
        ])
        for employee_id in employee_ids:
            self.create({
                'employee_id': employee_id.id,
                'check_in': start_date,
                'check_out': start_date,
            })
