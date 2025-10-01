from odoo import fields,models,api 


class StockLot(models.Model):
    _inherit="stock.lot"

    l10n_xma_fab_date = fields.Date(
        string="Fecha de Fabricacion"
    )