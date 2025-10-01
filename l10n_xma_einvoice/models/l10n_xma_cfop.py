# -*- coding: utf-8 -*-
from odoo import fields, models


class L10nXmaCfop(models.Model):
    _name = "l10n_xma.cfop"


    code = fields.Char(
        string='Código'
    )
    name = fields.Char(
        string='Nombre'
    )
    
    porcent = fields.Float(
        string='Porcentaje',
    )
    
    comments = fields.Char(
       string='Descripción'
    )
    country_id = fields.Many2one(
        'res.country',
        index=True,
        string='País'
    )