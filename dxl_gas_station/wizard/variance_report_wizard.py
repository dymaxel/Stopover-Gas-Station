# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class VarianceReportWizard(models.TransientModel):
    _name = 'variance.report.wizard'
    _description = 'Variance Report wizard'

    start_at = fields.Date(string='From Date', required=True)
    stop_at = fields.Date(string="To Date", required=True)
    branch_id = fields.Many2one('res.branch', string="Branch", required=True)
    product_ids = fields.Many2many('product.product', string="Product", domain=[('detailed_type', '=', 'product')], required=True)

    def _get_date_list(self):
        from datetime import datetime, timedelta
        delta = self.stop_at - self.start_at
        return [self.start_at + timedelta(days=i) for i in range(delta.days + 1)]

    def print_pdf_report(self):
        if self.start_at > self.stop_at:
            raise ValidationError(_('Invalid date !'))
        data = {
            'start_at': self.start_at,
            'stop_at': self.stop_at,
            'branch_id': self.branch_id.id,
            'product_ids': self.product_ids.ids,
        }
        return self.env.ref('dxl_gas_station.variance_report').report_action(self, data=data)


class QualitySheetReport(models.AbstractModel):
    _name = 'report.dxl_gas_station.variance_report_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        date_from = data['start_at']
        date_to = data['stop_at']
        date_list = docs._get_date_list()
        branch = self.env['res.branch'].browse(data['branch_id'])
        product_ids = self.env['product.product'].browse(data['product_ids'])
        product_wise_data = {}
        for product in product_ids:
            report_data = []
            for date in date_list:
                adj_out_moves = self.env['stock.move'].search([('date', '=', date), ('product_id', '=', product.id), ('state', '=', 'done'), ('location_id.usage', '=', 'internal'), ('location_dest_id.usage', '=', 'inventory')])
                adj_in_moves = self.env['stock.move'].search([('date', '=', date), ('product_id', '=', product.id), ('state', '=', 'done'), ('location_dest_id.usage', '=', 'internal'), ('location_id.usage', '=', 'inventory')])
                adj_qty = sum(adj_in_moves.mapped('quantity_done')) - sum(adj_out_moves.mapped('quantity_done'))
                reading_line = self.env['tank.dip.reading.line'].sudo().search([
                    ('reading_id.date', '=', date),
                    ('reading_id.state', '=', 'posted'),
                    ('reading_id.branch_id', '=', branch.id),
                    ('product_id', '=', product.id)
                ], limit=1)
                meter_reading_line = self.env['nozzle.dip.reading.line'].sudo().search([
                    ('reading_id.date', '=', date),
                    ('reading_id.state', '=', 'posted'),
                    ('reading_id.branch_id', '=', branch.id),
                    ('product_id', '=', product.id)
                ], limit=1)
                if reading_line:
                    onhand = reading_line.previous_stock_qty + reading_line.purchase_qty - reading_line.sale_qty + adj_qty
                    report_data.append({
                        'date': date.strftime("%d-%b-%Y"),
                        'location': reading_line.location_id.display_name,
                        'product': product.name,
                        'opening_stock': reading_line.previous_stock_qty,
                        'purchase': reading_line.purchase_qty,
                        'sale': reading_line.sale_qty,
                        'dip_reading': reading_line.dip_reading_gal,
                        'meter_reading': sum(meter_reading_line.mapped('variance')),
                        'adjustment': adj_qty,
                        'onhand': onhand
                    })
            product_wise_data[product.id] = report_data

        return {
            'docs': docs,
            'date_from': date_from,
            'date_to': date_to,
            'branch': branch.name,
            'product_wise_data': product_wise_data,
            'product_ids': product_ids.ids,
        }
