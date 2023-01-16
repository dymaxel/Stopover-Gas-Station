# -*- coding: utf-8 -*-
{
    "name": "Gas Station",
    "version": "15.0.10",
    "category": "Gas Station",
    "author": "Dymaxel Systems",
    "depends": ['branch'],
    "data": [
        'security/ir.model.access.csv',
        'data/gas_station_data.xml',
        'views/tank_dip_reading_view.xml',
        'views/tank_nozzle_view.xml',
        'views/nozzle_dispenser_view.xml',
        'views/nozzle_dip_reading_view.xml',
        'views/sale_order_view.xml',
        'views/stock_location_view.xml',
        'views/nozzle_salesperson_view.xml',
    ],
    "installable": True,
    "application": True,
    'license': 'LGPL-3',
}
