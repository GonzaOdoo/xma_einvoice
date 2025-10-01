from odoo import models, fields


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'


    l10n_xma_payment_type_id = fields.Many2one(
        'l10n_xma.payment_type',
        string='Metodo de Pago'
    )

    l10n_xma_payment_form_id = fields.Many2one(
        'xma_payment.form',
        string="Forma de pago"
    )

    def _create_payment_vals_from_wizard(self, batch_result):
        vals = super()._create_payment_vals_from_wizard(batch_result)
        vals['l10n_xma_payment_type_id'] = self.l10n_xma_payment_type_id.id
        vals['l10n_xma_payment_form_id'] = self.l10n_xma_payment_form_id.id
        return vals
