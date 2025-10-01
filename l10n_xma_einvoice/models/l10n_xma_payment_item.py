from odoo import fields, models, api, _, tools


"""
    {
        "@BienOServicio": "B" if line.product_id.detailed_type in ("product","consu") else "S",
        "@NumeroLinea": linea,
        "dte:Cantidad": "%s" % line.quantity,
        "dte:UnidadMedida": "%s" % "UNI",#line.product_uom_id.code if line.product_uom_id.code != False else 'UNI',
        "dte:Descripcion": "%s" % line.name,
        "dte:PrecioUnitario": "%s" % line.price_unit,
        "dte:Precio": "%s" % round(abs(line.price_unit * line.quantity),decimal_places),
        "dte:Descuento": "%s" % '0.0',
        "dte:Total": "%s" % round(line.price_total,decimal_places)
    }
"""

class XmaPaymentItem(models.Model):
    _name = "l10n_xma.payment.item"
    
    
    product_id = fields.Many2one("product.product", string="Producto/Servicio")
    name = fields.Char(string="Descripcion")
    quantity = fields.Float(string="Cantidad")
    product_uom_id = fields.Many2one("uom.uom", string="Unidad de medida")
    price_unit = fields.Float(string="Precio Unitario")
    price_total = fields.Float(string="Total")
    payment_id = fields.Many2one("account.payment",string="Pago")