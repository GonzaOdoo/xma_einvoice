from odoo import fields,models

class ResCountry(models.Model):
    _inherit="res.country"

    l10n_xma_country_code = fields.Char(
        string="Codigo de Pais"
    )
    l10n_xma_bacen_country_code = fields.Char(
        string="Código do País (BACEN)",        
        default='1058'
        
    )

    