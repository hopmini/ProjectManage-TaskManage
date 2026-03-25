# -*- coding: utf-8 -*-
from odoo import models, fields, api
try:
    from markupsafe import Markup
except ImportError:
    from odoo.tools import Markup # fallback for newer Odoo versions
import requests
import json

class QuanLyAIChat(models.Model):
    _name = 'quan_ly.ai_chat'
    _description = 'AI Chat Live'
    _order = 'write_date desc'

    name = fields.Char(string='Phiên thảo luận', default='Thảo luận tổng hợp')
    history_html = fields.Html(string='Lịch sử Chat', default="<div class='chat-container'></div>", sanitize=False)
    message_input = fields.Text(string='Tin nhắn')
    
    def action_send_message(self):
        self.ensure_one()
        if not self.message_input:
            return
            
        user_msg = self.message_input
        
        # Thêm User Bubble với CSS Class
        user_bubble = f'<div class="user-bubble"><div class="user-bubble-content">{user_msg}</div></div>'
        
        prompt = self._prepare_ai_prompt(user_msg)

        # Call AI
        api_key = self.env['ir.config_parameter'].sudo().get_param('quan_ly_du_an.groq_api_key', default="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")
        ai_content = "Không có phản hồi từ AI."
        try:
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                               headers={"Authorization": f"Bearer {api_key}"},
                               json={
                                   "model": "llama-3.3-70b-versatile",
                                   "messages": [{"role": "user", "content": prompt}],
                                   "temperature": 0.5
                               }, timeout=20)
            if res.status_code == 200:
                ai_content = res.json()['choices'][0]['message']['content'].replace('\n', '<br>')
            else:
                ai_content = f"Lỗi: {res.text}"
        except Exception as e:
            ai_content = f"Lỗi kết nối: {str(e)}"

        # Thêm AI Bubble với CSS Class
        ai_bubble = f'<div class="ai-bubble"><div class="ai-bubble-content">{ai_content}</div></div>'
        
        # Cập nhật dùng Markup để tránh escaping
        self.write({
            'history_html': Markup(self.history_html or "") + Markup(user_bubble) + Markup(ai_bubble),
            'message_input': False
        })
        
    def action_clear_history(self):
        if self:
            self.history_html = Markup("<div class='chat-container'></div>")
        else:
            # Trường hợp gọi từ Widget JS qua RPC (không có ID)
            session = self.env.ref('quan_ly_du_an.default_ai_chat_session', raise_if_not_found=False)
            if not session:
                session = self.env['quan_ly.ai_chat'].search([], limit=1)
            if session:
                session.history_html = Markup("<div class='chat-container'></div>")
        return True

    @api.model
    def action_send_message_from_widget(self, message):
        if not message:
            return {'response': "Vui lòng nhập tin nhắn."}

        # Tìm hoặc tạo session mặc định
        session = self.env.ref('quan_ly_du_an.default_ai_chat_session', raise_if_not_found=False)
        if not session:
            session = self.search([], limit=1)
        if not session:
            session = self.create({'name': 'AI Assistant Support'})

        # Build prompt & Call AI (Tìm kiếm dữ liệu trễ hạn để đưa vào ngữ cảnh)
        prompt = self._prepare_ai_prompt(message)

        api_key = self.env['ir.config_parameter'].sudo().get_param('quan_ly_du_an.groq_api_key', default="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")
        ai_response = "AI bận, thử lại sau."
        try:
            res = requests.post("https://api.groq.com/openai/v1/chat/completions", 
                               headers={"Authorization": f"Bearer {api_key}"},
                               json={
                                   "model": "llama-3.3-70b-versatile",
                                   "messages": [{"role": "user", "content": prompt}],
                                   "temperature": 0.5
                               }, timeout=15)
            if res.status_code == 200:
                ai_response = res.json()['choices'][0]['message']['content']
            else:
                ai_response = f"Lỗi AI: {res.status_code}"
        except Exception:
            ai_response = "Lỗi kết nối AI."

        # Lưu vào history để đồng bộ
        user_bubble = f'<div class="user-bubble"><div class="user-bubble-content">{message}</div></div>'
        ai_bubble = f'<div class="ai-bubble"><div class="ai-bubble-content">{ai_response.replace("\n", "<br>")}</div></div>'
        session.write({
            'history_html': Markup(session.history_html or "") + Markup(user_bubble) + Markup(ai_bubble)
        })

        return {'response': ai_response}

    def _prepare_ai_prompt(self, user_message):
        overdue_projects = self.env['quan_ly.du_an'].search([('trang_thai', '=', 'tre_han')])
        overdue_tasks = self.env['quan_ly.du_an.line'].search([('is_late', '=', True)])
        
        ctx_parts = ["Hệ thống Quản lý Dự án FaceWorks."]
        if overdue_projects:
            ctx_parts.append(f"Dự án TRỄ HẠN ({len(overdue_projects)}): " + ", ".join([p.ten_du_an for p in overdue_projects]))
        else:
            ctx_parts.append("Không có dự án nào trễ hạn.")
            
        if overdue_tasks:
            tasks_str = ", ".join([f"{t.cong_viec_id.ten_cong_viec} ({t.du_an_id.ten_du_an})" for t in overdue_tasks[:10]])
            ctx_parts.append(f"Công việc TRỄ HẠN ({len(overdue_tasks)}): " + tasks_str)
            
        total_projects = self.env['quan_ly.du_an'].search_count([])
        ctx_parts.append(f"Tổng dự án trong hệ thống: {total_projects}")

        return "Ngữ cảnh:\n" + "\n".join(ctx_parts) + f"\n\nNgười dùng: {user_message}\nTrả lời ngắn gọn, chuyên nghiệp."
