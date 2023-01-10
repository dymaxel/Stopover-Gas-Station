# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class NozzleDispenser(models.Model):
    _name = 'nozzle.dispenser'
    _description = 'Nozzle Dispenser'

    name = fields.Char(required=True, copy=False)
