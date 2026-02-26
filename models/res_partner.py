from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_driver = fields.Boolean(string='Es conductor', default=False)