# -*- coding: utf-8 -*-
from odoo import fields, models


class L10nXmaTaxpayerType(models.Model):
    _name = "l10n_xma.taxpayer_type"
    _description = "Latam Document Type for EDI"
    _order = 'sequence, id'
    _rec_names_search = ['code','name']

    active = fields.Boolean(default=True)
    sequence = fields.Integer(help='To set in which order show the documents type taking into account the most'
        ' commonly used first')
    country_id = fields.Many2one(
        'res.country',help='Country in which this taxpayer type is valid')
    name = fields.Char(required=True, help='Taxpayer type name')
    code = fields.Char(help='Code used by different localizations')
    comments = fields.Text(
       string='Comments'
    )

    

