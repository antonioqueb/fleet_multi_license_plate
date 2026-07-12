# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ServiceOrder(models.Model):
    """Cálculo de comisión del chofer sobre esta Orden de Servicio, a partir
    del catálogo `fleet.driver.commission`. Es una extensión puramente de
    reporte/valor informativo: no cambia el flujo, estados ni facturación de
    la orden."""
    _inherit = 'service.order'

    driver_commission_percentage = fields.Float(
        string='% Comisión Chofer', compute='_compute_driver_commission', store=True,
    )
    driver_commission_amount = fields.Monetary(
        string='Comisión Chofer', compute='_compute_driver_commission', store=True,
        currency_field='currency_id',
    )

    @api.depends('chofer_id', 'amount_total')
    def _compute_driver_commission(self):
        Commission = self.env['fleet.driver.commission']
        for order in self:
            commission = Commission.browse()
            if order.chofer_id:
                commission = Commission.search([
                    ('driver_id', '=', order.chofer_id.id),
                    ('active', '=', True),
                ], limit=1)
            order.driver_commission_percentage = commission.percentage or 0.0
            order.driver_commission_amount = order.amount_total * order.driver_commission_percentage / 100.0
