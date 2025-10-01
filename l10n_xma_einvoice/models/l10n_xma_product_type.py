# -*- coding: utf-8 -*-
from odoo import fields, models


class L10nXmaProductType(models.Model):
    _name = "l10n_xma.product_type"


    code = fields.Char(
        string='Código'
    )
    name = fields.Char(
        string='Nombre'
    )
    comments = fields.Char(
       string='Descripción'
    )
    country_id = fields.Many2one(
        'res.country',
        index=True,
        string='País'
    )