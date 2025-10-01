from odoo import fields, models


class L10nXmaDetraction(models.Model):
    _name = 'l10n_xma.detraction'

    country_id = fields.Many2one(
        'res.country', index=True, help='Country in which this document is valid')
    name = fields.Char(required=True, help='Use document name')
    code = fields.Char(help='Code used by different localizations')
    comments = fields.Char(
       string='comments'
    )
    porcent = fields.Integer(string="Porcentaje")