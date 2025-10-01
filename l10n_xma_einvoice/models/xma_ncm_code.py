# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields


class XmaNCMCode(models.Model):
    _name = "xma.ncm.code"
    _description = "NCM Code"

    code = fields.Char("Code")
    name = fields.Char("Name")
