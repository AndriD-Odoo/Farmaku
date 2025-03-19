# -*- coding: utf-8 -*-

from . import fmk_settlement
from . import inv_recap
from . import crm_team
# from . import config_settings

# def post_init_hook(cr, registry):
#     env = api.Environment(cr, 1, {})
#     sequence_format = env['ir.config_parameter'].sudo().get_param('farmaku.settlement.batch.sequence_format')

#     if sequence_format:
#         env['ir.sequence'].sudo().create({
#             'name': 'Settlement Batch Sequence',
#             'code': 'farmaku.settlement.batch.sequence',
#             'prefix': sequence_format,
#             'padding': 2,
#         })