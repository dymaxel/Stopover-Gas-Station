# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class NozzleSalesperson(models.Model):
    _name = 'nozzle.salesperson'
    _rec_name = 'branch_id'
    _description = 'Nozzle Sales Person'

    branch_id = fields.Many2one('res.branch', required=True, string="Branch")
    line_ids = fields.One2many('nozzle.salesperson.line', 'nozzle_salesperson_id')

    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        line_ids = [(5, 0, 0)]
        if self.branch_id:
            nozzle_ids = self.env['tank.nozzle'].search([('branch_id', '=', self.branch_id.id)])
            for nozzle in nozzle_ids:
                line_ids.append((0, 0, {
                    'nozzle_id': nozzle.id,
                }))
        self.line_ids = line_ids


class NozzleSalespersonLine(models.Model):
    _name = 'nozzle.salesperson.line'
    _description = 'Nozzle Salesperson Lines'

    nozzle_salesperson_id = fields.Many2one('nozzle.salesperson', required=True)
    branch_id = fields.Many2one('res.branch', related="nozzle_salesperson_id.branch_id", store=True)
    nozzle_id = fields.Many2one('tank.nozzle', required=True, string="Nozzle")
    salesperson_id = fields.Many2one('res.users', string="Sales Person")
