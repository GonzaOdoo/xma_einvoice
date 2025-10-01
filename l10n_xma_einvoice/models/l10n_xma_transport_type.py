from odoo import fields, models, api, _

class L10nXmaTransportType(models.Model):
    _name = 'l10n_xma.transport.type'
    _description = 'Transport Type'

    country_id = fields.Many2one(
        'res.country', index=True, help='Country in which this document is valid')
    name = fields.Char(required=True, help='Use document name')
    code = fields.Char(help='Code used by different localizations')
    comments = fields.Char(
        string='comments'
    )
    l10n_xma_transaction_type = fields.Selection(
        [
        ('', 'Seleccionar'),
        ('invoice', 'Factura'),
        ('remision_note', 'Nota de Remision')],
        string="Tipo de Documento",
        default='',
    )

    def name_get(self):
        # OVERRIDE
        return [(tipo.id, "%s %s" % (tipo.code, tipo.name or '')) for tipo in self]
    
