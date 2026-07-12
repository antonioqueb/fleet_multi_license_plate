from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    license_plate_2 = fields.Char(string='Matrícula 2')
    license_plate_3 = fields.Char(string='Matrícula 3')
    numero_economico = fields.Char(string='Número Económico')

    safety_equipment_ids = fields.One2many(
        'fleet.safety.equipment', 'vehicle_id', string='EPP, Extintores y Kits de Derrames',
    )
    safety_equipment_count = fields.Integer(compute='_compute_safety_equipment_count')
    safety_equipment_alert_count = fields.Integer(compute='_compute_safety_equipment_count')

    @api.depends('safety_equipment_ids.state')
    def _compute_safety_equipment_count(self):
        for vehicle in self:
            vehicle.safety_equipment_count = len(vehicle.safety_equipment_ids)
            vehicle.safety_equipment_alert_count = len(
                vehicle.safety_equipment_ids.filtered(lambda e: e.state in ('warning', 'expired'))
            )

    def action_view_safety_equipment(self):
        self.ensure_one()
        return {
            'name': _('EPP, Extintores y Kits de Derrames'),
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.safety.equipment',
            'view_mode': 'list,form',
            'domain': [('vehicle_id', '=', self.id)],
            'context': {'default_vehicle_id': self.id},
        }


    @api.constrains('license_plate', 'license_plate_2', 'license_plate_3')
    def _check_unique_license_plates(self):
        for vehicle in self:
            plates = [p for p in [
                vehicle.license_plate,
                vehicle.license_plate_2,
                vehicle.license_plate_3,
            ] if p]

            # Verificar duplicados internos
            if len(plates) != len(set(plates)):
                raise ValidationError('Las matrículas del vehículo no pueden repetirse entre sí.')

            # Verificar duplicados en otros vehículos
            for plate in plates:
                domain = [
                    ('id', '!=', vehicle.id),
                    '|', '|',
                    ('license_plate', '=', plate),
                    ('license_plate_2', '=', plate),
                    ('license_plate_3', '=', plate),
                ]
                if self.search_count(domain):
                    raise ValidationError(f'La matrícula "{plate}" ya está registrada en otro vehículo.')