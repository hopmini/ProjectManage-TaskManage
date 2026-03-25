# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date, datetime
import requests
import json
import logging
import base64
import io

_logger = logging.getLogger(__name__)

class QuanLyDuAn(models.Model):
    _name = 'quan_ly.du_an'
    _description = 'Quản lý Dự án'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ten_du_an'
    _order = 'do_uu_tien desc, ngay_bat_dau desc'

    # --- Thông tin dự án ---
    ten_du_an = fields.Char(string='Tên dự án', default='Dự án mới', tracking=True)
    ma_du_an = fields.Char(string='Mã dự án', required=True, copy=False, readonly=True, default=lambda self: _('NEW'))
    loai_du_an = fields.Selection([
        ('noi_bo', 'Nội bộ'),
        ('khach_hang', 'Khách hàng'),
        ('nghien_cuu', 'Nghiên cứu'),
        ('bao_tri', 'Bảo trì')
    ], string='Loại dự án', default='khach_hang', tracking=True)
    color = fields.Integer(string='Màu sắc', default=0)
    active = fields.Boolean(string='Kích hoạt', default=True)
    
    # --- Nhân sự ---
    truong_du_an_id = fields.Many2one('quan_ly.nhan_vien', string='Trưởng dự án', tracking=True)
    thanh_vien_ids = fields.Many2many('quan_ly.nhan_vien', 'du_an_nhan_vien_rel', 'du_an_id', 'nhan_vien_id', string='Thành viên')
    so_luong_thanh_vien = fields.Integer(string='Số lượng nhân sự', compute='_compute_member_count', store=True)

    # --- Kế hoạch ---
    ngay_bat_dau = fields.Date(string='Ngày bắt đầu', default=fields.Date.today, tracking=True)
    ngay_ket_thuc = fields.Date(string='Ngày kết thúc', tracking=True)
    ngay_nghiem_thu = fields.Date(string='Ngày nghiệm thu', readonly=True)
    ngay_cap_nhat_cuoi = fields.Datetime(string='Cập nhật cuối', compute='_compute_last_update', store=True)
    
    trang_thai = fields.Selection([
        ('nhap', 'Mới'),
        ('trien_khai', 'Đang thực hiện'),
        ('tam_dung', 'Tạm dừng'),
        ('tre_han', 'Trễ hạn'),
        ('hoan_thanh', 'Hoàn thành'),
        ('huy', 'Đã hủy')
    ], string='Trạng thái', default='nhap', tracking=True)
    do_uu_tien = fields.Selection([('0', 'Thấp'), ('1', 'Trung bình'), ('2', 'Cao'), ('3', 'Nghiêm trọng')], string='Ưu tiên', default='1', index=True)
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', default=lambda self: self.env.company.currency_id)
    # --- Tài chính & Tiến độ ---
    ngan_sach_du_kien = fields.Float(string='Ngân sách', default=0.0)
    chi_phi_thuc_te = fields.Float(string='Chi phí thực tế', default=0.0)
    ty_suat_loi_nhuan = fields.Float(string='Biên lợi nhuận (%)', compute='_compute_financial_stats', store=True)
    ty_le_ngan_sach = fields.Float(string='Tỷ lệ chi tiêu (%)', compute='_compute_financial_stats', store=True)
    
    tien_do_tong_the = fields.Float(string='Tiến độ (%)', compute='_compute_progress_stats', store=True)
    tong_so_viec = fields.Integer(string='Tổng số việc', compute='_compute_progress_stats', store=True)
    so_viec_hoan_thanh = fields.Integer(string='Đã xong', compute='_compute_progress_stats', store=True)

    # --- Chỉ số EVM ---
    spi_index = fields.Float(string='Chỉ số SPI', compute='_compute_evm_stats', help="Chỉ số hiệu suất tiến độ")
    cpi_index = fields.Float(string='Chỉ số CPI', compute='_compute_evm_stats', help="Chỉ số hiệu suất chi phí")
    smart_process_flow_html = fields.Html(string="Quy trình Dự án", compute='_compute_smart_process_flow')

    # --- Telegram & Notifications ---
    telegram_chat_id = fields.Char(string="Telegram Chat ID", help="ID của Chat hoặc Group Telegram")
    telegram_bot_token = fields.Char(string="Telegram Bot Token", help="Token lấy từ @BotFather", default=lambda self: self.env['ir.config_parameter'].sudo().get_param('quan_ly_du_an.telegram_bot_token'))
    telegram_enabled = fields.Boolean(string="Bật Telegram", default=True)
    last_alert_date = fields.Datetime(string="Ngày cảnh báo cuối")

    # --- Liên kết ---
    dong_cong_viec_ids = fields.One2many('quan_ly.du_an.line', 'du_an_id', string='Chi tiết hạng mục')
    milestone_ids = fields.One2many('quan_ly.du_an.milestone', 'du_an_id', string='Cột mốc')
    risk_ids = fields.One2many('quan_ly.du_an.risk', 'du_an_id', string='Rủi ro')
    mo_ta_du_an = fields.Html(string='Mô tả dự án')
    ghi_chu_quan_tri = fields.Text(string='Ghi chú')

    # --- AI & Automation ---
    ai_analysis_result = fields.Text(string="Phân tích AI", compute="_compute_ai_analysis", store=True)
    ai_report_card_html = fields.Html(string="Thẻ báo cáo chiến lược", compute="_compute_ai_analysis", store=True)
    ai_analysis_kanban = fields.Char(string="AI Phân tích nhanh", compute="_compute_ai_analysis_kanban")

    @api.depends('tien_do_tong_the', 'trang_thai')
    def _compute_ai_analysis_kanban(self):
        for r in self:
            if r.trang_thai == 'hoan_thanh':
                r.ai_analysis_kanban = "Dự án đã hoàn tất xuất sắc."
            elif r.tien_do_tong_the >= 80:
                r.ai_analysis_kanban = "Tiến độ rất tốt, sắp về đích."
            elif r.tien_do_tong_the >= 50:
                r.ai_analysis_kanban = "Dự án đang đi đúng hướng."
            elif r.trang_thai == 'tre_han':
                r.ai_analysis_kanban = "Cảnh báo: Cần đẩy nhanh tiến độ ngay."
            else:
                r.ai_analysis_kanban = "Dự án đang trong giai đoạn đầu."

    tai_lieu_mau = fields.Binary(string='Hồ sơ PDF')
    ten_file_mau = fields.Char(string='Tên file')
    email_lien_he = fields.Char(string='Email liên hệ', tracking=True, default='hop13101999@gmail.com')
    
    # --- Advanced AI & Risk (Required by Dashboard) ---
    risk_score = fields.Integer(string="Điểm rủi ro (0-100)", default=0)
    risk_heatmap_html = fields.Html(string="Ma trận Rủi ro AI", compute='_compute_risk_heatmap')
    tong_gio_thuc_te = fields.Float(string="Tổng giờ thực tế", compute="_compute_total_hours", store=True)
    cau_hoi_ai = fields.Char(string='Câu hỏi AI')
    cau_tra_loi_ai = fields.Text(string='Câu trả lời AI', readonly=True)

    @api.depends('dong_cong_viec_ids.so_gio_thuc_te')
    def _compute_total_hours(self):
        for r in self:
            r.tong_gio_thuc_te = sum(r.dong_cong_viec_ids.mapped('so_gio_thuc_te')) 

    @api.depends('message_ids')
    def _compute_last_update(self):
        for r in self:
            r.ngay_cap_nhat_cuoi = fields.Datetime.now()

    @api.constrains('ngay_bat_dau', 'ngay_ket_thuc')
    def _check_dates(self):
        for r in self:
            if r.ngay_bat_dau and r.ngay_ket_thuc and r.ngay_bat_dau > r.ngay_ket_thuc:
                raise ValidationError("Ngày kết thúc không được nhỏ hơn ngày bắt đầu.")

    @api.depends('thanh_vien_ids')
    def _compute_member_count(self):
        for r in self: r.so_luong_thanh_vien = len(r.thanh_vien_ids)

    @api.depends('ngan_sach_du_kien', 'chi_phi_thuc_te')
    def _compute_financial_stats(self):
        for r in self:
            if r.ngan_sach_du_kien > 0:
                r.ty_le_ngan_sach = (r.chi_phi_thuc_te / r.ngan_sach_du_kien) * 100
                r.ty_suat_loi_nhuan = ((r.ngan_sach_du_kien - r.chi_phi_thuc_te) / r.ngan_sach_du_kien) * 100
            else:
                r.ty_le_ngan_sach = 0.0
                r.ty_suat_loi_nhuan = 0.0

    @api.depends('dong_cong_viec_ids.tien_do_cong_viec', 'dong_cong_viec_ids.trang_thai_viec')
    def _compute_progress_stats(self):
        for r in self:
            lines = r.dong_cong_viec_ids
            r.tong_so_viec = len(lines)
            r.so_viec_hoan_thanh = len(lines.filtered(lambda x: x.trang_thai_viec == 'done'))
            if r.tong_so_viec > 0:
                total_prog = sum(lines.mapped('tien_do_cong_viec'))
                r.tien_do_tong_the = total_prog / r.tong_so_viec
            else:
                r.tien_do_tong_the = 0.0

    @api.depends('tien_do_tong_the', 'ty_le_ngan_sach', 'ngay_bat_dau', 'ngay_ket_thuc')
    def _compute_evm_stats(self):
        today = fields.Date.today()
        for r in self:
            if r.ngay_bat_dau and r.ngay_ket_thuc and r.ngay_ket_thuc > r.ngay_bat_dau:
                total_days = (r.ngay_ket_thuc - r.ngay_bat_dau).days
                passed_days = (today - r.ngay_bat_dau).days
                plan_progress = (passed_days / total_days * 100) if passed_days > 0 else 0.0
                plan_progress = min(100, max(0, plan_progress))
            else:
                plan_progress = 0.0
            
            r.spi_index = (r.tien_do_tong_the / plan_progress) if plan_progress > 0 else 1.0
            r.cpi_index = (r.tien_do_tong_the / r.ty_le_ngan_sach) if r.ty_le_ngan_sach > 0 else 1.0

    @api.onchange('dong_cong_viec_ids')
    def _onchange_dong_cong_viec_ids(self):
        self._compute_progress_stats()

    @api.depends('trang_thai')
    def _compute_smart_process_flow(self):
        for r in self:
            stages = [
                ('nhap', 'Khởi tạo'),
                ('tiep_nhan', 'Phân tích'),
                ('trien_khai', 'Thực thi'),
                ('hoan_thanh', 'Nghiệm thu')
            ]
            
            html = """<div style="display: flex; align-items: center; justify-content: space-between; font-family: sans-serif; font-size: 11px; padding: 5px 0;">"""
            
            current_found = False
            for idx, (code, name) in enumerate(stages):
                is_current = (r.trang_thai == code)
                is_past = not is_current and not current_found and r.trang_thai not in ['nhap', 'huy']
                if is_current: current_found = True
                
                if is_past or (is_current and code == 'hoan_thanh'):
                    bg_color = "#00a65a"; text_color = "#00a65a"; line_color = "#00a65a"; font_weight = "bold"
                elif is_current:
                    bg_color = "#dd4b39"; text_color = "#dd4b39"; line_color = "#e2e8f0"; font_weight = "bold"
                else:
                    bg_color = "#e2e8f0"; text_color = "#64748b"; line_color = "#e2e8f0"; font_weight = "normal"
                
                html += f"""
                <div style="display: flex; align-items: center;">
                    <div style="width: 10px; height: 10px; border-radius: 50%; background: {bg_color}; margin-right: 6px;"></div>
                    <span style="color: {text_color}; font-weight: {font_weight};">{name}</span>
                </div>
                """
                if idx < len(stages) - 1:
                    html += f'<div style="flex: 1; height: 1px; background: {line_color}; margin: 0 10px;"></div>'

            html += "</div>"
            r.smart_process_flow_html = html
    
    def _call_groq_api(self, prompt, require_json=False):
        api_key = self.env['ir.config_parameter'].sudo().get_param('quan_ly_du_an.groq_api_key', default="GROQ_API_KEY")
        api_url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        system_content = "Bạn là hệ thống AI phân tích dữ liệu dự án chuyên nghiệp."
        if require_json: system_content += " CHỈ TRẢ VỀ DUY NHẤT JSON HỢP LỆ."
        data = {
            "model": "llama-3.3-70b-versatile", 
            "messages": [{"role": "system", "content": system_content}, {"role": "user", "content": prompt}],
            "temperature": 0.2 if require_json else 0.5
        }
        try:
            res = requests.post(api_url, headers=headers, json=data, timeout=30)
            if res.status_code == 200: return res.json()['choices'][0]['message']['content']
            if res.status_code == 401: return "<b>Lỗi kết nối AI (401):</b> API Key không hợp lệ. Vui lòng cấu hình key mới tại <i>Settings > Technical > System Parameters</i> (Key: <code>quan_ly_du_an.groq_api_key</code>)."
            return f"Lỗi hệ thống AI: {res.text}"
        except Exception as e: return f"Lỗi kết nối mạng: {str(e)}"

    @api.model
    def process_voice_command(self, project_id, text):
        try:
            r = self.browse(project_id)
            if not r.exists(): return {'success': False, 'error': 'Dự án không tồn tại.'}
            prompt = f"AI phân tích lệnh giọng nói: \"{text}\"... Trích xuất JSON ý định."
            response = self._call_groq_api(prompt, require_json=True)
            res_clean = response.strip().replace("```json", "").replace("```", "")
            json_data = json.loads(res_clean)
            action = json_data.get('action'); val = json_data.get('value')
            if action in ['tien_do_tong_the', 'ngan_sach_du_kien', 'trang_thai', 'do_uu_tien'] and val is not None:
                r.write({action: val})
                return {'success': True}
            return {'success': False, 'error': 'Không hiểu lệnh.'}
        except Exception as e: return {'success': False, 'error': str(e)}

    def action_open_pitch_deck(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_url', 'url': f'/quan_ly_du_an/pitch_deck/{self.id}', 'target': 'new'}

    def action_extract_pdf(self):
        for r in self:
            if not r.tai_lieu_mau: raise ValidationError("Vui lòng đính kèm tài liệu.")
            file_content = base64.b64decode(r.tai_lieu_mau)
            text_content = ""
            
            # 1. Thử đọc PDF nếu là file type pdf
            is_pdf = (r.ten_file_mau and r.ten_file_mau.lower().endswith('.pdf'))
            if is_pdf:
                try:
                    import PyPDF2
                    import io
                    pdf = PyPDF2.PdfReader(io.BytesIO(file_content)) if hasattr(PyPDF2, 'PdfReader') else PyPDF2.PdfFileReader(io.BytesIO(file_content))
                    pages = pdf.pages if hasattr(pdf, 'pages') else range(pdf.getNumPages())
                    for page in list(pages)[:5]: # Đọc 5 trang đầu
                        text_content += page.extract_text() + "\n" if hasattr(page, 'extract_text') else page.extractText() + "\n"
                except Exception as e:
                    text_content = file_content.decode('utf-8', errors='ignore')
            else:
                text_content = file_content.decode('utf-8', errors='ignore')
                
            prompt = f"""Trích xuất thông tin dự án từ văn bản sau và trả về DUY NHẤT định dạng JSON với các key: 
- 'ten_du_an' (chuỗi)
- 'ma_du_an' (chuỗi)
- 'ngan_sach_du_kien' (số nguyên)
- 'tasks' (danh sách object): Các hạng mục công việc. Mỗi object có 'ten_cong_viec' (chuỗi), 'so_gio_du_kien' (số nguyên).
- 'risks' (danh sách object): Các rủi ro tiềm ẩn. Mỗi object có 'ten_rui_ro' (chuỗi), 'muc_do' (chuỗi: '1', '2' hoặc '3'), 'phuong_an_xu_ly' (chuỗi).
Nội dung:\n{text_content[:4000]}"""
            
            # AI extraction logic
            response = self._call_groq_api(prompt, require_json=True)
            try:
                import re
                res_clean = response.strip()
                json_match = re.search(r'\{.*\}', res_clean, re.DOTALL)
                if json_match:
                    try:
                        json_data = json.loads(json_match.group(0))
                    except:
                        json_data = json.loads(res_clean.replace("```json", "").replace("```", ""))
                else:
                    json_data = json.loads(res_clean.replace("```json", "").replace("```", ""))
                
                vals = {}
                if 'ten_du_an' in json_data and json_data['ten_du_an']: vals['ten_du_an'] = json_data['ten_du_an']
                if 'ma_du_an' in json_data and json_data['ma_du_an']: vals['ma_du_an'] = json_data['ma_du_an']
                if 'ngan_sach_du_kien' in json_data:
                    try:
                        import re
                        num_str = re.sub(r'[^\d]', '', str(json_data['ngan_sach_du_kien']))
                        if num_str: vals['ngan_sach_du_kien'] = float(num_str)
                    except: pass
                
                # Trích xuất tasks
                if 'tasks' in json_data and isinstance(json_data['tasks'], list):
                    task_cmds = []
                    for t in json_data['tasks']:
                        name = t.get('ten_cong_viec')
                        if not name: continue
                        task_rec = self.env['quan_ly.cong_viec'].sudo().search([('ten_cong_viec', '=', name)], limit=1)
                        if not task_rec: task_rec = self.env['quan_ly.cong_viec'].sudo().create({'ten_cong_viec': name})
                        task_cmds.append((0, 0, {
                            'cong_viec_id': task_rec.id, 
                            'ngay_deadline': fields.Date.today(), 
                            'so_gio_du_kien': t.get('so_gio_du_kien', 10)
                        }))
                    if task_cmds:
                        # Clear old ones if needed or just append
                        vals['dong_cong_viec_ids'] = [(5, 0, 0)] + task_cmds
                        
                # Trích xuất risks
                if 'risks' in json_data and isinstance(json_data['risks'], list):
                    risk_cmds = []
                    for rk in json_data['risks']:
                        name = rk.get('ten_rui_ro')
                        if not name: continue
                        muc_do = str(rk.get('muc_do', '1'))
                        if muc_do not in ['1', '2', '3']: muc_do = '1'
                        risk_cmds.append((0, 0, {
                            'ten_rui_ro': name,
                            'muc_do': muc_do,
                            'phuong_an_xu_ly': rk.get('phuong_an_xu_ly', '')
                        }))
                    if risk_cmds:
                        vals['risk_ids'] = [(5, 0, 0)] + risk_cmds
                        
                if vals:
                    r.write(vals)
            except Exception as e:
                # Nếu lỗi JSON, có thể ghi log hoặc bỏ qua, vẫn chạy logic phân tích
                pass
                
            r.action_ai_analyze()

    def action_ask_chatbot(self):
        for r in self:
            if not r.cau_hoi_ai: raise ValidationError("Vui lòng nhập câu hỏi.")
            prompt = f"Dự án {r.ten_du_an}. Hỏi: {r.cau_hoi_ai}"
            r.cau_tra_loi_ai = self._call_groq_api(prompt)

    def action_ai_auto_planner(self):
        for r in self:
            if not r.ten_du_an: raise ValidationError("Nhập tên dự án.")
            prompt = f"Lập kế hoạch cho: {r.ten_du_an}. JSON milestones, tasks."
            response = self._call_groq_api(prompt, require_json=True)

    @api.depends('tien_do_tong_the', 'trang_thai', 'risk_ids.muc_do', 'spi_index', 'cpi_index')
    def _compute_ai_analysis(self):
        for r in self:
            analysis = [f"BÁO CÁO DỰ ÁN - {datetime.now().strftime('%d/%m/%Y')}"]
            score = 100
            if r.spi_index < 0.9: score -= 20
            if r.cpi_index < 0.9: score -= 20
            if r.trang_thai == 'tre_han': score -= 10
            
            # Risk impact
            risks_high = len(r.risk_ids.filtered(lambda rk: rk.muc_do == '3'))
            if risks_high > 0: score -= min(30, risks_high * 10)
            
            score = max(0, min(100, score))
            r.risk_score = 100 - score
            
            if score >= 90:
                analysis.append("Đánh giá chung: Dự án vận hành ổn định.")
            elif score >= 70:
                analysis.append("Đánh giá chung: Dự án duy trì tiến độ tốt.")
            else:
                analysis.append("Đánh giá chung: Cần điều chỉnh quản trị.")
                
            if risks_high > 0:
                analysis.append(f"Cảnh báo: Có {risks_high} rủi ro cao.")
                
            analysis.append(f"Chỉ số tin cậy: {score}%")
            r.ai_analysis_result = "\n".join(analysis)
            
            # (Thẻ báo cáo HTML logic) - Giữ nguyên và cập nhật theme theo score
            theme = {"bg": "#ffffff", "border": "#0d9488", "text": "#0f766e", "status": "AN TOÀN MỨC 1"}
            if score < 80: theme = {"bg": "#ffffff", "border": "#f59e0b", "text": "#b45309", "status": "CẢNH BÁO MỨC 2"}
            if score < 50: theme = {"bg": "#ffffff", "border": "#ef4444", "text": "#b91c1c", "status": "KHẨN CẤP MỨC 3"}
            
            r.ai_report_card_html = f"""
            <div style="font-family: sans-serif; padding: 15px; background: #fff; border-radius: 4px; border: 1px solid #e2e8f0;">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; margin-bottom: 10px;">
                    <h2 style="margin: 0; color: #1e293b; font-size: 14px; font-weight: 700;">BÁO CÁO: {r.ma_du_an}</h2>
                    <div style="padding: 2px 6px; background: {theme['border']}; color: #fff; font-size: 10px; font-weight: bold; border-radius: 2px;">{theme['status']}</div>
                </div>
                <div style="display: flex; gap: 15px; align-items: center;">
                    <div style="flex: 1; padding: 10px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px; text-align: center;">
                        <div style="font-size: 10px; color: #64748b; margin-bottom: 2px;">TIN CẬY</div>
                        <div style="font-size: 24px; font-weight: 700; color: {theme['text']};">{score}/100</div>
                    </div>
                    <div style="flex: 1;">
                        <div style="font-size: 12px; color: #334155;">Giai đoạn: {dict(r._fields['trang_thai'].selection).get(r.trang_thai)}</div>
                        <div style="font-size: 11px; color: #64748b; margin-top: 2px;">{len(r.risk_ids)} rủi ro, {len(r.milestone_ids)} cột mốc.</div>
                    </div>
                </div>
            </div>
            """

    def action_ai_analyze(self):
        # Fallback if someone still calls the action button
        self._compute_ai_analysis()

    @api.depends('risk_ids.muc_do', 'risk_ids.trang_thai')
    def _compute_risk_heatmap(self):
        for r in self:
            matrix = {
                'da_xay_ra': {'3': [], '2': [], '1': []}, 
                'dang_theo_doi': {'3': [], '2': [], '1': []}, 
                'da_xu_ly': {'3': [], '2': [], '1': []}
            }
            for risk in r.risk_ids:
                if risk.trang_thai in matrix and str(risk.muc_do) in matrix[risk.trang_thai]:
                    matrix[risk.trang_thai][str(risk.muc_do)].append(risk)
            
            colors = {
                'da_xay_ra': {'3': '#dc2626', '2': '#ef4444', '1': '#f87171'}, 
                'dang_theo_doi': {'3': '#ea580c', '2': '#f97316', '1': '#fb923c'}, 
                'da_xu_ly': {'3': '#0f766e', '2': '#14b8a6', '1': '#5eead4'}
            }
            
            html = """<div style="background: #ffffff; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0;">
                <h3 style="margin: 0 0 15px 0; font-size: 14px; font-weight: 800; color: #1e293b;">Ma trận Rủi ro Chiến lược</h3>
                <div style="display: grid; grid-template-columns: 100px 1fr 1fr 1fr; gap: 8px;">
                    <div style="font-size: 11px; font-weight: bold; color: #64748b;">Trạng thái / Mức</div>
                    <div style="text-align: center; font-size: 11px; font-weight: bold; color: #ef4444;">CAO (3)</div>
                    <div style="text-align: center; font-size: 11px; font-weight: bold; color: #f59e0b;">TRUNG BÌNH (2)</div>
                    <div style="text-align: center; font-size: 11px; font-weight: bold; color: #10b981;">THẤP (1)</div>
            """
            
            rows = [
                ('da_xay_ra', 'ĐÃ XẢY RA'),
                ('dang_theo_doi', 'THEO DÕI'),
                ('da_xu_ly', 'ĐÃ XỬ LÝ')
            ]
            
            for row_key, row_label in rows:
                html += f'<div style="font-size: 11px; font-weight: 700; color: #475569; display: flex; align-items: center;">{row_label}</div>'
                for level in ['3', '2', '1']:
                    risks = matrix[row_key][level]
                    color = colors[row_key][level]
                    count = len(risks)
                    opacity = "1" if count > 0 else "0.2"
                    html += f"""
                        <div style="background: {color}; color: #fff; padding: 10px; border-radius: 4px; text-align: center; opacity: {opacity}; transition: all 0.3s; position: relative;">
                            <div style="font-size: 18px; font-weight: 900;">{count}</div>
                            <div style="font-size: 9px; font-weight: bold; opacity: 0.8;">RỦI RO</div>
                        </div>
                    """
            
            html += "</div>"
            if not r.risk_ids:
                html += '<div style="margin-top: 15px; font-size: 12px; color: #94a3b8; text-align: center; border: 1px dashed #cbd5e1; padding: 10px; border-radius: 4px;">Chưa có rủi ro nào được ghi nhận.</div>'
            html += "</div>"
            r.risk_heatmap_html = html

    def action_view_workload(self):
        self.ensure_one()
        return {'name': 'Phân tích Nguồn lực', 'type': 'ir.actions.act_window', 'res_model': 'quan_ly.du_an.line', 'view_mode': 'graph,pivot', 'domain': [('du_an_id', '=', self.id)]}

    def _send_telegram_msg(self, message):
        import logging
        _logger = logging.getLogger(__name__)

        default_token = self.env['ir.config_parameter'].sudo().get_param('quan_ly_du_an.telegram_bot_token')
        default_chat_id = self.env['ir.config_parameter'].sudo().get_param('quan_ly_du_an.telegram_chat_id')
        
        if not default_chat_id:
            last_chat = self.env['quan_ly.du_an'].sudo().search([
                ('telegram_chat_id', '!=', False), 
                ('telegram_chat_id', '!=', '')
            ], limit=1, order='id desc')
            if last_chat: default_chat_id = last_chat.telegram_chat_id
            
        if not default_token:
            last_token = self.env['quan_ly.du_an'].sudo().search([
                ('telegram_bot_token', '!=', False), 
                ('telegram_bot_token', '!=', '')
            ], limit=1, order='id desc')
            if last_token: default_token = last_token.telegram_bot_token

        for r in self:
            tk = r.telegram_bot_token or default_token
            cid = r.telegram_chat_id or default_chat_id
            if not r.telegram_enabled:
                _logger.warning("Telegram skipped: telegram_enabled is False")
                continue
            if not tk or not cid:
                _logger.warning(f"Telegram skipped: missing token or chat id. tk={bool(tk)}, cid={bool(cid)}")
                continue
            try:
                import requests
                url = f"https://api.telegram.org/bot{tk}/sendMessage"
                payload = {'chat_id': cid, 'text': message, 'parse_mode': 'HTML'}
                res = requests.post(url, json=payload, timeout=5)
                _logger.info(f"Telegram API Response: {res.status_code} - {res.text}")
            except Exception as e:
                _logger.error(f"Telegram Request Error: {e}")

    def _build_detail_msg(self, r, title, icon):
        from datetime import datetime
        pm = r.truong_du_an_id.name if r.truong_du_an_id else 'Chưa gán'
        ns = r.ngan_sach_du_kien or 0.0
        
        # Calculate Progress Bar
        p_val = min(100, max(0, int(r.tien_do_tong_the)))
        blocks = int(p_val / 10)
        progress_bar = ("■" * blocks) + ("□" * (10 - blocks))
        
        trang_thai_dict = dict(self._fields['trang_thai'].selection)
        trang_thai_str = trang_thai_dict.get(r.trang_thai, 'N/A')
        
        now_str = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        start_date = r.ngay_bat_dau.strftime('%Y-%m-%d') if r.ngay_bat_dau else 'N/A'
        end_date = r.ngay_ket_thuc.strftime('%Y-%m-%d') if r.ngay_ket_thuc else 'N/A'
        
        msg = f"🌟 <b>BÁO CÁO CHIẾN LƯỢC DỰ ÁN</b> 🌟\n"
        msg += "━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"📂 <b>Dự án:</b> {r.ten_du_an.upper() if r.ten_du_an else 'N/A'}\n"
        msg += f"🆔 <b>Mã hồ sơ:</b> #{r.ma_du_an or 'N/A'}\n"
        msg += f"👤 <b>Project Manager:</b> {pm}\n"
        msg += f"🚦 <b>Trạng thái:</b> {trang_thai_str}\n"
        msg += "━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"📊 <b>TIẾN ĐỘ THỰC THI</b>\n"
        msg += f"{progress_bar} {p_val}% Hoàn tất\n\n"
        msg += f"💰 <b>CHỈ SỐ TÀI CHÍNH (VNĐ)</b>\n"
        msg += f"• 🧱 Ngân sách: {ns:,.0f}\n"
        msg += f"• 💸 Chi thực tế: 0\n"
        msg += f"• ⚖️ Khả dụng: {ns:,.0f}\n\n"
        msg += f"📅 <b>LỘ TRÌNH THỜI GIAN</b>\n"
        msg += f"• 🛫 Bắt đầu: {start_date}\n"
        msg += f"• 🏁 Kết thúc: {end_date}\n"
        msg += "━━━━━━━━━━━━━━━━━━━━\n"
        msg += "🔗 <i>Xem trực tuyến trên Odoo Cloud</i>\n"
        msg += f"📅 Ghi nhận: {now_str}"
        return msg

    def action_tiep_nhan_du_an(self):
        for r in self: 
            r.write({'trang_thai': 'trien_khai'})
            r._send_telegram_msg(self._build_detail_msg(r, "BẮT ĐẦU TRIỂN KHAI", "🚀"))

    def action_tam_dung(self):
        for r in self:
            r.write({'trang_thai': 'tam_dung'})
            r._send_telegram_msg(self._build_detail_msg(r, "DỰ ÁN TẠM DỪNG", "⏸️"))

    def action_finish_project(self):
        for r in self:
            r.write({'trang_thai': 'hoan_thanh', 'ngay_nghiem_thu': date.today()})
            r._send_telegram_msg(self._build_detail_msg(r, "NGHIỆM THU HOÀN THÀNH", "✅"))

    def action_reset_to_draft(self):
        for r in self:
            r.write({'trang_thai': 'nhap'})
            r._send_telegram_msg(self._build_detail_msg(r, "HỦY KHỞI ĐỘNG (VỀ NHÁP)", "🔄"))

    def action_cancel_project(self):
        for r in self:
            r.write({'trang_thai': 'huy'})
            r._send_telegram_msg(self._build_detail_msg(r, "ĐÃ HỦY DỰ ÁN", "❌"))

    def action_noop(self): return True

    def action_randomize_demo_data(self):
        import random
        from datetime import date
        for r in self:
            # 1. TASKS (15)
            r.dong_cong_viec_ids = [(5, 0, 0)]
            task_names = ["Kế hoạch tổng thể", "Phân tích yêu cầu", "Thiết kế UI/UX", "Phát triển Backend", "Giao diện Frontend", "Kiểm thử hệ thống", "Bảo mật & Network", "Tối ưu hóa DB", "Tài liệu kỹ thuật", "Đào tạo nhân sự", "Triển khai Staging", "Phản hồi khách hàng", "Sửa lỗi tồn đọng", "Kiểm toán bảo mật", "Bảo trì định kỳ"]
            for i in range(len(task_names)):
                task_rec = self.env['quan_ly.cong_viec'].sudo().search([('ten_cong_viec', '=', task_names[i])], limit=1)
                if not task_rec: task_rec = self.env['quan_ly.cong_viec'].sudo().create({'ten_cong_viec': task_names[i]})
                r.write({'dong_cong_viec_ids': [(0, 0, {
                    'cong_viec_id': task_rec.id,
                    'nhan_vien_id': r.truong_du_an_id.id if r.truong_du_an_id else False,
                    'ngay_deadline': date.today(),
                    'so_gio_du_kien': random.randint(20, 100),
                    'so_gio_thuc_te': random.randint(5, 50),
                    'tien_do_cong_viec': random.randint(20, 95),
                    'trang_thai_viec': random.choice(['todo', 'doing', 'done'])
                })]})

            # 2. MILESTONES (15)
            r.milestone_ids = [(5, 0, 0)]
            for i in range(15):
                r.write({'milestone_ids': [(0, 0, {
                    'ten_cot_moc': f'Cột mốc chiến lược {i+1}',
                    'ngay_du_kien': date.today(),
                    'tien_do': random.randint(10, 100),
                    'ngan_sach': random.randint(10, 500) * 1000000,
                    'da_dat_duoc': random.choice([True, False])
                })]})

            # 3. RISKS (15)
            r.risk_ids = [(5, 0, 0)]
            risk_templates = ["Biến động tỉ giá", "Thiếu hụt thiết bị", "Thay đổi chính sách", "Biến động nhân sự", "Lỗi hạ tầng Cloud", "Rủi ro kỹ thuật mới", "Áp lực tài chính", "Thay đổi Scope", "Trễ Deadline", "Bản quyền phần mềm", "Vấn đề pháp lý", "Hạ tầng yếu", "Bảo mật dữ liệu", "Cạnh tranh thị trường", "Yêu cầu khách hàng"]
            for i in range(len(risk_templates)):
                r.write({'risk_ids': [(0, 0, {
                    'ten_rui_ro': risk_templates[i],
                    'muc_do': random.choice(['1', '2', '3']),
                    'trang_thai': random.choice(['dang_theo_doi', 'da_xay_ra', 'da_xu_ly']),
                    'phuong_an_xu_ly': 'Đã có kế hoạch xử lý dự phòng.'
                })]})
            
            # 4. Trigger AI & Analysis
            r._compute_ai_analysis()
            r._compute_risk_heatmap()
            
        return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {
            'title': 'Dữ liệu Demo', 
            'message': 'Đã nạp 15 hồ sơ mẫu. AI đã hoàn tất phân tích!', 
            'type': 'success',
            'sticky': False
        }}

    def action_send_telegram_alert(self):
        for r in self:
            msg = f"<b>Thông báo Dự án: {r.ten_du_an}</b>\n"
            msg += f"Tiến độ: {round(r.tien_do_tong_the, 1)}%\n"
            msg += f"Ngân sách: {r.ngan_sach_du_kien:,.0f} VND"
            r._send_telegram_msg(msg)
    def action_send_email_report(self): pass
    def action_view_tasks(self): pass
    def action_view_milestones(self): pass
    def action_view_resources(self): pass
    def action_quick_audit(self): pass

class QuanLyDuAnLine(models.Model):
    _name = 'quan_ly.du_an.line'
    _description = 'Chi tiết hạng mục'
    du_an_id = fields.Many2one('quan_ly.du_an', ondelete='cascade', required=True)
    cong_viec_id = fields.Many2one('quan_ly.cong_viec', string='Hạng mục', required=True)
    nhan_vien_id = fields.Many2one('quan_ly.nhan_vien', string='Người phụ trách')
    ngay_deadline = fields.Date(string='Hạn hoàn thành', required=True)
    trang_thai_viec = fields.Selection([('todo', 'Chờ xử lý'), ('doing', 'Đang thực hiện'), ('done', 'Hoàn tất')], string='Trạng thái', default='todo')
    ghi_chu_rieng = fields.Char(string='Ghi chú')
    is_late = fields.Boolean(string='Trễ hạn', compute='_compute_is_late')
    muc_do_uu_tien = fields.Selection([('0', 'Thấp'), ('1', 'Trung bình'), ('2', 'Cao'), ('3', 'Rất gấp')], string='Cấp độ ưu tiên', default='1')
    so_gio_du_kien = fields.Float(string='Giờ dự kiến', default=1.0)
    so_gio_thuc_te = fields.Float(string='Giờ thực tế', default=0.0)
    tien_do_cong_viec = fields.Float(string='Tiến độ (%)', default=0.0)

    @api.onchange('so_gio_du_kien', 'so_gio_thuc_te')
    def _onchange_hours(self):
        if self.so_gio_du_kien > 0: self.tien_do_cong_viec = min(round((self.so_gio_thuc_te / self.so_gio_du_kien) * 100, 1), 100.0)

    def action_done(self): self.write({'trang_thai_viec': 'done', 'so_gio_thuc_te': self.so_gio_du_kien})

    @api.depends('ngay_deadline', 'trang_thai_viec')
    def _compute_is_late(self):
        today = date.today()
        for line in self: line.is_late = bool(line.ngay_deadline and line.ngay_deadline < today and line.trang_thai_viec != 'done')

class QuanLyDuAnMilestone(models.Model):
    _name = 'quan_ly.du_an.milestone'
    _description = 'Cột mốc dự án'
    du_an_id = fields.Many2one('quan_ly.du_an', ondelete='cascade')
    ten_cot_moc = fields.Char(string='Tên cột mốc', required=True)
    ngay_du_kien = fields.Date(string='Ngày dự kiến', required=True)
    da_dat_duoc = fields.Boolean(string='Đạt được', default=False)
    ghi_chu = fields.Text(string='Ghi chú')
    tien_do = fields.Float(string='Tiến độ (%)', default=0.0)
    ngan_sach = fields.Monetary(string='Ngân sách mục tiêu')
    currency_id = fields.Many2one('res.currency', related='du_an_id.currency_id')
    mau_sac = fields.Integer(string='Màu sắc thẻ', default=0)
    trang_thai = fields.Selection([('pending', 'Chưa đạt'), ('done', 'Đã đạt')], string='Trạng thái', compute='_compute_trang_thai', store=True)

    @api.depends('da_dat_duoc')
    def _compute_trang_thai(self):
        for r in self: r.trang_thai = 'done' if r.da_dat_duoc else 'pending'

class QuanLyDuAnRisk(models.Model):
    _name = 'quan_ly.du_an.risk'
    _description = 'Rủi ro dự án'
    du_an_id = fields.Many2one('quan_ly.du_an', ondelete='cascade')
    ten_rui_ro = fields.Char(string='Tên rủi ro', required=True)
    muc_do = fields.Selection([('1', 'Thấp'), ('2', 'Trung bình'), ('3', 'Nghiêm trọng')], string='Mức độ', default='1')
    phuong_an_xu_ly = fields.Text(string='Phương án xử lý')
    trang_thai = fields.Selection([('dang_theo_doi', 'Theo dõi'), ('da_xay_ra', 'Đã xảy ra'), ('da_xu_ly', 'Đã xử lý')], string='Trạng thái', default='dang_theo_doi')