from odoo import models,fields,api,_

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import xlwt
import base64
from io import BytesIO
from datetime import date,time,datetime

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_brand = fields.Many2one(related='product_id.product_brand_id')


class InvoiceXLSWizard(models.Model):

    _name = 'purchase.popup'

    #fields to generate xls

    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    vendor_name = fields.Many2one('res.partner', required=True)

    # fields for download xls

    state = fields.Selection([('choose', 'choose'), ('get', 'get')],
                             default='choose')
    report = fields.Binary('Prepared file', filters='.xls', readonly=True)
    name =  fields.Char('File Name', size=32)


    @api.multi
    def generate_xls_report(self):

        self.ensure_one()

        wb1 = xlwt.Workbook(encoding='utf-8')
        ws1 = wb1.add_sheet('Purchase Details')
        fp  = BytesIO()


        #Content/Text style
        header_content_style = xlwt.easyxf("font: name Helvetica size 20 px, bold 1, height 170;")
        sub_header_style = xlwt.easyxf("font: name Helvetica size 10 px, bold 1, height 170;")
        sub_header_content_style = xlwt.easyxf("font: name Helvetica size 10 px, height 170;")
        line_content_style = xlwt.easyxf("font: name Helvetica, height 170;")
        row = 1
        col = 0
        ws1.row(row).height = 500
        ws1.write_merge(row,row, 3,7, "Purchase Order information", header_content_style)
        row += 2
        ws1.write(row, col+1, "From :", sub_header_style)
        ws1.write(row, col+2, datetime.strftime(datetime.strptime(self.date_from,DEFAULT_SERVER_DATE_FORMAT),"%d/%m/%Y"), sub_header_content_style)
        row += 1
        ws1.write(row, col+1, "To :", sub_header_style)
        ws1.write(row, col+2, datetime.strftime(datetime.strptime(self.date_to,DEFAULT_SERVER_DATE_FORMAT),"%d/%m/%Y"), sub_header_content_style)
        row += 1
        tier_count = self.env['tier.brand'].search([])
        ws1.write(row, col + 1, "Vendor", sub_header_style)
        ws1.write(row, col + 2, "Brand", sub_header_style)
        ws1.write(row, col + 3, "Total Purchase", sub_header_style)
        i=4
        z=0
        for data in tier_count:
            ws1.write(row, col + i, (data.tier_name1), sub_header_style)
            i +=1
            k = i


        z=k
        for data in tier_count:
            ws1.write(row, col + k, (data.tier_name1,"Rebate %"), sub_header_style)
            k+=1

        j=k-1

        ws1.write(row, col + j+1, "Total Rebate%", sub_header_style)

        row += 1

        #Searching for vendor purchase orders

        purchase_details = self.env['purchase.order'].search([('state','=','purchase'),('date_order','<=',self.date_to),('date_order','>=',self.date_from),('partner_id','=',self.vendor_name.id),('product_id.product_brand_id.is_mcb','=',True)])
        po_lines = purchase_details.mapped('order_line')
        brands = po_lines.mapped('product_brand')
        for brand in brands:
            brand_po_lines = po_lines.filtered(lambda r:r.product_brand.id==brand.id)
            total_purchase = sum(brand_po_lines.mapped('price_subtotal'))
            tier_amount = brand.mcb


            col=0
            ws1.write(row,col+1,self.vendor_name.name,line_content_style)
            ws1.write(row,col+2,brand.name,line_content_style)
            ws1.write(row,col+3,total_purchase,line_content_style)


            # to insert tier amount
            k = 4
            for data in tier_amount:
                ws1.write(row, col+k, (data.amount), line_content_style)
                k +=1



            # to insert the rebate percentage
            p =z-1
            for data in tier_amount:
                ws1.write(row,p+1,(data.rebate),line_content_style)
                p+=1



            #to insert total rebate

            total_rebate_per = 0
            tier_count = len(tier_amount)
            for data in tier_amount.sorted(key=lambda r: r.amount,reverse=True):
                if total_purchase < data.amount:
                    if tier_count == 1:
                        total_rebate_per = int(total_purchase) * (int(data.rebate) / 100)
                        break
                    else:
                        tier_count-=1
                else:
                    total_rebate_per = int(total_purchase) * (int(data.rebate) / 100)
                    break
            ws1.write(row, j + 1, (total_rebate_per), line_content_style)

            row +=1

        row +=1

        wb1.save(fp)
        out = base64.encodestring(fp.getvalue())
        self.write({'state': 'get', 'report': out, 'name':'purchase_order_detail.xls'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.popup',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
