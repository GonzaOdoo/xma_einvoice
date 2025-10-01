from odoo import api, fields, models, _
import base64

class L10nXmaSendXmlDo(models.TransientModel):
    _name = 'l10n_xma.send.xml.do'
    _description = 'Send XML to Xmarts apis'


    xml_file = fields.Binary(string="Archivo")


    def send_xmla_to_api(self):
        # send xml to api
        move = self.env['account.move'].browse(self._context['active_ids'])
        print(move.name)
        xml_returned = move.get_xml_data_to_format_ap_co(self.xml_file)
        print(xml_returned)
        xml_byte = xml_returned['xml'].encode('utf-8')
        xml =  base64.b64encode(xml_byte)
        print(xml)
        xml_attachment = self.env['ir.attachment'].create({
            'name': xml_returned['xml_name'],
            'type': 'binary',
            'datas':xml,
            'res_model': 'account.move',
            'res_id': move.id,
            'mimetype': 'application/xml'
        })
        move.message_post(
            body="%s" % xml_returned['response'], 
            attachment_ids=[xml_attachment.id], 
            body_is_html=True, 
            message_type='comment', 
            subtype_xmlid='mail.mt_comment')

        pass

class L10nXmaSendXmlDoAC(models.TransientModel):
    _name = 'l10n_xma.send.xml.ac'
    _description = 'Send XML to Xmarts apis'


    xml_file = fields.Binary(string="Archivo")


    def send_xmla_to_api(self):
        # send xml to api
        move = self.env['account.move'].browse(self._context['active_ids'])
        print(move.name)
        xml_returned = move.get_xml_data_to_format_ac_re(self.xml_file)
        print(xml_returned)
        xml_byte = xml_returned['xml'].encode('utf-8')
        xml =  base64.b64encode(xml_byte)
        print(xml)
        xml_attachment = self.env['ir.attachment'].create({
            'name': xml_returned['xml_name'],
            'type': 'binary',
            'datas':xml,
            'res_model': 'account.move',
            'res_id': move.id,
            'mimetype': 'application/xml'
        })
        move.message_post(
            body="Acuse de Recibo", 
            attachment_ids=[xml_attachment.id], 
            body_is_html=True, 
            message_type='comment', 
            subtype_xmlid='mail.mt_comment')






