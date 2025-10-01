from odoo import fields,models

class ResCountryState(models.Model):
    _inherit="res.country.state"

    
    l10n_xma_statecode = fields.Char(
        string='Código de la provincia',
    )