from odoo import models,api,fields,_
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import xlwt
import base64
from io import BytesIO
from datetime import date,time,datetime

SALE_TYPE = {'credit':'Credit Sale','cash':'Cash Sale','approval':'Approval Sale'}


class ReportWizard(models.TransientModel):

    _name = 'report.wizard'

    date_from = fields.Date('Start Date',default = fields.Datetime.now())
    date_to = fields.Date('End Date',default = fields.Datetime.now())
    state = fields.Selection([('choose', 'choose'), ('get', 'get')],
                             default='choose')
    report = fields.Binary('Prepared file', filters='.xls', readonly=True)
    name =  fields.Char('File Name', size=32)

    @api.multi
    def generate_report(self):
        self.ensure_one()

        wb1 = xlwt.Workbook(encoding='utf-8')
        ws1 = wb1.add_sheet('Sales Report')
        fp  = BytesIO()


        #Content/Text style
        header_content_style = xlwt.easyxf("font: name Helvetica size 20 px, bold 1, height 170;")
        sub_header_style = xlwt.easyxf("font: name Helvetica size 10 px, bold 1, height 170;")
        sub_header_content_style = xlwt.easyxf("font: name Helvetica size 10 px, height 170;")
        line_content_style = xlwt.easyxf("font: name Helvetica, height 170;")
        row = 1
        col = 0
        ws1.row(row).height = 500
        ws1.write_merge(row,row, 3,7, "Sales Report", header_content_style)
        row += 2
        ws1.write(row, col+1, "From :", sub_header_style)
        ws1.write(row, col+2, datetime.strftime(datetime.strptime(self.date_from,DEFAULT_SERVER_DATE_FORMAT),"%d/%m/%Y"), sub_header_content_style)
        row += 1
        ws1.write(row, col+1, "To :", sub_header_style)
        ws1.write(row, col+2, datetime.strftime(datetime.strptime(self.date_to,DEFAULT_SERVER_DATE_FORMAT),"%d/%m/%Y"), sub_header_content_style)
        row += 1
        for key, value in SALE_TYPE.items():
            ws1.write(row, col + 1, value, sub_header_style)
            row +=2
            sale_details = self.env['sale.order'].search([('state','in',['sale','done']),('date_order','<=',self.date_to),('date_order','>=',self.date_from),('sale_type','=',key)])
            sale_lines = sale_details.mapped('order_line')
            products = sale_lines.mapped('product_id')
            for product in products:
                sale_line_pr = sale_lines.filtered(lambda  r:r.product_id.id==product.id)
                total_qty = sum(sale_line_pr.mapped('product_uom_qty'))
                col=0
                ws1.write(row,col+1,product.name,line_content_style)
                ws1.write(row,col+2,total_qty,line_content_style)
                ws1.write(row,col+3,product.virtual_available,line_content_style)

                row +=1
            row +=1


        wb1.save(fp)
        out = base64.encodestring(fp.getvalue())
        self.write({'state': 'get', 'report': out, 'name':'Sale Report.xls'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'report.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
