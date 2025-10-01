# -*- coding: utf-8 -*-
from odoo import fields, models


class L10nXmaEdiLegalStatus(models.Model):
    _name = "l10n_xma.economic_activity"
    
    code = fields.Char(
        string="Código"
    )

    name = fields.Char(
        string="Nombre"
    )

    comments = fields.Text(
        string="Comentarios"
    )

    country_id = fields.Many2one(
        'res.country',
        string="Pais"
    )
    res_company = fields.Many2one(
        'res.company',
    )