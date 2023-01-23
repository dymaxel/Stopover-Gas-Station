from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class NozzleReportWizard(models.TransientModel):
    _name = 'nozzle.report.wizard'
    _description = 'Daily Summary Of Fuel Pump'

    start_at = fields.Date(string='Date', required=True)
    branch_id = fields.Many2one('res.branch', string="Branch", required=True)

    def print_pdf_report(self):
        data = {
            'start_at': self.start_at,
            'branch_id': self.branch_id.id,
        }
        return self.env.ref('dxl_gas_station.nozzle_report').report_action(self, data=data)

    def cancel(self):
        print()


class QualitySheetReportNozzle(models.AbstractModel):
    _name = 'report.dxl_gas_station.nozzle_report_template'

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        date_from = data['start_at']
        branch = self.env['res.branch'].browse(data['branch_id'])
        tanks = self.env['stock.location'].search([('is_tank', '=', True), ('branch_id', '=', branch.id)])
        vals = {}
        ids = []
        for tank in tanks:
            ids.append(tank.product_id.id)
            if not branch.name in vals:
                vals.update({branch.name: [{
                    'tank': tank.name
                }]})
            else:
                new_dict = {'tank': tank.name}
                row = vals.get(branch.name)
                row.append(new_dict)
        data['tanks'] = vals
        product_ids = self.env['product.product'].browse(ids)
        date = date_from
        report_data = []
        for product in product_ids:
            report_data.append({
                'nozzle': self.get_nozzle(product, date),
                'product': product.name,
                'opening': self.get_opening_reading(product, date),
                'closing': self.get_closing_reading(product, date),
                'gal': self.get_gal(product, date),
                'unit': product.list_price,
                'amount': self.get_gal(product, date) * product.list_price,
            })
        print()
        return {
            'docs': docs,
            'date_from': date_from,
            'branch': branch.name,
            'tanks': vals,
            'readings': report_data,
        }

    def get_gal(self, product, date):
        reading_line = self.env['tank.dip.reading.line'].sudo().search([
            ('reading_id.date', '=', date),
            ('reading_id.state', '=', 'posted'),
            ('product_id', '=', product.id)
        ], limit=1)
        if reading_line:
            return reading_line.dip_reading_gal
        else:
            return 0

    def get_nozzle(self, product, date):
        meter_reading_line = self.env['nozzle.dip.reading.line'].sudo().search([
            ('reading_id.date', '=', date),
            ('reading_id.state', '=', 'posted'),
            ('product_id', '=', product.id)
        ], limit=1)
        if meter_reading_line:
            return meter_reading_line.nozzle_id.name
        else:
            return "-"

    def get_opening_reading(self, product, date):
        meter_reading_line = self.env['nozzle.dip.reading.line'].sudo().search([
            ('reading_id.date', '=', date),
            ('reading_id.state', '=', 'posted'),
            ('product_id', '=', product.id)
        ], limit=1)
        if meter_reading_line:
            return meter_reading_line.opening_reading
        else:
            return "-"

    def get_closing_reading(self, product, date):
        meter_reading_line = self.env['nozzle.dip.reading.line'].sudo().search([
            ('reading_id.date', '=', date),
            ('reading_id.state', '=', 'posted'),
            ('product_id', '=', product.id)
        ], limit=1)
        if meter_reading_line:
            return meter_reading_line.closing_reading
        else:
            return "-"
