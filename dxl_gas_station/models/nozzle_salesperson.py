# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class NozzleSalesperson(models.Model):
    _name = 'nozzle.salesperson'
    _rec_name = 'branch_id'
    _description = 'Nozzle Sales Person'

    branch_id = fields.Many2one('res.branch', required=True, string="Branch")
    line_ids = fields.One2many('nozzle.salesperson.line', 'nozzle_salesperson_id')


class NozzleSalespersonLine(models.Model):
    _name = 'nozzle.salesperson.line'
    _description = 'Nozzle Salesperson Lines'

    nozzle_salesperson_id = fields.Many2one('nozzle.salesperson', required=True)
    branch_id = fields.Many2one('res.branch', related="nozzle_salesperson_id.branch_id", store=True)
    nozzle_id = fields.Many2one('tank.nozzle', required=True, string="Nozzle")
    salesperson_id = fields.Many2one('res.users', required=True, string="Sales Person")
