# -*- coding: utf-8 -*-
from odoo import models, fields, api

class DuAnBenLienQuan(models.Model):
    _name = 'quan_ly.du_an.stakeholder'
    _description = 'Bên liên quan dự án'

    du_an_id = fields.Many2one('quan_ly.du_an', string='Dự án', ondelete='cascade')
    name = fields.Char(string='Tên đối tác', required=True)
    role = fields.Char(string='Vai trò')
    organization = fields.Char(string='Tổ chức / Công ty')
    email = fields.Char(string='Email')
    phone = fields.Char(string='Số điện thoại')
    note = fields.Text(string='Ghi chú')
    influence_score = fields.Integer(string='Mức độ ảnh hưởng (0-100)', default=50)
    stakeholder_card_html = fields.Html(compute="_compute_card_html")

    @api.depends('name', 'role', 'organization', 'influence_score')
    def _compute_card_html(self):
        for r in self:
            score = r.influence_score or 0
            
            html = f"""
            <div style="font-family: 'Outfit', sans-serif; background: #fffdf5; padding: 25px; border-radius: 16px; border: 1px solid #fde047; color: #422006; display: flex; align-items: center; gap: 20px; box-shadow: 0 4px 15px rgba(202, 138, 4, 0.05);">
                <div style="width: 80px; height: 80px; border-radius: 50%; background: #fef08a; border: 3px solid #facc15; display: flex; align-items: center; justify-content: center; font-size: 32px; color: #ca8a04; box-shadow: 0 4px 10px rgba(250, 204, 21, 0.2);">
                    <i class="fa fa-user-circle"></i>
                </div>
                <div style="flex-grow: 1;">
                    <div style="font-size: 12px; font-weight: 700; color: #a16207; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px;">{r.role or 'Chức danh'} | {r.organization or 'Tổ chức'}</div>
                    <h2 style="margin: 0 0 10px 0; font-size: 24px; font-weight: 800; color: #713f12;">{r.name or 'Chưa rõ tên'}</h2>
                    
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <span style="font-size: 13px; font-weight: 600; color: #854d0e;">TÍN NHIỆM / ẢNH HƯỞNG:</span>
                        <div style="flex-grow: 1; height: 8px; background: #fef9c3; border-radius: 4px; border: 1px solid #fde047; position: relative; overflow: hidden;">
                            <div style="width: {score}%; height: 100%; background: #eab308; box-shadow: 0 0 10px #facc15;"></div>
                        </div>
                        <span style="font-size: 16px; font-weight: 800; color: #ca8a04;">{score}%</span>
                    </div>
                </div>
            </div>
            """
            r.stakeholder_card_html = html
