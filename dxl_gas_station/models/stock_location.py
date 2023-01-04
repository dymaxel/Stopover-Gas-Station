# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class StockLocation(models.Model):
    _inherit = 'stock.location'

    product_id = fields.Many2one('product.product', string="Product", domain="[('detailed_type', '=', 'product')]")
    is_tank = fields.Boolean('Is a Tank', copy=False)
    tank_code = fields.Char('Tank Code', copy=False)
    tank_name = fields.Char(string="Tank Name", compute='_compute_tank_name', store=True)
    loss_location_id = fields.Many2one('stock.location', domain="[('usage', '=', 'inventory'), ('company_id', '=', company_id)]", string="Loss Location")

    @api.onchange('is_tank')
    def _onchange_is_tank(self):
        self.product_id = False
        self.tank_code = ''

    @api.depends('tank_code', 'product_id', 'branch_id')
    def _compute_tank_name(self):
        for location in self:
            tank_name = ''
            if location.product_id:
                tank_name += location.product_id.name
            if location.tank_code:
                tank_name += ' - ' + location.tank_code
            if location.branch_id:
                tank_name += ' - ' + location.branch_id.name
            location.tank_name = tank_name
