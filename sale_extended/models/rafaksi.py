from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.osv import expression


class Rafaksi(models.Model):
    _name = "rafaksi"
    _description = "Rafaksi"
    _order = "real_write_date desc, start_date, name, product_id, team_ids"

    name = fields.Char(
        string='Program Name',
        required=True
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True)
    subsidy_amount = fields.Float(
        string='Rafaksi Amount',
        required=False)
    quota = fields.Integer(
        string='Quota',
        default=0,
        required=True)
    current_quota = fields.Integer(
        string='Current Quota',
        default=0,
        required=False)
    start_date = fields.Date(
        string='Start Date',
        required=False)
    end_date = fields.Date(
        string='End Date',
        required=False)
    team_ids = fields.Many2many(
        comodel_name='crm.team',
        string='Sales Team IDS',
        required=False)
    exclude_team_ids = fields.Many2many(
        comodel_name='crm.team',
        relation="rafaksi_exclude_crm_team_rel",
        column1="rafaksi_id",
        column2="team_id",
        string='Exclude Sales Team IDS',
        required=False)
    real_write_date = fields.Datetime(
        string='Last Updated on (Real)',
        default=fields.Datetime.now(),
        readonly=True,
        copy=False)
    real_write_uid = fields.Many2one(
        comodel_name='res.users',
        string='Last Updated by (Real)',
        default=lambda self: self.env.user.id,
        readonly=True,
        copy=False)
    active = fields.Boolean(
        string='Active',
        default=True,
        copy=False)
    teams = fields.Char(
        string='Sales Team',
        required=False)
    exclude_teams = fields.Char(
        string='Exclude Sales Team',
        required=False)

    def add_same_teams(self, team_vals):
        if not team_vals:
            return team_vals
        team_vals_final = []
        team_obj = self.env['crm.team'].sudo()
        for val in team_vals:
            if val:
                if val[0] == 6:
                    if val[2]:
                        team_ids = team_obj.browse(val[2])
                        all_team_ids = team_ids.search([
                            ('name', 'in', team_ids.mapped('name'))
                        ])
                        team_vals_final.append([6, False, all_team_ids.ids])
                    else:
                        team_vals_final.append([6, False, []])
        return team_vals_final

    @api.model
    def create(self, vals):
        print('\n vals', vals)
        if 'teams' in vals:
            if not vals.get('teams'):
                vals['team_ids'] = [[6, False, []]]
            else:
                teams_list = vals['teams'].split(',')
                team_domain = []
                for team_name in teams_list:
                    team_domain = expression.OR([team_domain, [('name', 'ilike', team_name)]])
                team_ids = self.env['crm.team'].sudo().search(team_domain)
                vals['team_ids'] = [[6, False, team_ids.ids]]
        if 'exclude_teams' in vals:
            if not vals.get('exclude_teams'):
                vals['exclude_team_ids'] = [[6, False, []]]
            else:
                teams_list = vals['exclude_teams'].split(',')
                team_domain = []
                for team_name in teams_list:
                    team_domain = expression.OR([team_domain, [('name', 'ilike', team_name)]])
                team_ids = self.env['crm.team'].sudo().search(team_domain)
                vals['exclude_team_ids'] = [[6, False, team_ids.ids]]
        vals['team_ids'] = self.add_same_teams(vals.get('team_ids', []))
        vals['exclude_team_ids'] = self.add_same_teams(vals.get('exclude_team_ids', []))
        res = super(Rafaksi, self).create(vals)
        return res

    def write(self, vals):
        print('\n vals', vals)
        if 'teams' in vals:
            if not vals.get('teams'):
                vals['team_ids'] = [[6, False, []]]
            else:
                teams_list = vals['teams'].split(',')
                team_domain = []
                for team_name in teams_list:
                    team_domain = expression.OR([team_domain, [('name', 'ilike', team_name)]])
                team_ids = self.env['crm.team'].sudo().search(team_domain)
                vals['team_ids'] = [[6, False, team_ids.ids]]
        if 'exclude_teams' in vals:
            if not vals.get('exclude_teams'):
                vals['exclude_team_ids'] = [[6, False, []]]
            else:
                teams_list = vals['exclude_teams'].split(',')
                team_domain = []
                for team_name in teams_list:
                    team_domain = expression.OR([team_domain, [('name', 'ilike', team_name)]])
                team_ids = self.env['crm.team'].sudo().search(team_domain)
                vals['exclude_team_ids'] = [[6, False, team_ids.ids]]
        if vals.get('team_ids'):
            team_ids = vals['team_ids'][0][2]
            prev_team_ids = self.sudo().mapped('team_ids')
            current_team_ids = self.env['crm.team'].sudo().search([
                ('id', 'in', team_ids)
            ])
            removed_team_ids = self.env['crm.team'].sudo().search([
                ('id', 'in', prev_team_ids.ids),
                ('id', 'not in', current_team_ids.ids),
            ])
            removed_team_ids = self.env['crm.team'].sudo().search([
                ('name', 'in', removed_team_ids.mapped('name')),
            ])
            final_team_ids = self.env['crm.team'].sudo().search([
                ('id', 'in', current_team_ids.ids),
                ('id', 'not in', removed_team_ids.ids),
            ])
            vals['team_ids'] = [[6, False, final_team_ids.ids]]
            vals['team_ids'] = self.add_same_teams(vals['team_ids'])
        if vals.get('exclude_team_ids'):
            exclude_team_ids = vals['exclude_team_ids'][0][2]
            prev_exclude_team_ids = self.sudo().mapped('exclude_team_ids')
            current_exclude_team_ids = self.env['crm.team'].sudo().search([
                ('id', 'in', exclude_team_ids)
            ])
            removed_exclude_team_ids = self.env['crm.team'].sudo().search([
                ('id', 'in', prev_exclude_team_ids.ids),
                ('id', 'not in', current_exclude_team_ids.ids),
            ])
            removed_exclude_team_ids = self.env['crm.team'].sudo().search([
                ('name', 'in', removed_exclude_team_ids.mapped('name')),
            ])
            final_exclude_team_ids = self.env['crm.team'].sudo().search([
                ('id', 'in', current_exclude_team_ids.ids),
                ('id', 'not in', removed_exclude_team_ids.ids),
            ])
            vals['exclude_team_ids'] = [[6, False, final_exclude_team_ids.ids]]
            vals['exclude_team_ids'] = self.add_same_teams(vals['exclude_team_ids'])
        res = super(Rafaksi, self).write(vals)
        if 'current_quota' not in vals and not self.env.context.get('skip_update'):
            context = self.env.context.copy()
            context['skip_update'] = True
            self.with_context(context).write({
                'real_write_date': fields.Datetime.now(),
                'real_write_uid': self.env.user.id,
            })
        return res

    def action_view_detail(self):
        self.ensure_one()
        return {
            'name': self.display_name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'rafaksi',
            'res_id': self.id,
        }
