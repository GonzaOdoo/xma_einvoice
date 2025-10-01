from odoo import fields, models, api


class AccountMoveLine(models.Model):
    _inherit="account.move.line"    

    l10n_xma_tax_type_id = fields.Many2one(
        'l10n_xma.tax_type', string="Motivo de afectación"
    )
    l10n_xma_tax_situation_id = fields.Many2one(
        'l10n_xma.tax_situation', string="Situación tributaria"
    )
    l10n_xma_economic_activity_id = fields.Many2one(
        'l10n_xma.economic_activity', string="Actividad económina"
    )
    
    def _convert_to_tax_base_line_dict(self):
        self.ensure_one()
        is_invoice = self.move_id.is_invoice(include_receipts=True)
        sign = -1 if self.move_id.is_inbound(include_receipts=True) else 1

        return self.env['account.tax']._convert_to_tax_base_line_dict(
            self,
            partner=self.partner_id,
            currency=self.currency_id,
            product=self.product_id,
            taxes=self.tax_ids,
            price_unit=self.price_unit if is_invoice else self.amount_currency,
            quantity=self.quantity if is_invoice else 1.0,
            discount=self.discount if is_invoice else 0.0,
            account=self.account_id,
            analytic_distribution=self.analytic_distribution,
            price_subtotal=sign * self.amount_currency,
            is_refund=self.is_refund,
            rate=(abs(self.amount_currency) / abs(self.balance)) if self.balance else 1.0
        )

    @api.onchange('tax_ids')
    def ochande_tax_ids_get_tax(self):
        for rec in self.tax_ids:
            self.l10n_xma_tax_type_id = rec.l10n_xma_tax_type_id.id
    

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for order in res:
            order.ochande_tax_ids_get_tax()
        return res