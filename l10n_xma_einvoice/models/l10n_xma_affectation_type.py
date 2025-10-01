# -*- coding: utf-8 -*-
from odoo import fields, models


class L10nXmaAffectationType(models.Model):
    _name = "l10n_xma.affectation_type"


    code = fields.Char(
        string='Código'
    )
    name = fields.Char(
        string='Nombre'
    )
    comments = fields.Char(
       string='Descripción'
    )
    code_unece = fields.Char(
       string='Code un/ece'
    )
    country_id = fields.Many2one(
        'res.country',
        index=True,
        string='País'
    )