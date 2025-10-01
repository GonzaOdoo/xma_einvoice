from odoo import fields, models, _


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    l10n_xma_decimal_number = fields.Integer(
        'Número de decimales'
    )