from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    license_plate_2 = fields.Char(string='Matrícula 2')
    license_plate_3 = fields.Char(string='Matrícula 3')

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
