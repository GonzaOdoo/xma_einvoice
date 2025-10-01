# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class LatamDocument(models.Model):
    _inherit = "l10n_latam.document.type"
    
    l10n_xma_authorization_code = fields.Char()
    l10n_xma_branch = fields.Char()
    l10n_xma_dispatch_point = fields.Char()
    l10n_xma_sequence_start = fields.Integer()
    l10n_xma_sequence_end = fields.Integer()
    l10n_xma_date_start = fields.Date()
    l10n_xma_date_end = fields.Date()
    internal_type = fields.Selection(
        selection_add=[
            ('receipt_invoice', 'Recibo Electronico'),
        ]
    )
    l10n_xma_current_number = fields.Integer(readonly=True)
    l10n_xma_next_number = fields.Integer(readonly=True)
    l10n_xma_resequence_document = fields.Boolean(default=False, string="Resecuenciar documentos", help="Resecuenciar documentos cuando se reintenta timbrar la factura por algun error.")
    l10n_xma_left_refil = fields.Integer(default=6)
    journal_id = fields.Many2one("account.journal", string="Diario", domain=[('l10n_latam_use_documents', '=', True)])
    
    l10n_xma_serie = fields.Char(string="Serie")
    l10n_xma_transaction_type = fields.Selection(
        [
        ('', 'Seleccionar'),
        ('invoice', 'Factura'),
        ('remision_note', 'Nota de Remision')],
        string="Tipo de Documento",
        default='',
    )
    
    @api.model
    def consume_sequence(self):
        for record in self:
            record._check_date_end()
            record._check_current_number()
            # if record.l10n_xma_current_number >= record.l10n_xma_sequence_end:
            #     raise ValidationError(_("El número actual ha alcanzado el límite de la secuencia."))

            record.l10n_xma_current_number += 1
            record.l10n_xma_next_number = record.l10n_xma_current_number + 1
    
    @api.onchange('l10n_xma_sequence_start')
    def _onchange_sequence_start(self):
        if self.l10n_xma_sequence_start:
            self.l10n_xma_current_number = self.l10n_xma_sequence_start
            self.l10n_xma_next_number = self.l10n_xma_sequence_start + 1
            if self.l10n_xma_sequence_start != self._origin.l10n_xma_sequence_start:
                return {'warning': {
                        'title': _("La secuencia ha cambiado."),
                        'message': "%s\n\n%s" % ("Esta cambiando la secuencia establecida", "Esto puede ocacionar un desfase en los números autorizados")
                    }} 

    # @api.constrains('l10n_xma_current_number', 'l10n_xma_sequence_end')
    def _check_current_number(self):
        for record in self:
            if record.l10n_xma_current_number > record.l10n_xma_sequence_end:
                raise ValidationError("Esta superando el número de folios autorizados para este tipo de documento.")

    # @api.constrains('l10n_xma_date_end')
    def _check_date_end(self):
        for record in self:
            if record.l10n_xma_date_end and record.l10n_xma_date_end < fields.Date.today():
                raise ValidationError("La fecha de vencimiento de los folios ha vencido para este tipo de documento.\nFavor de solicitar un nuevo lote de folios.")

class XmaSequenceLog(models.Model):
    _name = "xma.sequence.log"

    move_id = fields.Many2one("account.move") 
    no_document = fields.Char()
    error_log = fields.Text()
    date = fields.Date()
    document_type_id = fields.Many2one("l10n_latam.document.type")
    company_id = fields.Many2one("res.company")