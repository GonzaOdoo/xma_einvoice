from odoo import api, fields, models, _
from odoo.tools.float_utils import float_repr, float_round
from odoo.exceptions import UserError

class FelPhrase(models.Model):
    _name = 'l10n_xma.fel_phrase'
    _description ='Frases FEL'
    _order='typeprase_code, name asc'

    name= fields.Char(string="Texto a Colocar",required=True)
    typeprase_code = fields.Selection(selection=[ ('1','Frase de retención del ISR'),
                                                    ('2','Frase de retención del IVA'),
                                                    ('3','Frase de no genera derecho a crédito fiscal del IVA'),
                                                    ('4','Frase de exento o no afecto al IVA'),], required=True)
    
    scenario_code = fields.Integer(string="Codigo Escenario", default=0, required=True)
    scenario= fields.Text(string="Escenario",required=True)
    

    withhold_isr = fields.Boolean(string='Reten ISR', default=False)
    withhold_agent = fields.Boolean(string='Es Agente Retenedor', default=False)
    small_taxpayer = fields.Boolean(string='Es Pequeño Contribuyente', default=False)
    include_iva  = fields.Boolean(string='Incluye IVA', default=False)

    
    @api.depends('typeprase_code','scenario_code')
    def _compute_display_name(self):
        for rec in self:
            name = 'F%s-E%s %s' % (rec.typeprase_code,rec.scenario_code,rec.name)
            rec.display_name = name
            
    # @api.model
    # def _name_search(self, name='', args=None, operator='ilike', order='id', limit=100, name_get_uid=None):
    #     args = list(args or [])
    #     if not (name == '' and operator == 'ilike'):
    #         args += ['|', (self._rec_name, operator, name),
    #                     ('display_name', operator, name)]
    #     return self._search(args, limit=limit, access_rights_uid=name_get_uid)
    
    # def name_get(self):
    #     result = []    	
    #     for rec in self:
    #         result.append((rec.id, 'F%s-E%s %s' % (rec.typeprase_code,rec.scenario_code,rec.name)))    	
    #     return result
    