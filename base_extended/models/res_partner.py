import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _display_address(self, without_company=False):
        res = super(ResPartner, self)._display_address(without_company=without_company)
        _logger.info(f'\nwithout_company: {without_company}')
        _logger.info(f'\ndisplay_address: {res}')
        # split address setiap 35 karakter
        splitted_res = res.split('\n')
        res_list = []
        if self.ref_company_ids:
            for res_part in splitted_res:
                final_res_part = res_part
                if len(res_part) > 35:
                    res_part_space_list = res_part.split(' ')
                    res_part_space_count = 0
                    part_1 = []
                    part_2 = []
                    for res_part_space in res_part_space_list:
                        if res_part_space_count <= 35:
                            part_1.append(res_part_space)
                            res_part_space_count += (len(res_part_space) + 1)  # +1 untuk spasi
                        else:
                            part_2.append(res_part_space)
                    part_1 = ' '.join(part_1)
                    part_2 = ' '.join(part_2)
                    final_res_part = f'{part_1}\n{part_2}'
                res_list.append(final_res_part)
            res = '\n'.join(res_list)
        _logger.info(f'\nfinal address: {res}')
        return res

    sia = fields.Char(
        string='SIA',
        required=False)
    pbf_permit_number = fields.Char(
        string='Nomor Izin PBF',
        required=False)
    cdob = fields.Char(
        string='No CDOB',
        required=False)
