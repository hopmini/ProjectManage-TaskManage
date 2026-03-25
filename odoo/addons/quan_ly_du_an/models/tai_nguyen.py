# -*- coding: utf-8 -*-
from odoo import models, fields, api

class DuAnTaiNguyen(models.Model):
    _name = 'quan_ly.du_an.resource'
    _description = 'Tài nguyên dự án'

    du_an_id = fields.Many2one('quan_ly.du_an', string='Dự án', ondelete='cascade')
    name = fields.Char(string='Tên tài nguyên', required=True)
    type = fields.Selection([
        ('hardware', 'Phần cứng'),
        ('software', 'Phần mềm'),
        ('human', 'Nhân lực thuê ngoài'),
        ('other', 'Khác')
    ], string='Loại', default='hardware')
    quantity = fields.Float(string='Số lượng', default=1.0)
    unit_price = fields.Float(string='Đơn giá')
    total_cost = fields.Float(string='Thành tiền', compute='_compute_total', store=True)

    workload_percent = fields.Integer(string='Công suất tải (%)', default=50)
    resource_capacity_html = fields.Html(compute='_compute_capacity_html')

    @api.depends('quantity', 'unit_price')
    def _compute_total(self):
        for r in self:
            r.total_cost = r.quantity * r.unit_price

    @api.depends('name', 'type', 'workload_percent', 'quantity')
    def _compute_capacity_html(self):
        for r in self:
            load = r.workload_percent or 0
            
            if load <= 70:
                batt_color = "#facc15" 
                text_col = "#a16207"
            elif load <= 90:
                batt_color = "#eab308"
                text_col = "#854d0e"
            else:
                batt_color = "#ca8a04"
                text_col = "#713f12"
                
            bars = ""
            for i in range(10):
                bg = batt_color if i < (load / 10) else "#fef9c3"
                bars += f'<div style="flex: 1; height: 100%; background: {bg}; margin-right: 2px; border-radius: 2px;"></div>'

            html = f"""
            <div style="font-family: 'Outfit', sans-serif; background: #fffdf5; padding: 20px; border-radius: 12px; border: 1px solid #fde047; color: #422006; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 4px 10px rgba(202, 138, 4, 0.05);">
                <div>
                    <div style="font-size: 11px; font-weight: 700; color: #a16207; text-transform: uppercase;">{dict(self._fields['type'].selection).get(r.type, 'Khác')} | Số lượng: {r.quantity}</div>
                    <h3 style="margin: 5px 0 0 0; font-size: 20px; font-weight: 800; color: #713f12;">{r.name or 'Resource'}</h3>
                </div>
                
                <div style="display: flex; flex-direction: column; align-items: flex-end;">
                    <div style="font-size: 11px; font-weight: 800; color: {text_col}; margin-bottom: 5px;">CÔNG SUẤT: {load}%</div>
                    <div style="display: flex; align-items: center;">
                        <div style="width: 120px; height: 24px; border: 2px solid #fde047; padding: 2px; border-radius: 4px; display: flex;">
                            {bars}
                        </div>
                        <div style="width: 4px; height: 12px; background: #fde047; border-radius: 0 2px 2px 0;"></div>
                    </div>
                </div>
            </div>
            """
            r.resource_capacity_html = html
