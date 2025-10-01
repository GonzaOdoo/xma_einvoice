from odoo import fields, models


class AccountAccountTag(models.Model):
    _inherit="account.account.tag"    

    l10n_xma_tax_type_id = fields.Many2one(
        'l10n_xma.tax_type', string="Motivo de afectación"
    )