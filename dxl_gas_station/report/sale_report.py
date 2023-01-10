# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    salesperson_id = fields.Many2one('res.users', string='Nozzle Sales Person', readonly=True)

    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['salesperson_id'] = ", l.salesperson_id as salesperson_id"
        groupby += ', l.salesperson_id'
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
