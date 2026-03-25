# -*- coding: utf-8 -*-
from odoo import models, fields, api

class DuAnKiemDinh(models.Model):
    _name = 'quan_ly.du_an.quality'
    _description = 'Kiểm định chất lượng dự án'

    du_an_id = fields.Many2one('quan_ly.du_an', string='Dự án', ondelete='cascade')
    name = fields.Char(string='Nội dung kiểm tra', required=True)
    is_passed = fields.Boolean(string='Đạt yêu cầu', default=False)
    inspector_id = fields.Many2one('quan_ly.nhan_vien', string='Người kiểm tra')
    check_date = fields.Date(string='Ngày kiểm tra', default=fields.Date.today)
    result_note = fields.Text(string='Ghi chú kết quả')
    
    quality_score = fields.Integer(string='Điểm chất lượng (0-100)', default=100)
    risk_factor = fields.Float(string='Hệ số rủi ro', compute='_compute_risk_factor', store=True)
    quality_gauge_html = fields.Html(compute='_compute_quality_gauge')

    @api.depends('quality_score', 'is_passed')
    def _compute_risk_factor(self):
        for r in self:
            if r.is_passed:
                r.risk_factor = max(0.0, 1.0 - (r.quality_score / 100.0))
            else:
                r.risk_factor = max(1.0, 2.0 - (r.quality_score / 100.0))

    @api.depends('quality_score', 'is_passed', 'name')
    def _compute_quality_gauge(self):
        for r in self:
            score = r.quality_score or 0
            
            # Yellow theme: bg yellow-50, yellow-100, accent yellow-600
            if score >= 80:
                color = "#ca8a04" # yellow-600
                bg = "#fef08a" # yellow-200
                status = "ĐẠT CHUẨN"
                icon = "fa-check-circle"
            elif score >= 50:
                color = "#b45309" # yellow-700
                bg = "#fde047" # yellow-300
                status = "BÁO ĐỘNG"
                icon = "fa-exclamation-triangle"
            else:
                color = "#9a3412" # orange-800
                bg = "#fcd34d" # yellow-400
                status = "NGHIÊM TRỌNG"
                icon = "fa-times-circle"
                
            rotation = (score / 100 * 180) - 90
            
            html = f"""
            <div style="font-family: 'Outfit', sans-serif; background: #fffdf5; padding: 25px; border-radius: 16px; border: 1px solid #fde047; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 4px 15px rgba(202, 138, 4, 0.05);">
                <div style="flex-grow: 1;">
                    <div style="font-size: 11px; font-weight: 700; color: #a16207; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">HỒ SƠ KIỂM ĐỊNH CHẤT LƯỢNG</div>
                    <h2 style="margin: 0 0 10px 0; font-size: 22px; font-weight: 800; color: #713f12;">{r.name or 'Chưa rõ'}</h2>
                    <div style="display: flex; gap: 10px;">
                        <span style="background: {bg}; color: {color}; padding: 4px 12px; border-radius: 6px; font-size: 12px; font-weight: 700;"><i class="fa {icon}"></i> {status}</span>
                        <span style="background: #fef9c3; color: #854d0e; padding: 4px 12px; border-radius: 6px; font-size: 12px; font-weight: 700;">HS RỦI RO: {r.risk_factor:.2f}</span>
                    </div>
                </div>
                
                <!-- Gauge Chart -->
                <div style="position: relative; width: 140px; height: 75px; overflow: hidden; text-align: center;">
                    <!-- Semicircle background -->
                    <div style="width: 140px; height: 140px; border-radius: 50%; border: 15px solid #fef9c3; position: absolute; bottom: -65px; box-sizing: border-box;"></div>
                    <!-- Semicircle value -->
                    <div style="width: 140px; height: 140px; border-radius: 50%; border: 15px solid {color}; border-bottom-color: transparent; border-right-color: transparent; position: absolute; bottom: -65px; left: 0; box-sizing: border-box; transform: rotate({rotation}deg); transition: transform 1s ease;"></div>
                    
                    <div style="position: absolute; bottom: 0; left: 0; right: 0; font-size: 24px; font-weight: 800; color: {color};">{score}</div>
                </div>
            </div>
            """
            r.quality_gauge_html = html
