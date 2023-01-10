# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_type = fields.Selection([('credit', 'Credit'), ('cash', 'Cash')], default='cash')
    vehicle_number = fields.Char('Vehicle Number', copy=False)
    driver_name = fields.Char('Driver Name', copy=False)
    driver_mobile_no = fields.Char('Driver Mobile Number', copy=False)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    nozzle_id = fields.Many2one('tank.nozzle')
    opening_qty = fields.Float('Opening Quantity')
    salesperson_id = fields.Many2one('res.users', string="Nozzle Sales Person")

    @api.onchange('nozzle_id')
    def _onchange_nozzle_id(self):
        if self.nozzle_id and self.nozzle_id.product_id:
            self.product_id = self.nozzle_id.product_id.id
            nozzle_line = self.env['nozzle.dip.reading.line'].search([('reading_id.date', '=', fields.Date.today()), ('nozzle_id', '=', self.nozzle_id.id), ('salesperson_id', '!=', False)], limit=1)
            if nozzle_line:
                self.salesperson_id = nozzle_line.salesperson_id.id
        else:
            self.product_id = False
