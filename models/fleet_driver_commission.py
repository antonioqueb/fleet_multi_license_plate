# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class FleetDriverCommission(models.Model):
    """Catálogo de comisión por chofer sobre Órdenes de Servicio (módulo de
    Flota). Es la única fuente de verdad del porcentaje vigente; el reporte
    de servicios por chofer (extensión de `service.order`) lo consulta para
    calcular el monto de comisión de cada orden."""
    _name = 'fleet.driver.commission'
    _description = 'Comisión de Chofer por Órdenes de Servicio'
    _order = 'driver_id, date_from desc'

    driver_id = fields.Many2one(
        'res.partner', string='Chofer', required=True, domain=[('is_driver', '=', True)],
    )
    percentage = fields.Float(
        string='% de Comisión', required=True,
        help='Porcentaje aplicado sobre el total de cada Orden de Servicio donde este chofer '
             'aparezca como operador.',
    )
    date_from = fields.Date(string='Vigente Desde', default=fields.Date.context_today, required=True)
    active = fields.Boolean(string='Activa', default=True)
    notes = fields.Text(string='Observaciones')
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)

    @api.constrains('driver_id', 'active')
    def _check_unique_active_driver(self):
        for rec in self:
            if not rec.active:
                continue
            duplicated = self.search([
                ('driver_id', '=', rec.driver_id.id),
                ('active', '=', True),
                ('id', '!=', rec.id),
            ])
            if duplicated:
                raise ValidationError(
                    'El chofer "%s" ya tiene una comisión activa (%s%%, vigente desde %s). '
                    'Archive la anterior antes de crear una nueva.'
                    % (rec.driver_id.name, duplicated[0].percentage, duplicated[0].date_from)
                )

    @api.constrains('percentage')
    def _check_percentage_range(self):
        for rec in self:
            if rec.percentage < 0 or rec.percentage > 100:
                raise ValidationError('El porcentaje de comisión debe estar entre 0 y 100.')
