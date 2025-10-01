from odoo import fields, models


class AccountJournalInherit(models.Model):
    _inherit="account.journal"

    version_document  = fields.Char()

    
    l10n_xma_version_document = fields.Char(
        string='Versión del documento electrónico',
    )
    

    l10n_xma_invoice_dir_id = fields.Many2one(
        'res.partner', string="Establecimiento"
    )
    
    l10n_xma_latam_document_type_id = fields.Many2one(
        'l10n_latam.document.type', string="Latam Document"
    )

    country_id = fields.Many2one(
        'res.country',
        related="company_id.country_id",
    )