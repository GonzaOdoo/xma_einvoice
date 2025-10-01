from odoo import models, fields, _


class ResBank(models.Model):
    _inherit = "res.bank"

    l10n_xma_vat = fields.Char(
        string="VAT", help="Indicate the VAT of this institution, the value "
        "could be used in the payment complement in Mexico documents")
