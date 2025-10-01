# -*- coding: utf-8 -*-
from odoo import fields, models



class ResPartner(models.Model):
    _inherit = "res.partner"

    l10n_xma_taxpayer_type_id = fields.Many2one(
        'l10n_xma.taxpayer_type', domain="[('country_id', 'in', (False, country_id))]",
        string='Taxpayer Type'
    )    
    
   
    commercial_name = fields.Char()
    
    external_number = fields.Char()
    
    internal_number = fields.Char()
    
    city_id = fields.Many2one('res.city')
    
    control_digit = fields.Char()
    
    municipality_id = fields.Many2one('l10n_xma.municipality', string="Municipio")
    
    is_taxpayer = fields.Boolean()
    
    customer_operation_type = fields.Selection([ ('1', 'Type 1'),
                                                ('2', 'Type 2'),
                                                ('3', 'Type 2'),
                                                ('4', 'Type 2'),],
                                               'Type')
    
    # Fields Paraguay invoices
    
    l10n_xma_external_number = fields.Char()
    
    l10n_xma_internal_number = fields.Char()
    
    l10n_xma_city_id = fields.Many2one('res.city',string="Ciudad")
    
    l10n_xma_control_digit = fields.Char()
    
    l10n_xma_municipality_id = fields.Many2one(
        'l10n_xma.municipality', string='Municipio'
    )
    
    l10n_xma_is_taxpayer = fields.Boolean()
    
    l10n_xma_customer_operation_type = fields.Selection([ ('1', 'B2B'),
                                                ('2', 'B2C'),
                                                ('3', 'B2G'),
                                                ('4', 'B2F'),])
    
    l10n_xma_indentification_type = fields.Selection(
        [
            ('1', 'Cedula paraguaya'),
            ('2', 'Pasaporte'),
            ('3', 'Cedula Extranjera'),
            ('4', 'Carnet de Residencia')
        ], default="1", string="Tipo de Documento de vendedor"
    )

    l10n_xma_identification_number = fields.Char(
        string="Número de documento de identidad del vendedor",
    )
    # Fields Paraguay invoices 
   
    # Campo para los pagos MX

    l10n_xma_no_tax_breakdown = fields.Boolean(
        string="No Tax Breakdown",
        help="Includes taxes in the price and does not add tax information to the CFDI. Particularly in handy for IEPS. ")
    
    l10n_xma_ubigeo_code = fields.Char()


    # Fields Brasil invoices 

    l10n_xma_ie_indicator = fields.Selection([ ('1', '1-Contribuinte ICMS (informar a IE do destinatário)'),
                                                ('2', '2-Contribuinte isento de Inscrição no cadastro de Contribuintes do ICMS.'),
                                                ('3', '9-Não Contribuinte, que pode ou não possuir Inscrição Estadual no Cadastro de Contribuintes do ICMS'),])


    
    l10n_xma_suframa_code = fields.Char(
        string='Suframa',
    )
    
    l10n_xma_is_principal_contact = fields.Boolean(
        string='Es el contacto principal',
    )

    
    l10n_xma_default_document_id = fields.Many2one(
        string='Tipo de documento',
        comodel_name='l10n_latam.document.type',
    )
    
    l10n_xma_rps_verification_code = fields.Char(string="Codigo de verificacion RPS")
    l10n_xma_special_regime = fields.Selection(string="Regimen Especial", selection=[
        ("1","Microempresa municipal"),
        ("2","Estimativa"),
        ("3","Sociedade de profissionais"),
        ("4","Cooperativa"),
        ("5","Microempresário Individual (MEI)"),
        ("6","Microempresário e Empresa de Pequeno Porte (ME EPP)"),
        ("7","Optante pelo Simples Nacional (Exclusivo Elotech e GLC Consultoria 2.0)"),
        ("8","Tributação Normal (Exclusivo E&L)"),
        ("9","Autônomo (Exclusivo E&L)"),
        ("10","Variável (Exclusivo GLC Consultoria 2.0)"),
        ("11","Lucro Real (Exclusivo Digifred)"),
        ("12","Lucro Presumido (Exclusivo Digifred)"),
        ("13","Sociedade de Profissionais Pessoa Jurídica (Exclusivo SEMFAZ)"),
        ("14","Não (Exclusivo NF-Eletrônica)"),
        ("15","Notas Totalizadoras (Exclusivo NF-Eletrônica)"),
        ("16","Inscrito no PRODEVAL (Exclusivo NF-Eletrônica)"),
    ])

    l10n_br_ie_code = fields.Char()
    l10n_br_im_code = fields.Char()
    l10n_br_cpf_code = fields.Char(string="CPF", help="Natural Persons Register.")
    
    l10n_xma_fiscal_unit_code = fields.Char(string="Codigo de la unidad fiscal") 
    l10n_xma_colony_code = fields.Char(
        string='Codigo de la colonia',
    )
