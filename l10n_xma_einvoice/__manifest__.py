# -*- coding: utf-8 -*-
{
    'name': "Facturacion Electronica",

    'summary': """
        El objetivo de este modulo es contar con todos los elementos base 
        que se requieren para llevar acabo la facturación electrónica en varios países de Latinoamérica, como son: 
        México, República  Dominicana,  Paraguay, Perú y Chile.""",

    'description': """ 
    """,

    'author': "Xmarts Group LLC",
    'website': "https://www.xmarts.com",
    'category': 'Account',
    'version': '18.0.0.1',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'base_address_extended',
        'account',
        'l10n_latam_invoice_document', 
        'stock',
        'xma_core'
    ],

    'data': [
        "security/ir.model.access.csv",
        "views/account_move.xml",
        "wizard/wizard_cancel.xml",
        "views/res_config_settings.xml",
    ],
}
