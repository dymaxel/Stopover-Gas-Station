# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class TankNozzle(models.Model):
    _name = 'tank.nozzle'
    _description = 'Tank Nozzle'

    name = fields.Char(required=True, copy=False)
    location_id = fields.Many2one('stock.location', string="Tank Name", domain="[('is_tank', '=', True), ('branch_id', '!=', False), ('product_id', '!=', False)]")
    tank_code = fields.Char('Tank Code', related='location_id.tank_code')
    branch_id = fields.Many2one('res.branch', related="location_id.branch_id", string="Branch")
    product_id = fields.Many2one('product.product', related="location_id.product_id")
    tank_name = fields.Char('Tank Name', related="location_id.tank_name")
