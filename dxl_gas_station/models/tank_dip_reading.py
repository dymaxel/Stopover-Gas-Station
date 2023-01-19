# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
from odoo.exceptions import UserError, ValidationError


class TankDipReading(models.Model):
    _name = 'tank.dip.reading'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Tank Dip Reading'

    name = fields.Char(default='New', readonly=True, required=True, copy=False)
    date = fields.Date('Date', required=True, default=fields.Date.context_today, states={'posted': [('submit', True)], 'posted': [('readonly', True)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('submit', 'Submit'),
        ('posted', 'Posted'),
        ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')
    branch_id = fields.Many2one('res.branch', required=True, string="Branch", states={'posted': [('readonly', True)]})
    reading_lines = fields.One2many('tank.dip.reading.line', 'reading_id', states={'posted': [('readonly', True)]})
    sale_order_count = fields.Integer(string="Sale Orders", compute="_compute_sale_order_count")
    purchase_order_count = fields.Integer(string="Purchase Orders", compute="_compute_purchase_order_count")
    sale_order_ids = fields.Many2many('sale.order', compute="_compute_sale_order_ids")
    purchase_order_ids = fields.Many2many('purchase.order', compute="_compute_purchase_order_ids")
    loss_entry_count = fields.Integer(compute="_compute_loss_entry_count")
    loss_move_ids = fields.Many2many('account.move', compute="_compute_loss_move_ids")

    def _compute_loss_move_ids(self):
        for reading in self:
            reading.loss_move_ids = self.env['account.move'].search([('stock_move_id.tank_reading_id', '=', reading.id)]).ids

    def _compute_loss_entry_count(self):
        for reading in self:
            reading.loss_entry_count = len(reading.loss_move_ids)

    def action_view_loss_entry(self):
        action = {
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'name': _("Journal Entries"),
            'domain': [('id', 'in', self.loss_move_ids.ids)],
            'view_mode': 'tree,form',
        }
        return action

    @api.constrains('date', 'branch_id')
    def _check_duplicate_reading(self):
        if self.env['tank.dip.reading'].search_count([('branch_id', '=', self.branch_id.id), ('date', '=', self.date)]) > 1:
            raise ValidationError(_('You cannot create more than one reading of same branch and date.'))

    def _compute_purchase_order_ids(self):
        for reading in self:
            purchase_order_ids = []
            if reading.date:
                start_at = self.env['tank.dip.reading.line'].convert_to_server_time(reading.date.strftime('%Y-%m-%d') + ' 00:00:00')
                stop_at = self.env['tank.dip.reading.line'].convert_to_server_time(reading.date.strftime('%Y-%m-%d') + ' 23:59:59')
                domain = [
                    ('date', '>=', start_at),
                    ('date', '<=', stop_at),
                    ('location_id.usage', '=', 'supplier'),
                    ('location_dest_id', 'in', reading.reading_lines.mapped('location_id').ids),
                    ('state', '=', 'done'),
                    ('purchase_line_id', '!=', False),
                ]
                purchase_moves = self.env['stock.move'].sudo().search(domain)
                purchase_order_ids = purchase_moves.mapped('purchase_line_id.order_id')
            reading.purchase_order_ids = purchase_order_ids

    def _compute_sale_order_ids(self):
        for reading in self:
            sale_order_ids = []
            if reading.date:
                start_at = self.env['tank.dip.reading.line'].convert_to_server_time(reading.date.strftime('%Y-%m-%d') + ' 00:00:00')
                stop_at = self.env['tank.dip.reading.line'].convert_to_server_time(reading.date.strftime('%Y-%m-%d') + ' 23:59:59')
                domain = [
                    ('date', '>=', start_at),
                    ('date', '<=', stop_at),
                    ('location_dest_id.usage', '=', 'customer'),
                    ('location_id', 'in', reading.reading_lines.mapped('location_id').ids),
                    ('state', '=', 'done'),
                    ('sale_line_id', '!=', False),
                ]
                sale_moves = self.env['stock.move'].sudo().search(domain)
                sale_order_ids = sale_moves.mapped('sale_line_id.order_id')
            reading.sale_order_ids = sale_order_ids

    def _compute_purchase_order_count(self):
        for reading in self:
            reading.purchase_order_count = len(reading.purchase_order_ids)

    def _compute_sale_order_count(self):
        for reading in self:
            reading.sale_order_count = len(reading.sale_order_ids)

    def action_view_purchase_orders(self):
        action = {
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'name': _("Purchase Orders"),
            'domain': [('id', 'in', self.purchase_order_ids.ids)],
            'view_mode': 'tree,form',
        }
        return action

    def action_view_sale_orders(self):
        action = {
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'name': _("Sale Orders"),
            'domain': [('id', 'in', self.sale_order_ids.ids)],
            'view_mode': 'tree,form',
        }
        return action

    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        lines = [(5, 0, 0)]
        if self.branch_id:
            tank_ids = self.env['stock.location'].sudo().search([('branch_id', '=', self.branch_id.id), ('is_tank', '=', True), ('product_id', '!=', False)])
            for tank in tank_ids:
                lines.append((0, 0, {
                    'location_id': tank.id,
                }))
        self.reading_lines = lines

    @api.onchange('date')
    def _onchange_date(self):
        if self.date:
            self.reading_lines._update_stock_in_data()
            self.reading_lines._update_stock_out_data()

    @api.model
    def create(self, vals):
        if vals.get('name') == 'New' or 'name' not in vals:
            vals['name'] = self.env.ref('dxl_gas_station.tank_dip_reading_sequence').next_by_id()
        return super(TankDipReading, self).create(vals)

    def action_running(self):
        if not self.reading_lines:
            raise ValidationError(_('There is no details.'))
        self.write({'state': 'running'})

    def action_validate(self):
        self.write({'state': 'submit'})

    def action_approve(self):
        # if self.reading_lines.filtered(lambda x: x.on_hand_qty > 0 and x.dip_reading == 0):
        #     raise ValidationError(_('Please enter Dip Reading on every lines.'))
        # self.action_process_tank_loss()
        self.write({'state': 'posted'})

    def action_process_tank_loss(self):
        out_moves = self.env['stock.move']
        for line in self.reading_lines.filtered(lambda x: x.tank_loss > 0):
            group_id = self.env['procurement.group'].sudo().create({'name': line.reading_id.name + ' - ' + line.location_id.name})
            warehouse_id = line.location_id.warehouse_id
            loss_location_id = line.location_id.loss_location_id
            if not loss_location_id:
                raise ValidationError(_('Please set loss location on %s' % line.location_id.display_name))
            picking_type_id = self.env['stock.picking.type'].search([('warehouse_id', '=', warehouse_id.id), ('code', '=', 'internal')])
            int_move = self.env['stock.move'].sudo().create({
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'origin': line.reading_id.name,
                'location_id': line.location_id.id,
                'location_dest_id': loss_location_id.id,
                'product_uom_qty': line.tank_loss,
                'product_uom': line.product_id.uom_id.id,
                'picking_type_id': picking_type_id.id,
                'group_id': group_id.id,
                'tank_reading_id': line.reading_id.id,
                'quantity_done': line.tank_loss,
            })
            out_moves = int_move._action_confirm()
            out_moves._action_done()
            picking_ids = out_moves.mapped('picking_id')


class TankDipReadingLine(models.Model):
    _name = 'tank.dip.reading.line'
    _description = "Tank Dip Reading Line"

    reading_id = fields.Many2one('tank.dip.reading', required=True)
    branch_id = fields.Many2one('res.branch', related="reading_id.branch_id")
    location_id = fields.Many2one('stock.location', required=True, string="Tanks")
    product_id = fields.Many2one('product.product', related="location_id.product_id", store=True)
    previous_stock_qty = fields.Float('Previous Stock', compute="_compute_previous_stock_qty")
    purchase_qty = fields.Float('Purchase', readonly=True)
    sale_qty = fields.Float('Sale', readonly=True)
    on_hand_qty = fields.Float('On Hand Qty', compute="_compute_on_hand_qty")
    dip_reading = fields.Float('Dip Reading(cm)')
    dip_reading_gal = fields.Float('Dip Reading(gal)')
    tank_loss = fields.Float('Tank Loss', compute="_compute_tank_loss")

    @api.onchange('dip_reading')
    def _onchange_dip_reading(self):
        if self.dip_reading > self.on_hand_qty:
            raise ValidationError(_('Dip Reading should not more than on hand quantity.'))

    @api.depends('on_hand_qty', 'dip_reading_gal')
    def _compute_tank_loss(self):
        for line in self:
            line.tank_loss = line.on_hand_qty - line.dip_reading_gal

    @api.depends('reading_id.date', 'location_id', 'previous_stock_qty', 'purchase_qty', 'sale_qty')
    def _compute_on_hand_qty(self):
        for line in self:
            line.on_hand_qty = line.previous_stock_qty + line.purchase_qty - line.sale_qty

    @api.onchange('location_id', 'reading_id.date')
    def _onchange_location_id(self):
        if self.location_id and self.product_id:
            self._update_stock_in_data()
            self._update_stock_out_data()

    def _update_stock_out_data(self):
        for line in self.filtered(lambda x: x.reading_id.state in ('draft', 'running')):
            sale_qty = 0.0
            if line.reading_id.date and line.location_id:
                start_at = self.convert_to_server_time(line.reading_id.date.strftime('%Y-%m-%d') + ' 00:00:00')
                stop_at = self.convert_to_server_time(line.reading_id.date.strftime('%Y-%m-%d') + ' 23:59:59')
                domain = [
                    ('date', '>=', start_at),
                    ('date', '<=', stop_at),
                    ('location_dest_id.usage', '=', 'customer'),
                    ('location_id', '=', line.location_id.id),
                    ('state', '=', 'done'),
                    ('sale_line_id', '!=', False),
                ]
                sale_moves = self.env['stock.move'].sudo().search(domain)
                sale_qty = sum(sale_moves.mapped('product_uom_qty'))
            line.write({'sale_qty': sale_qty})

    def _update_stock_in_data(self):
        for line in self.filtered(lambda x: x.reading_id.state in ('draft', 'running')):
            purchase_qty = 0.0
            if line.reading_id.date and line.location_id:
                start_at = self.convert_to_server_time(line.reading_id.date.strftime('%Y-%m-%d') + ' 00:00:00')
                stop_at = self.convert_to_server_time(line.reading_id.date.strftime('%Y-%m-%d') + ' 23:59:59')
                domain = [
                    ('date', '>=', start_at),
                    ('date', '<=', stop_at),
                    ('location_id.usage', '=', 'supplier'),
                    ('location_dest_id', '=', line.location_id.id),
                    ('state', '=', 'done'),
                    ('purchase_line_id', '!=', False),
                ]
                purchase_moves = self.env['stock.move'].sudo().search(domain)
                purchase_qty = sum(purchase_moves.mapped('product_uom_qty'))
            line.write({'purchase_qty': purchase_qty})

    @api.depends('reading_id.date', 'location_id')
    def _compute_previous_stock_qty(self):
        for line in self:
            previous_stock_qty = 0.0
            if line.reading_id.date and line.product_id and line.branch_id:
                previous_stock_qty = line._get_opening_stock(line.reading_id.date, line.product_id.id, line.branch_id.id, line.location_id.id)
            line.previous_stock_qty = previous_stock_qty

    def convert_to_server_time(self, date):
        user = self.env.user
        dt = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        if self.env.user.tz:
            utc = pytz.timezone('UTC')
            user_tz = pytz.timezone(self.env.user.tz)
            dt = user_tz.localize(dt).astimezone(utc)
        return datetime.strftime(dt, '%Y-%m-%d %H:%M:%S')

    def _get_opening_stock(self, start_at, product_id, branch_id, location_id):
        start_at = self.convert_to_server_time(start_at.strftime('%Y-%m-%d') + ' 00:00:00')
        query = """SELECT 
                    sum(inventory.quantity) as quantity
                    from (select 
                    m.date as date,
                    sum(-m.product_uom_qty) as quantity
                    from stock_move as m
                    LEFT join product_product as p on (p.id = m.product_id)
                    LEFT join product_template as pt on (pt.id = p.product_tmpl_id)
                    LEFT JOIN stock_location ls on (ls.id=m.location_id)
                    LEFT JOIN stock_location ld on (ld.id=m.location_dest_id)
                    where ls.branch_id = %(branch_id)s and ls.id = %(location_id)s and (ls.usage = 'internal' and ld.usage != 'internal') and m.state = 'done' and m.product_id = %(product_id)s
                    group by m.date
                    UNION ALL
                    select 
                        m.date as date,
                        sum(m.product_uom_qty) as quantity
                    from stock_move as m
                    LEFT join product_product as p on (p.id = m.product_id)
                    LEFT join product_template as pt on (pt.id = p.product_tmpl_id)
                    LEFT JOIN stock_location ls on (ls.id=m.location_id)
                    LEFT JOIN stock_location ld on (ld.id=m.location_dest_id)
                    where ld.branch_id = %(branch_id)s and ld.id = %(location_id)s and (ls.usage != 'internal' and ld.usage = 'internal') and m.state = 'done' and m.product_id = %(product_id)s
                    group by m.date) as inventory
                    where inventory.date < %(start_at)s"""
        self.env.cr.execute(query , {'start_at': start_at, 'product_id': product_id, 'branch_id': branch_id, 'location_id': location_id})
        res = self.env.cr.dictfetchall()
        quantity = 0.0
        if res:
            quantity = res[0].get('quantity') or 0.0
        return quantity

