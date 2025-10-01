from odoo import fields, models

class L10nXmaHazardousMaterial(models.Model):
    _name = 'l10n_xma.hazardous.material'
    _rec_names_search = ['code','name']

    name = fields.Char(required=True, help='Use document name')
    code = fields.Char(help='Code used by different localizations')
    comments = fields.Char(
       string='comments'
    )
    country_id = fields.Many2one(
        'res.country', index=True, help='Country in which this document is valid')
    
    date_from = fields.Date(
        string="Date from"
    )

    date_end = fields.Date(
        string="Date end"
    )

    code_division = fields.Char(
        string="Code division"
    )

    secondary_danger = fields.Char(
        string="Secondary Danger"
    )