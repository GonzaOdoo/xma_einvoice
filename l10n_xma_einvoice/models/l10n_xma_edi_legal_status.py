# -*- coding: utf-8 -*-
from odoo import fields, models


class L10nXmaEdiLegalStatus(models.Model):
    _name = "l10n_xma.edi.legal.status"
    _description = "Status on Country Tax Deparment"
    _order = 'sequence, id'
    _rec_names_search = ['code','name']

    active = fields.Boolean(default=True)
    sequence = fields.Integer(
        default=10, required=True, help='To set in which order show the status')
    country_id = fields.Many2one(
        'res.country', required=True, index=True, help='Country in which this is valid')
    name = fields.Char(required=True, help='Status name')
    code = fields.Char(help='Code Status')
    comments = fields.Char(
       string='comments'
    )
   
    

