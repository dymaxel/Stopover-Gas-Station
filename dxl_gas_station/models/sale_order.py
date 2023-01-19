# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_type = fields.Selection([('credit', 'Credit'), ('cash', 'Cash')], default='cash')
    vehicle_number = fields.Char('Vehicle Number', copy=False)
    driver_name = fields.Char('Driver Name', copy=False)
    driver_mobile_no = fields.Char('Driver Mobile Number', copy=False)

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for sale in self.filtered(lambda x: x.company_id.auto_invoice):
            # Force done delivery - dawaai
            for picking in sale.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel')):
                for move in picking.move_lines:
                    move.write({'quantity_done': move.product_uom_qty})
                picking.button_validate()

            # Create Customer Invoice on sale confirm
            invoice = sale._create_invoices()
            invoice.action_post()
        return res

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    nozzle_id = fields.Many2one('tank.nozzle')
    dispenser_id = fields.Many2one('nozzle.dispenser', string="Pump", related="nozzle_id.dispenser_id", store=True)
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
