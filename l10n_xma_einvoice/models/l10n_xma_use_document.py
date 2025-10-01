# -*- coding: utf-8 -*-
from odoo import fields, models


class L10nXmaUseDocument(models.Model):
    _name = "l10n_xma.use.document"
    _description = "Latam EDI Document Use"
    _order = 'sequence, id'
    _rec_names_search = ['code','name']

    active = fields.Boolean(default=True)
    sequence = fields.Integer(help='To set in which order show the documents type taking into account the most'
        ' commonly used first')
    country_id = fields.Many2one(
        'res.country', required=True, index=True, help='Country in which this document is valid')
    name = fields.Char(required=True, help='Use document name')
    code = fields.Char(help='Code used by different localizations')
    comments = fields.Char(
       string='comments'
    )
    operation_type = fields.Integer(
        string='Operation type',
    )
    l10n_xma_transaction_type = fields.Selection(
        [
        ('', 'Seleccionar'),
        ('invoice', 'Factura'),
        ('remision_note', 'Nota de Remision')],
        string="Tipo de Documento",
        default='',
    )

    

