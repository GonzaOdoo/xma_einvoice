from odoo import fields, models


class L10nXmaReasonDiscount(models.Model):
    _name = 'l10n_xma.reason.discount'
    
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

    l10n_xma_doc_type = fields.Selection(
        [
        ('', 'Seleccionar'),
        ('invoice', 'Factura'),
        ('remision_note', 'Nota de Remision')],
        string="Tipo de Documento",
        default='',
    )