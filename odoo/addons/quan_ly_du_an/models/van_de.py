# -*- coding: utf-8 -*-
from odoo import models, fields, api

class DuAnVanDe(models.Model):
    _name = 'quan_ly.du_an.issue'
    _description = 'Vấn đề / Lỗi dự án'

    du_an_id = fields.Many2one('quan_ly.du_an', string='Dự án', ondelete='cascade')
    name = fields.Char(string='Tiêu đề vấn đề', required=True)
    priority = fields.Selection([('0', 'Thấp'), ('1', 'Trung bình'), ('2', 'Cao')], string='Ưu tiên', default='1')
    severity = fields.Selection([('low', 'Nhẹ'), ('medium', 'Vừa'), ('high', 'Nghiêm trọng')], string='Mức độ', default='medium')
    assignee_id = fields.Many2one('quan_ly.nhan_vien', string='Người xử lý')
    status = fields.Selection([
        ('new', 'Mới'),
        ('in_progress', 'Đang xử lý'),
        ('resolved', 'Đã xong'),
        ('closed', 'Đã đóng')
    ], string='Trạng thái', default='new')
    description = fields.Text(string='Mô tả chi tiết')
    
    blocker_score = fields.Integer(string='Điểm Block (0-100)', default=10)
    is_blocker = fields.Boolean(string='Là Blocker?', compute='_compute_is_blocker', store=True)
    issue_ticket_html = fields.Html(compute='_compute_issue_ticket')

    @api.depends('blocker_score', 'severity')
    def _compute_is_blocker(self):
        for r in self:
            r.is_blocker = bool(r.blocker_score >= 80 or r.severity == 'high')

    @api.depends('name', 'status', 'priority', 'blocker_score', 'severity')
    def _compute_issue_ticket(self):
        for r in self:
            score = r.blocker_score or 0
            
            # Status colors in yellow theme
            if r.status == 'new': badge_bg, badge_col = '#fef08a', '#854d0e'
            elif r.status == 'in_progress': badge_bg, badge_col = '#fde047', '#a16207'
            elif r.status == 'resolved': badge_bg, badge_col = '#facc15', '#422006'
            else: badge_bg, badge_col = '#fef9c3', '#ca8a04'

            p_labels = {'0':'Thấp', '1':'Bình thường', '2':'Cao'}
            s_labels = {'low':'Nhẹ', 'medium':'Vừa', 'high':'Nghiêm trọng'}
            
            html = f"""
            <div style="font-family: 'Outfit', sans-serif; background: #fffdf5; border-radius: 12px; border: 1px solid #fde047; box-shadow: 0 4px 10px rgba(202, 138, 4, 0.05); position: relative; overflow: hidden; display: flex;">
                <!-- Left Color Bar (Yellows) -->
                <div style="width: 8px; background: {'#854d0e' if r.is_blocker else '#facc15'};"></div>
                
                <div style="padding: 20px; flex-grow: 1;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                        <div style="font-size: 11px; font-weight: 800; color: #a16207; text-transform: uppercase;">
                            <i class="fa fa-ticket"></i> ISSUE TICKET
                        </div>
                        <div style="background: {badge_bg}; color: {badge_col}; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;">
                            {dict(self._fields['status'].selection).get(r.status, 'Mới')}
                        </div>
                    </div>
                    
                    <h3 style="margin: 0 0 15px 0; font-size: 20px; font-weight: 800; color: #713f12;">{r.name or 'Vấn đề mới'}</h3>
                    
                    <div style="display: flex; gap: 15px; margin-bottom: 15px;">
                        <span style="font-size: 12px; color: #854d0e; font-weight: 600;"><i class="fa fa-arrow-up"></i> Ưu tiên: {p_labels.get(r.priority, 'N/A')}</span>
                        <span style="font-size: 12px; color: #854d0e; font-weight: 600;"><i class="fa fa-warning"></i> Mức độ: {s_labels.get(r.severity, 'N/A')}</span>
                    </div>

                    <div style="background: #fef9c3; padding: 12px; border-radius: 8px; border: 1px solid #fef08a;">
                        <div style="display: flex; justify-content: space-between; font-size: 11px; font-weight: 700; color: #a16207; margin-bottom: 6px;">
                            <span>ĐIỂM TẮC NGHẼN (BLOCKER SCORE)</span>
                            <span>{score}/100</span>
                        </div>
                        <div style="height: 6px; background: #fffdf5; border-radius: 3px; overflow: hidden;">
                            <div style="height: 100%; width: {score}%; background: {'#854d0e' if score > 70 else '#facc15'};"></div>
                        </div>
                    </div>
                </div>
            </div>
            """
            r.issue_ticket_html = html
