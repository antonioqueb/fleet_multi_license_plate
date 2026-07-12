# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import _, api, fields, models

# Días de anticipación para marcar "Próximo a Vencer" (requiere validar con el
# negocio; mismo estilo de constante ajustable que RP_ALERT_MONTHS en
# service_order_recepcion / DF_ALERT_DIAS_* en destruccion_fiscal).
SAFETY_EQUIPMENT_ALERT_DAYS = 30

EQUIPMENT_TYPE_SELECTION = [
    ('epp', 'Equipo de Protección Personal (EPP)'),
    ('extintor', 'Extintor'),
    ('kit_derrames', 'Kit de Derrames'),
]


class FleetSafetyEquipment(models.Model):
    """Control de EPP, extintores y kits de derrames por vehículo: qué hay,
    cuánto, cuándo se revisó por última vez y cuándo vence/hay que recargarlo."""
    _name = 'fleet.safety.equipment'
    _description = 'Control de EPP, Extintores y Kits de Derrames'
    _inherit = ['mail.thread']
    _order = 'vehicle_id, expiration_date'

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehículo', required=True, ondelete='cascade')
    equipment_type = fields.Selection(EQUIPMENT_TYPE_SELECTION, string='Tipo', required=True, tracking=True)
    name = fields.Char(string='Descripción', required=True, help='Ej: "Guantes de nitrilo", "Extintor PQS 9kg", "Kit universal 20L".')
    quantity = fields.Integer(string='Cantidad', default=1)
    capacity = fields.Char(string='Capacidad / Especificación', help='Ej: "9 kg", "20 L", "Talla M".')

    last_inspection_date = fields.Date(string='Última Inspección', tracking=True)
    expiration_date = fields.Date(string='Fecha de Vencimiento / Recarga', tracking=True)
    responsible_id = fields.Many2one(
        'res.users', string='Responsable de Inspección', default=lambda self: self.env.user,
    )

    state = fields.Selection([
        ('sin_vencimiento', 'Sin Vencimiento'),
        ('ok', 'Vigente'),
        ('warning', 'Próximo a Vencer'),
        ('expired', 'Vencido'),
    ], string='Estado', compute='_compute_state', store=True)

    attachment = fields.Binary(string='Evidencia / Certificado')
    attachment_filename = fields.Char(string='Nombre de Archivo')
    notes = fields.Text(string='Observaciones')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)

    @api.depends('expiration_date')
    def _compute_state(self):
        today = fields.Date.context_today(self)
        threshold = today + timedelta(days=SAFETY_EQUIPMENT_ALERT_DAYS)
        for rec in self:
            if not rec.expiration_date:
                rec.state = 'sin_vencimiento'
            elif rec.expiration_date < today:
                rec.state = 'expired'
            elif rec.expiration_date <= threshold:
                rec.state = 'warning'
            else:
                rec.state = 'ok'

    @api.model
    def _cron_check_safety_equipment(self):
        """Alerta diaria (actividad en el vehículo, deduplicada) para EPP,
        extintores y kits de derrames vencidos o próximos a vencer."""
        equipos = self.search([('state', 'in', ('warning', 'expired'))])
        labels = dict(EQUIPMENT_TYPE_SELECTION)
        for vehicle in equipos.mapped('vehicle_id'):
            items = equipos.filtered(lambda e: e.vehicle_id == vehicle)
            summary = _('Revisión de EPP/Extintores/Kits de Derrames pendiente')
            existing = self.env['mail.activity'].search([
                ('res_model', '=', 'fleet.vehicle'),
                ('res_id', '=', vehicle.id),
                ('summary', '=', summary),
            ], limit=1)
            if existing:
                continue
            detalle = '\n'.join(
                '- %s (%s): %s' % (
                    item.name, labels.get(item.equipment_type, item.equipment_type),
                    _('Vencido') if item.state == 'expired' else _('Próximo a vencer'),
                )
                for item in items
            )
            vehicle.activity_schedule(
                act_type_xmlid='mail.mail_activity_data_warning',
                summary=summary,
                note=_('Los siguientes elementos de seguridad requieren atención:\n%s') % detalle,
            )
        return True
