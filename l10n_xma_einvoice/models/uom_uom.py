# -*- coding: utf-8 -*-
from odoo import fields, models, api


class UomUom(models.Model):
    _inherit = 'uom.uom'


    l10n_xma_uomcode = fields.Many2one(
        'l10n_xma.uomcode',
        string="Código unidad de medida"
    )

    l10n_xma_uomcode_id = fields.Many2one(
        'l10n_xma.uomcode',
        string="Código unidad de medida",
    )

    country_id = fields.Many2one(
        'res.country',
        string='País',
        help="País de la empresa",
    )

class UomCategory(models.Model):
    _inherit = 'uom.category'

    country_id = fields.Many2one(
        'res.country',
        compute='get_country_id_from_company',
        string='País',
        help="País de la empresa",
    )

    @api.model
    def get_country_id_from_company(self):
        for rec in self:
            rec.country_id = self.env.company.country_id.id