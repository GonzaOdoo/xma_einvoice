from odoo import fields, models


class L10nXmaServiceType(models.Model):
    _name = "l10n_xma.service_type"


    code = fields.Char(
        string='Código'
    )
    name = fields.Char(
        string='Nombre'
    )
    comments = fields.Char(
       string='Descripción'
    )
    country_id = fields.Many2one(
        'res.country',
        index=True,
        string='País'
    )