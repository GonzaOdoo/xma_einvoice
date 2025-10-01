# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductProduct(models.Model):
    _inherit="product.product"

    country_id = fields.Many2one(
        'res.country',
        related="company_id.country_id",
    ) 

    l10n_xma_productcode_id = fields.Many2one(
        'l10n_xma.productcode',
        string="Código del SAT",
        related="product_tmpl_id.l10n_xma_productcode_id",
        readonly=False
    )

    l10n_xma_detraction_id = fields.Many2one(
        'l10n_xma.detraction',
    )

    l10n_xma_detraction_porcent = fields.Integer(
        related="l10n_xma_detraction_id.porcent" 
    )


    l10n_xma_origin_prod = fields.Many2one(
        'l10n_xma.origin_operation'
    )

    # br
    l10n_xma_codtributNacional_id = fields.Many2one(
        'l10n_xma.productcode',
        string="Código de tributação Nacional",
        related="product_tmpl_id.l10n_xma_codtributNacional_id",
        readonly=False
    )

    l10n_xma_cfop_id = fields.Many2one(
        string='Código Fiscal de Operações e Prestações',
        related="product_tmpl_id.l10n_xma_cfop_id"
    )

    l10n_xma_product_type_id = fields.Many2one(
        string='Tipo de producto',
        related="product_tmpl_id.l10n_xma_product_type_id"
    )
    l10n_xma_service_type_id = fields.Many2one(
        string='Tipo de servicio',
        related="product_tmpl_id.l10n_xma_service_type_id"
    )

    l10n_xma_is_hazaudous_material = fields.Selection(
        [('si', "Si"),("noo", "No (Opcional)"), ('no', 'No')],
        string="Es Material Peligroso",
        related='product_tmpl_id.l10n_xma_is_hazaudous_material'
    )
    l10n_xma_hazaudous_material_id = fields.Many2one(
        'l10n_xma.hazardous.material',
        string="Material Peligroso",
        related='product_tmpl_id.l10n_xma_hazaudous_material_id',
        readonly=False
    )
    l10n_xma_need_retention = fields.Boolean(
        string='Necesita retención',
        related='product_tmpl_id.l10n_xma_need_retention',
        readonly=False
    )

    options_cst_field = [
        ('00', 'Tributada integralmente'),
        ('02', 'Tributação monofásica própria sobre combustíveis'),
        ('10', 'Tributada e com cobrança do ICMS por substituição tributária'),
        ('15', 'Tributação monofásica própria e com responsabilidade pela retenção sobre combustíveis'),
        ('20', 'Com redução de base de cálculo'),
        ('30', 'Isenta ou não tributada e com cobrança do ICMS por substituição tributária'),
        ('40', 'Isenta'),
        ('41', 'Não tributada'),
        ('50', 'Suspensão'),
        ('51', 'Diferimento'),
        ('53', 'Tributação monofásica sobre combustíveis com recolhimento diferido'),
        ('60', 'ICMS cobrado anteriormente por substituição tributária'),
        ('61', 'Tributação monofásica sobre combustíveis cobrada anteriormente'),
        ('70', 'Com redução de base de cálculo e cobrança do ICMS por substituição tributária'),
        ('90', 'Outros'),
        ('101', 'Tributada pelo Simples Nacional com permissão de crédito'),
        ('102', 'Tributada pelo Simples Nacional sem permissão de crédito'),
        ('103', 'Isenção do ICMS no Simples Nacional para faixa de receita bruta'),
        ('300', 'Imune'),
        ('400', 'Não tributada pelo Simples Nacional'),
        ('201', 'Tributada pelo Simples Nacional com permissão de crédito e com cobrança do ICMS por Substituição Tributária'),
        ('202', 'Tributada pelo Simples Nacional sem permissão de crédito e com cobrança do ICMS por Substituição Tributária'),
        ('203', 'Isenção do ICMS nos Simples Nacional para faixa de receita bruta e com cobrança do ICMS por Substituição Tributária'),
        ('500', 'ICMS cobrado anteriormente por substituição tributária (substituído) ou por antecipação'),
        ('900', 'Outros')
    ]
    
    l10n_xma_cst_code = fields.Selection(options_cst_field, string='Tributação do ICMS', related="product_tmpl_id.l10n_xma_cst_code")

    options_cst_pis_field = [
        ('01', 'Operação Tributável (base de cálculo = valor da operação alíquota normal (cumulativo/não cumulativo))'),
        ('02', 'Operação Tributável (base de cálculo = valor da operação (alíquota diferenciada))'),
        ('03', 'Operação Tributável (base de cálculo = quantidade vendida x alíquota por unidade de produto)'),
        ('04', 'Operação Tributável (tributação monofásica (alíquota zero))'),
        ('05', 'Operação Tributável (Substituição Tributária)'),
        ('06', 'Operação Tributável (alíquota zero)'),
        ('07', 'Operação Isenta da Contribuição'),
        ('08', 'Operação Sem Incidência da Contribuição'),
        ('09', 'Operação com Suspensão da Contribuição'),
        ('99', 'Outras Operações'),
        ('49', 'Outras Operações de Saída'),
        ('50', 'Operação com Direito a Crédito - Vinculada Exclusivamente a Receita Tributada no Mercado Interno'),
        ('51', 'Operação com Direito a Crédito - Vinculada Exclusivamente a Receita Não Tributada no Mercado Interno'),
        ('52', 'Operação com Direito a Crédito - Vinculada Exclusivamente a Receita de Exportação'),
        ('53', 'Operação com Direito a Crédito - Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno'),
        ('54', 'Operação com Direito a Crédito - Vinculada a Receitas Tributadas no Mercado Interno e de Exportação'),
        ('55', 'Operação com Direito a Crédito - Vinculada a Receitas Não-Tributadas no Mercado Interno e de Exportação'),
        ('56', 'Operação com Direito a Crédito - Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno, e de Exportação'),
        ('60', 'Crédito Presumido - Operação de Aquisição Vinculada Exclusivamente a Receita Tributada no Mercado Interno'),
        ('61', 'Crédito Presumido - Operação de Aquisição Vinculada Exclusivamente a Receita Não Tributada no Mercado Interno'),
        ('62', 'Crédito Presumido - Operação de Aquisição Vinculada Exclusivamente a Receita de Exportação'),
        ('63', 'Crédito Presumido - Operación de Aquisição Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno'),
        ('64', 'Crédito Presumido - Operação de Aquisição Vinculada a Receitas Tributadas no Mercado Interno e de Exportação'),
        ('65', 'Crédito Presumido - Operação de Aquisição Vinculada a Receitas Não-Tributadas no Mercado Interno e de Exportação'),
        ('66', 'Crédito Presumido - Operação de Aquisição Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno, e de Exportação'),
        ('67', 'Crédito Presumido - Outras Operações'),
        ('70', 'Operação de Aquisição sem Direito a Crédito'),
        ('71', 'Operação de Aquisição com Isenção'),
        ('72', 'Operação de Aquisição com Suspensão'),
        ('73', 'Operação de Aquisição a Alíquota Zero'),
        ('74', 'Operação de Aquisição sem Incidência da Contribuição'),
        ('75', 'Operação de Aquisição por Substituição Tributária'),
        ('98', 'Outras Operações de Entrada')
    ]
    
    l10n_xma_cst_pis_code = fields.Selection(options_cst_pis_field, string='Código de Situação Tributária do PIS', related="product_tmpl_id.l10n_xma_cst_pis_code")


    options_cst_cofins_field = [
        ('01', 'Operação Tributável (base de cálculo = valor da operação alíquota normal (cumulativo/não cumulativo))'),
        ('02', 'Operação Tributável (base de cálculo = valor da operação (alíquota diferenciada))'),
        ('03', 'Operação Tributável (base de cálculo = quantidade vendida x alíquota por unidade de produto)'),
        ('04', 'Operação Tributável (tributação monofásica (alíquota zero))'),
        ('05', 'Operação Tributável (Substituição Tributária)'),
        ('06', 'Operação Tributável (alíquota zero)'),
        ('07', 'Operação Isenta da Contribuição'),
        ('08', 'Operação Sem Incidência da Contribuição'),
        ('09', 'Operação com Suspensão da Contribuição'),
        ('99', 'Outras Operações'),
        ('49', 'Outras Operações de Saída'),
        ('50', 'Operação com Direito a Crédito - Vinculada Exclusivamente a Receita Tributada no Mercado Interno'),
        ('51', 'Operação com Direito a Crédito - Vinculada Exclusivamente a Receita Não Tributada no Mercado Interno'),
        ('52', 'Operação com Direito a Crédito - Vinculada Exclusivamente a Receita de Exportação'),
        ('53', 'Operação com Direito a Crédito - Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno'),
        ('54', 'Operação com Direito a Crédito - Vinculada a Receitas Tributadas no Mercado Interno e de Exportação'),
        ('55', 'Operação com Direito a Crédito - Vinculada a Receitas Não-Tributadas no Mercado Interno e de Exportação'),
        ('56', 'Operação com Direito a Crédito - Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno, e de Exportação'),
        ('60', 'Crédito Presumido - Operação de Aquisição Vinculada Exclusivamente a Receita Tributada no Mercado Interno'),
        ('61', 'Crédito Presumido - Operação de Aquisição Vinculada Exclusivamente a Receita Não Tributada no Mercado Interno'),
        ('62', 'Crédito Presumido - Operação de Aquisição Vinculada Exclusivamente a Receita de Exportação'),
        ('63', 'Crédito Presumido - Operação de Aquisição Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno'),
        ('64', 'Crédito Presumido - Operação de Aquisição Vinculada a Receitas Tributadas no Mercado Interno e de Exportação'),
        ('65', 'Crédito Presumido - Operação de Aquisição Vinculada a Receitas Não-Tributadas no Mercado Interno e de Exportação'),
        ('66', 'Crédito Presumido - Operação de Aquisição Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno, e de Exportação'),
        ('67', 'Crédito Presumido - Outras Operações'),
        ('70', 'Operação de Aquisição sem Direito a Crédito'),
        ('71', 'Operação de Aquisição com Isenção'),
        ('72', 'Operação de Aquisição com Suspensão'),
        ('73', 'Operação de Aquisição a Alíquota Zero'),
        ('74', 'Operação de Aquisição sem Incidência da Contribuição'),
        ('75', 'Operação de Aquisição por Substituição Tributária'),
        ('98', 'Outras Operações de Entrada')
    ]
    
    l10n_xma_cst_cofins_code = fields.Selection(options_cst_cofins_field, string='Código de Situação Tributária do COFINS', related="product_tmpl_id.l10n_xma_cst_cofins_code")

    l10n_xma_cst_ipi_code = fields.Selection([
        ('00', 'Entrada com recuperação de crédito'),
        ('01', 'Entrada tributada com alíquota zero'),
        ('02', 'Entrada isenta'),
        ('03', 'Entrada não-tributada'),
        ('04', 'Entrada imune'),
        ('05', 'Entrada com suspensão'),
        ('49', 'Outras entradas'),
        ('50', 'Saída tributada'),
        ('51', 'Saída tributada com alíquota zero'),
        ('52', 'Saída isenta'),
        ('53', 'Saída não-tributada'),
        ('54', 'Saída imune'),
        ('55', 'Saída com suspensão'),
        ('99', 'Outras saídas')
    ], string='Código de Situação Tributária do IPI', related="product_tmpl_id.l10n_xma_cst_ipi_code") 
    
    l10n_xma_is_fuel = fields.Boolean(string="Es combustible.", related="product_tmpl_id.l10n_xma_is_fuel")
    
    current_country_id = fields.Many2one(
        'res.country',
        compute='get_current_country_id_from_company',
        string='País',
        help="País de la empresa",
    )

    l10n_xma_isdiscount = fields.Boolean(string="Es descuento",
        related="product_tmpl_id.l10n_xma_isdiscount",
        readonly=False
    )
    
    l10n_xma_type_discount = fields.Selection([
            ('D', 'Descuento'),
            ('R', 'Recargo')
        ], string='Tipo de descuento',
        related="product_tmpl_id.l10n_xma_type_discount",
        readonly=False
    )


    def get_current_country_id_from_company(self):
        for rec in self:
            rec.current_country_id = self.env.company.country_id.id