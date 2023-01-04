# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class StockMove(models.Model):
    _inherit = 'stock.move'

    tank_reading_id = fields.Many2one('tank.dip.reading', copy=False)

    def _action_done(self, cancel_backorder=False):
        res = super(StockMove, self)._action_done(cancel_backorder=cancel_backorder)
        tanks_tobe_update = self.env['tank.dip.reading.line'].search([('reading_id.state', 'in', ('draft', 'running'))])
        nozzle_tobe_update = self.env['nozzle.dip.reading.line'].search([('reading_id.state', 'in', ('draft', 'running'))])
        if tanks_tobe_update:
            tanks_tobe_update._update_stock_in_data()
            tanks_tobe_update._update_stock_out_data()
        if nozzle_tobe_update:
            nozzle_tobe_update._update_stock_out_data()
        return res
