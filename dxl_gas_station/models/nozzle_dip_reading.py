# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class NozzleDipReading(models.Model):
    _name = 'nozzle.dip.reading'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Nozzle Dip Reading'

    name = fields.Char(default='New', readonly=True, required=True, copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('submit', 'Submit'),
        ('posted', 'Posted'),
        ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')
    branch_id = fields.Many2one('res.branch', required=True, string="Branch", states={'posted': [('readonly', True)]})
    opening_date = fields.Datetime('Opening Date', states={'posted': [('readonly', True)]})
    closing_date = fields.Datetime('Closing Date', states={'posted': [('readonly', True)]})
    reading_lines = fields.One2many('nozzle.dip.reading.line', 'reading_id', states={'posted': [('readonly', True)]})

    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        lines = [(5, 0, 0)]
        if self.branch_id:
            nozzle_ids = self.env['tank.nozzle'].sudo().search([('branch_id', '=', self.branch_id.id), ('product_id', '!=', False)])
            for nozzle in nozzle_ids:
                lines.append((0, 0, {
                    'nozzle_id': nozzle.id,
                    'location_id': nozzle.location_id.id,
                }))
        self.reading_lines = lines

    @api.model
    def create(self, vals):
        if vals.get('name') == 'New' or 'name' not in vals:
            vals['name'] = self.env.ref('dxl_gas_station.nozzle_dip_reading_sequence').next_by_id()
        return super(NozzleDipReading, self).create(vals)

    def action_running(self):
        self.write({'state': 'running'})

    def action_validate(self):
        self.write({'state': 'submit'})

    def action_approve(self):
        self.write({'state': 'posted'})


class NozzleDipReadingLine(models.Model):
    _name = 'nozzle.dip.reading.line'
    _description = "Nozzle Dip Reading Line"

    reading_id = fields.Many2one('nozzle.dip.reading', required=True)
    nozzle_id = fields.Many2one('tank.nozzle', required=True)
    branch_id = fields.Many2one('res.branch', related="reading_id.branch_id")
    location_id = fields.Many2one('stock.location', required=True, string="Tanks")
    product_id = fields.Many2one('product.product', related="location_id.product_id", store=True)
    opening_reading = fields.Float('System Nozzle Opening Reading', compute="_compute_opening_reading")
    physical_reading = fields.Float('Physical Nozzle Closing')
    sale_qty = fields.Float('Sales', readonly=True, copy=False)
    closing_reading = fields.Float('System Nozzle Closing Reading', compute='_compute_closing_reading')
    variance = fields.Float('Variance', compute='_compute_variance')

    @api.depends('sale_qty', 'opening_reading')
    def _compute_closing_reading(self):
        for line in self:
            line.closing_reading = line.opening_reading + line.sale_qty

    @api.depends('closing_reading', 'physical_reading')
    def _compute_variance(self):
        for line in self:
            line.variance = line.closing_reading - line.physical_reading

    @api.depends('reading_id.opening_date', 'nozzle_id', 'location_id')
    def _compute_opening_reading(self):
        for line in self:
            last_reading_line = self.env['nozzle.dip.reading.line'].search([('nozzle_id', '=', line.nozzle_id.id), ('location_id', '=', line.location_id.id), ('reading_id.opening_date', '<', line.reading_id.opening_date), ('reading_id.state', '=', 'posted')], limit=1)
            if last_reading_line:
                line.opening_reading = last_reading_line.closing_reading
            else:
                line.opening_reading = 0.0

    @api.model
    def create(self, vals):
        res = super(NozzleDipReadingLine, self).create(vals)
        res._update_stock_out_data()
        return res

    @api.onchange('nozzle_id', 'location_id', 'reading_id.opening_date', 'reading_id.closing_date')
    def _onchange_nozzle_id(self):
        if self.nozzle_id and self.location_id:
            self._update_stock_out_data()

    def _update_stock_out_data(self):
        print('CA:::::::::::::::::')
        for line in self.filtered(lambda x: x.reading_id.state in ('draft', 'running')):
            sale_qty = 0.0
            if line.reading_id.opening_date and line.location_id:
                domain = [
                    ('date', '>=', line.reading_id.opening_date),
                    ('location_dest_id.usage', '=', 'customer'),
                    # ('location_dest_id.usage', '=', 'internal'),
                    # ('location_dest_id.branch_id', '=', branch_id),
                    ('location_id', '=', line.location_id.id),
                    ('state', '=', 'done'),
                    ('sale_line_id.nozzle_id', '=', line.nozzle_id.id),
                ]
                if line.reading_id.closing_date:
                    domain.append(('date', '<=', line.reading_id.closing_date))
                sale_moves = self.env['stock.move'].sudo().search(domain)
                sale_qty = sum(sale_moves.mapped('product_uom_qty'))
            line.write({'sale_qty': sale_qty})
