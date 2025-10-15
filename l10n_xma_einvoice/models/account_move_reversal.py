# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    l10n_latam_document_type_id = fields.Many2one('l10n_latam.document.type', 'Document Type', ondelete='cascade', domain="[]", compute='_compute_document_type', readonly=False, store=True)
    

    # def reverse_moves(self, is_modify=False):
    #     self.ensure_one()
    #     res = super(AccountMoveReversal, self).reverse_moves(fields)
    #     print(f"RES MOVES ::: {self.new_move_ids}")

    def _get_custom_reversal_values(self, move):
        if move.country_id.id == 185:
            return {
                'debit_origin_id': move.id,
                'l10n_xma_cdc_asociado': move.l10n_xma_uuid_invoice,
                'l10n_xma_number_timbrado_asociado': move.l10n_latam_document_type_id.l10n_xma_authorization_code,
                'l10n_xma_cod_state_asociado': move.l10n_latam_document_type_id.l10n_xma_branch,
                'l10n_xma_point_exp_asociado': move.l10n_latam_document_type_id.l10n_xma_dispatch_point,
                'l10n_xma_document_number_asociado': move.sequence_number,
                'l10n_xma_tipo_doc_asociado': '1',
                'l10n_xma_date_document_emision': move.l10n_xma_date_post,
                'l10n_xma_payment_term': move.l10n_xma_payment_term
            }
        return {}


    def _prepare_default_reversal(self, move):
        values = super()._prepare_default_reversal(move)
        custom_vals = self._get_custom_reversal_values(move)
        return {**values, **custom_vals}
