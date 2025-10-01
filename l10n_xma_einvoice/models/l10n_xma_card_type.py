from odoo import fields,models


class L10nXmaCardType(models.Model):
    _name = "l10n_xma.card.type"

    name = fields.Char(
        string="Nombre"
    )

    code = fields.Char(
        string="Codigo"
    )

    country_id = fields.Many2one(
        'res.country',
        string="Pais"
    )