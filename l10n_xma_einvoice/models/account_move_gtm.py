# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import json
from lxml.objectify import fromstring
import base64
from datetime import datetime, timedelta
from odoo.tools import float_round
from odoo.exceptions import UserError, ValidationError
import time
import re
from random import choice, randint
from xml.etree import ElementTree as ET
from io import BytesIO, StringIO
from xml.dom import minidom
from num2words import num2words
from MqttLibPy.client import MqttClient
import logging
import re
import json
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"
    
    
    def button_cancel_json_gtm(self):
        if not self.l10n_xma_cancel_motive:
            raise ValidationError(_('Error de Cancelacion:\nDebe llenar primero el campo de motivo de cancelacion.'))
        if self.l10n_xma_einvoice_status == 'signed':
            self.cancel_json_gtm()
            time.sleep(1)
            self.refresh_account_move_xma()
            return True
        else:
            raise ValidationError(_('Error de Cancelacion:\nEsta factura no ha sido timbrada aun.'))
        
    def cancel_json_gtm(self, payment=False):
        cancel_json_gtm = False 
        cancel_json_gtm = self.generate_cancel_json_l10n_gtm(payment)
        xml_json = {"GT": cancel_json_gtm}
        company = self.get_company()
        uuid = company.company_name
        rfc = re.sub(r"\D", "", self.company_id.partner_id.vat)
        country = self.company_id.partner_id.country_id.code.lower()
        xml_json = {"from":uuid, "data":xml_json}
        mqtt_client = MqttClient("api.xmarts.com", 1883, prefix=f"uuid/{uuid}/rfc/{rfc}/country/{country}/", encryption_key=company.key)
        mqtt_client.send_message_serialized(
            [xml_json],
            f"uuid/{uuid}/rfc/{rfc}/country/{country}/stamp",  
            valid_json=True, 
            secure=True
        )

        self.env.cr.commit()
        time.sleep(1) 
        return True
        
        
    def generate_cancel_json_l10n_gtm(self, payment=False):
        for move in self:
            current_dt = datetime.now()
            date_time = fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), current_dt)
            cancel_date = date_time.strftime('%Y-%m-%dT%H:%M:%S')
            invoice_date = move.l10n_xma_date_post.strftime('%Y-%m-%dT%H:%M:%S')
            json_gtm = [{
                            "dte:GTAnulacionDocumento": {
                                "@xmlns:ds": "http://www.w3.org/2000/09/xmldsig#",
                                "@xmlns:dte": "http://www.sat.gob.gt/dte/fel/0.1.0",
                                "@xmlns:n1": "http://www.altova.com/samplexml/other-namespace",
                                "@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                                "@Version": "0.1",
                                "dte:SAT": {
                                    "dte:AnulacionDTE": {
                                        "@ID": "DatosCertificados",
                                        "dte:DatosGenerales": {
                                            "@FechaEmisionDocumentoAnular": "%s" % invoice_date,
                                            "@FechaHoraAnulacion": "%s" % cancel_date,
                                            "@ID": "DatosAnulacion",
                                            "@IDReceptor": "%s" % move.partner_id.vat,
                                            "@MotivoAnulacion": "%s" % move.l10n_xma_cancel_motive,
                                            "@NITEmisor": "%s" % move.company_id.vat,
                                            "@NumeroDocumentoAAnular": "%s" % move.l10n_xma_einvoice_numero
                                        }
                                    }
                                }
                            }
                        }]
            json_complete = {
                "id":self.id if not payment else payment.id,
                "uuid_client":self.company_id.uuid_client,
                "doc_type": "FGT",
                "rfc":re.sub(r"\D", "", self.company_id.vat),
                "data":json_gtm,
                "UsuarioFirma": "%s" % self.company_id.xma_infile_user, #"110659988",
                "LlaveFirma": "%s" % self.company_id.xma_token_signer, #"d72b7bfef3fbab468ba627730c0684fc",
                "UsuarioApi": "%s" % self.company_id.xma_infile_user, #"110659988",
                "LlaveApi": "%s" % self.company_id.xma_api_key, #"975A95F15C59A715B6B04640632CFE32",
                "url": "%s" % self.company_id.xma_api_url, #"https://certificador.feel.com.gt/fel/procesounificado/transaccion/v2/xml",
                "cancel": True,
                "payment": False if not payment else True
                
            }
            return json_complete
        
        
        

    def button_send_json_gtm(self):
        if self.l10n_xma_einvoice_status != 'signed':
            self.send_json_gtm()
            time.sleep(1)
            # self.refresh_account_move_xma()
            return True
        else:
            raise ValidationError(_('Error de timbrado: Esta factura ya esta timbrada.'))

    def send_json_gtm(self, itemlines=False, payment=False):
        xml_json_gtm = False  
        xml_json_gtm = self.generate_json_l10n_gtm(itemlines, payment)
        xml_json = {"GT": xml_json_gtm}
        company = self.get_company()
        uuid = company.company_name
        rfc = re.sub(r"\D", "", self.company_id.partner_id.vat)
        country = self.company_id.partner_id.country_id.code.lower()
        xml_json = {"from":uuid, "data":xml_json}
        json_formatted_str = json.dumps(xml_json, indent=2)
        _logger.info(f"\nJSON GTM |||||||||\n{json_formatted_str}\n||||||||||||||||||||")
        mqtt_client = MqttClient("api.xmarts.com", 1883, prefix=f"uuid/{uuid}/rfc/{rfc}/country/{country}/", encryption_key=company.key)
        mqtt_client.send_message_serialized(
            [xml_json],
            f"uuid/{uuid}/rfc/{rfc}/country/{country}/stamp",  
            valid_json=True, 
            secure=True
        )

        self.env.cr.commit()
        time.sleep(1) 
        return True

    def xma_get_tax_force_sign(self):
        self.ensure_one()
        return -1 if self.move_type in ('out_invoice', 'in_refund', 'out_receipt') else 1

    def xma_compute_base_line_taxes(self, base_line):
        move = base_line.move_id

        if move.is_invoice(include_receipts=True):
            handle_price_include = True
            sign = -1 if move.is_inbound() else 1
            quantity = base_line.quantity
            is_refund = move.move_type in ('out_refund', 'in_refund')
            price_unit_wo_discount = sign * base_line.price_unit * (1 - (base_line.discount / 100.0))
        else:
            handle_price_include = False
            quantity = 1.0
            tax_type = base_line.tax_ids[0].type_tax_use if base_line.tax_ids else None
            is_refund = (tax_type == 'sale' and base_line.debit) or (tax_type == 'purchase' and base_line.credit)
            price_unit_wo_discount = base_line.amount_currency

        return base_line.tax_ids._origin.with_context(force_sign=move.xma_get_tax_force_sign()).compute_all(
            price_unit_wo_discount,
            currency=base_line.currency_id,
            quantity=quantity,
            product=base_line.product_id,
            partner=base_line.partner_id,
            is_refund=is_refund,
            handle_price_include=handle_price_include,
            include_caba_tags=move.always_tax_exigible,
        )


    def generate_json_l10n_gtm(self, itemlines=False, payment=False):
        for move in self:
            # l10n_latam_document_type_id
            l10n_latam_document_type_id = False
            if payment != False:
                l10n_latam_document_type_id = payment.l10n_latam_document_type_id
            else:
                l10n_latam_document_type_id = move.l10n_latam_document_type_id
            current_dt = datetime.now()
            date_time = fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), current_dt)
            invoice_date = date_time.strftime('%Y-%m-%dT%H:%M:%S')
            move.l10n_xma_date_post = current_dt
            decimal_places = move.currency_id.decimal_places
            export_ok = False
            if move.partner_id.country_id.code != 'GT':
                export_ok = True
            litems = []
            linea=0   
            xlines = False
            grantotal = 0.00
            if itemlines != False:
                xlines = itemlines
            else:
                xlines = move.invoice_line_ids
            RetencionISR=0.00
            RetencionIVA=0.00
            TotalIVA=0.00
            for line in xlines:
                limpuestos = []
                if l10n_latam_document_type_id.code not in ("NABN", "RANT"):
                    for key, value in move.xma_compute_base_line_taxes(line).items():
                        if 'taxes' in key:
                            for tx in value:
                                taxes = self.env['account.tax'].search([('id','=',tx['id'])],limit=1) 
                                if "IVA" in taxes.l10n_xma_edi_tax_type_id.name and taxes.amount >= 0:
                                    TotalIVA += round(abs(tx['amount']),decimal_places)
                                    limpuestos.append({
                                        "dte:NombreCorto": "%s" % taxes.l10n_xma_edi_tax_type_id.name,
                                        "dte:CodigoUnidadGravable": "1",
                                        "dte:MontoGravable": "%s" % round(abs(tx['base']),decimal_places),
                                        "dte:MontoImpuesto": "%s" % round(abs(tx['amount']),decimal_places)
                                    })
                                elif "IVA" in taxes.l10n_xma_edi_tax_type_id.name and taxes.amount < 0:
                                    RetencionIVA += round(abs(tx['amount']),decimal_places)
                                elif "ISR" in taxes.l10n_xma_edi_tax_type_id.name and taxes.amount < 0:
                                    RetencionISR += round(abs(tx['amount']),decimal_places)
                linea+=1
                if l10n_latam_document_type_id.code not in ("NABN", "RANT"):
                    litems.append({
                                    "@BienOServicio": "B" if line.product_id.type in ("product","consu") else "S",
                                    "@NumeroLinea": linea,
                                    "dte:Cantidad": "%s" % line.quantity,
                                    "dte:UnidadMedida": "%s" % "UNI",#line.product_uom_id.code if line.product_uom_id.code != False else 'UNI',
                                    "dte:Descripcion": "%s" % line.name,
                                    "dte:PrecioUnitario": "%s" % line.price_unit,
                                    "dte:Precio": "%s" % round(abs(line.price_unit * line.quantity),decimal_places),
                                    "dte:Descuento": "%s" % round(abs((line.price_unit * line.quantity) * (line.discount / 100.0)),decimal_places) if line.discount > 0 else '0.0',
                                    "dte:Impuestos": {
                                        "dte:Impuesto": limpuestos 
                                    },
                                    "dte:Total": "%s" % round(abs(line.price_unit * line.quantity),decimal_places)
                                })
                    grantotal += round(abs(line.price_unit * line.quantity),decimal_places)
                else:
                    litems.append({
                                    "@BienOServicio": "B" if line.product_id.type in ("product","consu") else "S",
                                    "@NumeroLinea": linea,
                                    "dte:Cantidad": "%s" % line.quantity,
                                    "dte:UnidadMedida": "%s" % "UNI",#line.product_uom_id.code if line.product_uom_id.code != False else 'UNI',
                                    "dte:Descripcion": "%s" % line.name,
                                    "dte:PrecioUnitario": "%s" % line.price_unit,
                                    "dte:Precio": "%s" % round(abs(line.price_unit * line.quantity),decimal_places),
                                    "dte:Descuento": "%s" % '0.0',
                                    "dte:Total": "%s" % round(line.price_subtotal,decimal_places)
                                })
                    grantotal += round(abs(line.price_unit * line.quantity),decimal_places)
            
            if l10n_latam_document_type_id.code not in ("NABN","RANT"):
                totalimpuestos = {
                                "dte:TotalImpuestos": {
                                    "dte:TotalImpuesto": {
                                        "@NombreCorto": "IVA",
                                        "@TotalMontoImpuesto": "%s" % TotalIVA
                                    }
                                },
                                "dte:GranTotal": "%s" % round(grantotal,decimal_places)
                            }
                # tax_totals = move.tax_totals
                # print(f"TAX TOTALS XXX {tax_totals}")
                # tax_totals = tax_totals['groups_by_subtotal'].items()
                # # _logger.info(f"TAX TOTALS: {tax_totals}")
                # RetencionISR=0.00
                # RetencionIVA=0.00
                # totalimpuestos = {} 
                # for taxes in tax_totals:
                #     for tax in taxes[1]:
                #         if 'IVA' in tax['tax_group_name'] and tax['tax_group_amount'] >=0:
                #             totalimpuestos = {
                #                             "dte:TotalImpuestos": {
                #                                 "dte:TotalImpuesto": {
                #                                     "@NombreCorto": "IVA",
                #                                     "@TotalMontoImpuesto": "%s" % round(abs(tax['tax_group_amount']),decimal_places)
                #                                 }
                #                             },
                #                             "dte:GranTotal": "%s" % round(grantotal,decimal_places)
                #                         }
                #         elif 'IVA' in tax['tax_group_name'] and tax['tax_group_amount'] < 0:
                #             RetencionIVA+= round(abs(tax['tax_group_amount']),decimal_places)
                #         elif "ISR" in tax['tax_group_name'] and tax['tax_group_amount'] < 0:
                #             RetencionISR += round(abs(tax['tax_group_amount']),decimal_places)
            else:
                totalimpuestos = {
                                "dte:GranTotal": "%s" % round(move.amount_untaxed if not payment else payment.amount,decimal_places)
                            }
            
            frases = []
            if l10n_latam_document_type_id.code in('FACT','NCRE') and export_ok == True:
                fs = self.env['l10n_xma.fel_phrase'].sudo().search([('scenario_code','=',1),(('typeprase_code','in',('1','4')))])
                for frase in fs:
                    frases.append({'@CodigoEscenario':frase.scenario_code,'@TipoFrase':frase.typeprase_code}) 
            elif move.move_type =='out_invoice' and l10n_latam_document_type_id.code == 'FACT' and move.currency_id.id == self.env.ref('base.USD').id and export_ok == False:
                fs = self.env['l10n_xma.fel_phrase'].sudo().search([('scenario_code','=',19),(('typeprase_code','=','4'))]) 
                for frase in fs:
                    frases.append({'@CodigoEscenario':frase.scenario_code,'@TipoFrase':frase.typeprase_code}) 
                for frase in move.company_id.l10n_xma_phrase_ids:
                    frases.append({'@CodigoEscenario':frase.scenario_code,'@TipoFrase':frase.typeprase_code}) 
            elif l10n_latam_document_type_id.code == "RANT":
                frases.append({'@CodigoEscenario':6,'@TipoFrase':9}) 
                # for frase in payment.l10n_xma_phrase_ids:
                #     frases.append({'@CodigoEscenario':frase.scenario_code,'@TipoFrase':frase.typeprase_code}) 
            else:
                for frase in move.company_id.l10n_xma_phrase_ids:
                    frases.append({'@CodigoEscenario':frase.scenario_code,'@TipoFrase':frase.typeprase_code}) 
            
            tipoespecial = False
            if move.amount_total >=2500 and move.partner_id.l10n_latam_identification_type_id.name == "CUI" and l10n_latam_document_type_id.code == "FESP":
                tipoespecial = "CUI"
            elif move.amount_total >=2500 and move.partner_id.l10n_latam_identification_type_id.name == "CUI" and export_ok != True:
                tipoespecial = "CUI"
            elif move.move_type =='out_invoice' and l10n_latam_document_type_id.code == 'FACT' and export_ok == True:
                tipoespecial = "EXT"
            elif move.move_type =='out_invoice' and l10n_latam_document_type_id.code == 'FACT' and move.currency_id.id == self.env.ref('base.USD').id and export_ok == False:
                tipoespecial = "EXT"
            elif move.move_type =='out_refund' and l10n_latam_document_type_id.code =='NCRE' and export_ok == True:
                tipoespecial = "EXT"
                
            complemento = False
            if l10n_latam_document_type_id.code in ('NCRE','NDEB'):
                complemento = {
                                "dte:Complemento": {
                                    "@IDComplemento": 1,
                                    "@NombreComplemento": "NOTA %s" % "CREDITO" if l10n_latam_document_type_id.code == "NCRE" else "DEBITO",
                                    "@URIComplemento": "http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0",
                                    "cno:ReferenciasNota": {
                                        "@xmlns:cno": "http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0",
                                        "@FechaEmisionDocumentoOrigen": fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), move.reversed_entry_id.l10n_xma_date_post).strftime('%Y-%m-%d') if move.l10n_latam_document_type_id.code == 'NCRE' else fields.Datetime.context_timestamp(self.with_context(tz=self.env.user.tz), move.debit_origin_id.l10n_xma_date_post).strftime('%Y-%m-%d'),#"2024-09-12",
                                        "@MotivoAjuste": move.ref,
                                        "@NumeroAutorizacionDocumentoOrigen": move.reversed_entry_id.l10n_xma_einvoice_numero if l10n_latam_document_type_id.code == 'NCRE' else move.debit_origin_id.l10n_xma_einvoice_numero,#"BD201010-1372-4D09-93D1-9F040E2955C9",
                                        "@NumeroDocumentoOrigen": move.reversed_entry_id.l10n_xma_uuid_invoice if l10n_latam_document_type_id.code == 'NCRE' else move.debit_origin_id.l10n_xma_uuid_invoice,#"PRUEBAS",
                                        "@SerieDocumentoOrigen": move.reversed_entry_id.l10n_xma_einvoice_serie if l10n_latam_document_type_id.code == 'NCRE' else move.debit_origin_id.l10n_xma_einvoice_serie,#"326257929",
                                        "@Version": "0.1"
                                    }
                                }
                            }
            elif l10n_latam_document_type_id.code == "FESP":
                complemento = {
                                "dte:Complemento": {
                                    "@IDComplemento": "Especial",
                                    "@NombreComplemento": "Especial",
                                    "@URIComplemento": "http://www.sat.gob.gt/face2/ComplementoFacturaEspecial/0.1.0",
                                    "cfe:RetencionesFacturaEspecial": {
                                        "@xmlns:cfe": "http://www.sat.gob.gt/face2/ComplementoFacturaEspecial/0.1.0",
                                        "@Version": "1",
                                        "cfe:RetencionISR": "%s" % RetencionISR,
                                        "cfe:RetencionIVA": "%s" % RetencionIVA,
                                        "cfe:TotalMenosRetenciones": "%s" % round(move.amount_total ,decimal_places)
                                    }
                                }
                            }
            else:
                complemento = []
            
            json_gtm = [{"dte:GTDocumento": {
                            "@xmlns:ds": "http://www.w3.org/2000/09/xmldsig#",
                            "@xmlns:dte": "http://www.sat.gob.gt/dte/fel/0.2.0",
                            "@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                            "@Version": "0.1",
                            "@xsi:schemaLocation": "http://www.sat.gob.gt/dte/fel/0.2.0",
                            "dte:SAT": {
                                "@ClaseDocumento": "dte",
                                "dte:DTE": {
                                    "@ID": "DatosCertificados",
                                    "dte:DatosEmision": {
                                        "@ID": "DatosEmision",
                                        "dte:DatosGenerales": {
                                            "@CodigoMoneda": "%s" % move.currency_id.name,
                                            "@FechaHoraEmision": "%s" % invoice_date,
                                            "@Tipo": "%s" % l10n_latam_document_type_id.code,
                                        },
                                        "dte:Emisor": {
                                            "@AfiliacionIVA": "%s" % move.company_id.partner_id.l10n_xma_taxpayer_type_id.code,
                                            "@CodigoEstablecimiento": "%s" % l10n_latam_document_type_id.l10n_xma_branch, # Revisar que es el codigo centro o de establecimiento, Tomar branch de tipo de doc
                                            "@CorreoEmisor": "%s" % move.company_id.email,#"demo@demo.com.gt",
                                            "@NITEmisor": "%s" % move.company_id.vat , #"110659988",
                                            "@NombreComercial": "%s" % move.company_id.partner_id.commercial_name, #"DEMO", #USAR ESTOS DATOS SI ESTA EN MODO TEST
                                            "@NombreEmisor": "%s" % move.company_id.partner_id.name, #"DEMO, SOCIEDAD ANONIMA", #USAR ESTOS DATOS SI ESTA EN MODO TEST
                                            "dte:DireccionEmisor": {
                                                "dte:Direccion": "%s" % move.company_id.street, #"CUIDAD",
                                                "dte:CodigoPostal": "%s" % move.company_id.zip, #"01001",
                                                "dte:Municipio": "%s" % move.company_id.city, #"GUATEMALA",
                                                "dte:Departamento": "%s" % move.company_id.state_id.name, #"GUATEMALA",
                                                "dte:Pais": "%s" % move.company_id.country_id.code, #"GT"
                                            },
                                        },
                                        "dte:Receptor": {
                                            "@CorreoReceptor": "%s" % move.partner_id.email, #"demo@demo.com",
                                            "@IDReceptor": "%s" % move.partner_id.vat, #"CF",
                                            "@NombreReceptor": "%s" % move.partner_id.name, #"Consumidor Final",
                                            "dte:DireccionReceptor": {
                                                "dte:Direccion": "%s" % move.partner_id.street, #"CUIDAD",
                                                "dte:CodigoPostal": "%s" % move.partner_id.zip, #"01001",
                                                "dte:Municipio": "%s" % move.partner_id.city, #"GUATEMALA",
                                                "dte:Departamento": "%s" % move.partner_id.state_id.name, #"GUATEMALA",
                                                "dte:Pais": "%s" % move.partner_id.country_id.code, #"GT"
                                            }
                                        },
                                        "dte:Frases": {
                                            "dte:Frase": frases
                                        } if l10n_latam_document_type_id.code not in ("FESP","NABN") else [],
                                        "dte:Items": {
                                            "dte:Item": litems
                                        },
                                        "dte:Totales": totalimpuestos,
                                        # "dte:Totales":{
                                        #     "dte:GranTotal": "%s" % round(move.amount_total,decimal_places)
                                        # },
                                        "dte:Complementos": complemento
                                    }
                                },
                                # "dte:Adenda":{
                                #     "tipopago": "CONTADO",
                                #     "factura_referencia": "7C279AC7-258C-4265-A796-95E41E2712CB",
                                #     "cliente": "%s" % move.partner_id.vat} if move.l10n_latam_document_type_id.code == "NABN" else []
                            }
                        }
                    }]
            """
                <dte:Adenda>
                    <CorrelativoInterno>FPM10/2024/02137</CorrelativoInterno>
                    <OrdenVenta>S04668</OrdenVenta>
                    <Vendedor>Rossana Ruiz</Vendedor>
                    <Tipodecambio>1.0</Tipodecambio>
                    <GuiaPadre>ENV. 9961</GuiaPadre><GuiaHija />
                    <CantidadConsolidada />
                    <PrecioConsolidado />
                    <TotalConsolidado />
                    <DescripcionConsolidada />
                    <Valor3 /><Valor4 /><Valor6 />
                </dte:Adenda>
            """
            if tipoespecial != False:
                json_gtm[0]['dte:GTDocumento']['dte:SAT']['dte:DTE']['dte:DatosEmision']['dte:Receptor']['@TipoEspecial'] = tipoespecial
            if l10n_latam_document_type_id.code == "RANT":
                json_gtm[0]['dte:GTDocumento']['dte:SAT']['dte:DTE']['dte:DatosEmision']['dte:DatosGenerales']['@TipoPersoneria'] = "698"

            json_complete = {
                "id":self.id if not payment else payment.id,
                "uuid_client":self.company_id.uuid_client,
                "doc_type": "FGT",
                "rfc":re.sub(r"\D", "", self.company_id.vat),
                "data":json_gtm,
                "UsuarioFirma": "%s" % self.company_id.xma_infile_user, #"110659988",
                "LlaveFirma": "%s" % self.company_id.xma_token_signer, #"d72b7bfef3fbab468ba627730c0684fc",
                "UsuarioApi": "%s" % self.company_id.xma_infile_user, #"110659988",
                "LlaveApi": "%s" % self.company_id.xma_api_key, #"975A95F15C59A715B6B04640632CFE32",
                "url": "%s" % self.company_id.xma_api_url, #"https://certificador.feel.com.gt/fel/procesounificado/transaccion/v2/xml",
                "cancel": False,
                "payment": False if not payment else True
            }
            return json_complete