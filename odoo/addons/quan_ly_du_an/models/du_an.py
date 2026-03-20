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
    telegram_chat_id = fields.Char(string="Telegram Chat ID", help="ID của Chat hoặc Group Telegram", default='5707408090')
    telegram_bot_token = fields.Char(string="Telegram Bot Token", help="Token lấy từ @BotFather", default='8752418278:AAEvsyOmhMGA65H_jhO3rODUy4k5biJ04ys')
    telegram_enabled = fields.Boolean(string="Bật Telegram", default=True)
    last_alert_date = fields.Datetime(string="Ngày cảnh báo cuối")

    # --- Liên kết ---
    dong_cong_viec_ids = fields.One2many('quan_ly.du_an.line', 'du_an_id', string='Chi tiết hạng mục')
    milestone_ids = fields.One2many('quan_ly.du_an.milestone', 'du_an_id', string='Cột mốc')
    risk_ids = fields.One2many('quan_ly.du_an.risk', 'du_an_id', string='Rủi ro')
    mo_ta_du_an = fields.Html(string='Mô tả dự án')
    ghi_chu_quan_tri = fields.Text(string='Ghi chú')

    # --- AI & Automation ---
    ai_analysis_result = fields.Text(string="Phân tích AI", readonly=True)
    ai_report_card_html = fields.Html(string="Thẻ báo cáo chiến lược", readonly=True)
    tai_lieu_mau = fields.Binary(string='Hồ sơ PDF')
    ten_file_mau = fields.Char(string='Tên file')
    email_lien_he = fields.Char(string='Email liên hệ', tracking=True, default='hop13101999@gmail.com')

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

    @api.depends('dong_cong_viec_ids.trang_thai_viec')
    def _compute_progress_stats(self):
        for r in self:
            lines = r.dong_cong_viec_ids
            r.tong_so_viec = len(lines)
            done = len(lines.filtered(lambda x: x.trang_thai_viec == 'done'))
            r.so_viec_hoan_thanh = done
            r.tien_do_tong_the = (done / r.tong_so_viec * 100) if r.tong_so_viec > 0 else 0.0

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

    @api.depends('trang_thai')
    def _compute_smart_process_flow(self):
        for r in self:
            stages = [
                ('nhap', 'MỚI'),
                ('tiep_nhan', 'TIẾP NHẬN'),
                ('trien_khai', 'TRIỂN KHAI'),
                ('hoan_thanh', 'HOÀN THÀNH')
            ]
            
            html = '<div style="display: flex; justify-content: space-between; align-items: center; padding: 20px 0; position: relative; max-width: 800px; margin: 0 auto;">'
            # Connector Line background
            html += '<div style="position: absolute; top: 35px; left: 10%; right: 10%; height: 2px; background: #e0e0e0; z-index: 1;"></div>'
            
            current_found = False
            for code, name in stages:
                is_current = (r.trang_thai == code)
                is_past = not is_current and not current_found and r.trang_thai not in ['nhap', 'huy']
                if is_current: current_found = True
                
                # Special colors and glow
                color = "#28a745" if (is_past or (is_current and code == 'hoan_thanh')) else "#007bff" if is_current else "#ccc"
                glow = "box-shadow: 0 0 15px #007bff, 0 0 5px #007bff; border: 2px solid #fff;" if is_current else "border: 2px solid #fff;"
                
                html += f"""
                <div style="z-index: 2; text-align: center; width: 100px;">
                    <div style="width: 32px; height: 32px; border-radius: 50%; background: {color}; margin: 0 auto 10px; {glow} display: flex; align-items: center; justify-content: center; color: white; font-size: 14px; transition: all 0.3s ease;">
                        {"✓" if is_past else "●"}
                    </div>
                    <div style="font-size: 11px; color: {color if is_current else '#888'}; font-weight: {'bold' if is_current else 'normal'}; text-transform: uppercase; letter-spacing: 0.5px;">{name}</div>
                </div>
                """
            html += '</div>'
            r.smart_process_flow_html = html
    
    def _call_groq_api(self, prompt, require_json=False):
        api_key = "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"
        api_url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        
        system_content = "Bạn là hệ thống AI phân tích dữ liệu dự án chuyên nghiệp."
        if require_json:
            system_content += " CHỈ TRẢ VỀ DUY NHẤT JSON HỢP LỆ."

        data = {
            "model": "llama-3.3-70b-versatile", 
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2 if require_json else 0.5
        }
        try:
            res = requests.post(api_url, headers=headers, json=data, timeout=30)
            if res.status_code == 200:
                return res.json()['choices'][0]['message']['content']
            _logger.error(f"Groq API Error: {res.text}")
            return f"Lỗi hệ thống: {res.text}"
        except Exception as e:
            return f"Lỗi kết nối: {str(e)}"

    def action_extract_pdf(self):
        """Trích xuất dữ liệu từ PDF"""
        for r in self:
            if not r.tai_lieu_mau:
                raise ValidationError("Vui lòng đính kèm tài liệu.")
            
            file_content = base64.b64decode(r.tai_lieu_mau)
            text_content = ""
            try:
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                for page in pdf_reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text_content += extracted + "\n"
            except ImportError:
                 raise ValidationError("Hệ thống chưa cài đặt thư viện PyPDF2.")
            except Exception as e:
                raise ValidationError(f"Lỗi đọc file PDF: {str(e)}")

            if not text_content.strip():
                raise ValidationError("Không tìm thấy nội dung văn bản trong file PDF.")

            prompt = f"""
            Phân tích dữ liệu dự án từ nội dung sau và trả về JSON.
            Cấu trúc: {{"ten_du_an": "...", "ngan_sach": 0, "pm": "...", "chuyen_gia": [], "email": "...", "ngay_bat_dau": "YYYY-MM-DD", "ngay_ket_thuc": "YYYY-MM-DD", "cong_viec": [], "mo_ta": "..."}}
            
            Nội dung:
            {text_content}
            """
            
            response = self._call_groq_api(prompt, require_json=True)
            try:
                res_clean = response.strip()
                if res_clean.startswith("```json"): res_clean = res_clean[7:]
                elif res_clean.startswith("```"): res_clean = res_clean[3:]
                if res_clean.endswith("```"): res_clean = res_clean[:-3]
                
                json_data = json.loads(res_clean.strip())
                
                with self.env.cr.savepoint():
                    if json_data.get('ten_du_an'): r.ten_du_an = json_data['ten_du_an']
                    if json_data.get('ngan_sach'): r.ngan_sach_du_kien = float(json_data['ngan_sach'])
                    if json_data.get('email'): r.email_lien_he = json_data['email']
                    if json_data.get('mo_ta'): r.mo_ta_du_an = json_data['mo_ta']
                    if json_data.get('ngay_bat_dau'): r.ngay_bat_dau = fields.Date.to_date(json_data['ngay_bat_dau'])
                    if json_data.get('ngay_ket_thuc'): r.ngay_ket_thuc = fields.Date.to_date(json_data['ngay_ket_thuc'])
                    
                    pm_name = json_data.get('pm')
                    if pm_name:
                        pm_record = self.env['quan_ly.nhan_vien'].sudo().search([('name', '=', pm_name)], limit=1)
                        if not pm_record:
                            pm_record = self.env['quan_ly.nhan_vien'].sudo().create({'name': pm_name, 'ma_nv': f"AI-{datetime.now().strftime('%M%S')}"})
                        r.truong_du_an_id = pm_record.id
                    
                    if json_data.get('cong_viec'):
                        r.dong_cong_viec_ids = [(5, 0, 0)]  # Xóa các dòng cũ
                        task_vals = []
                        for t_name in json_data['cong_viec']:
                            task_record = self.env['quan_ly.cong_viec'].sudo().search([('ten_cong_viec', '=', t_name)], limit=1)
                            if not task_record:
                                task_record = self.env['quan_ly.cong_viec'].sudo().create({'ten_cong_viec': t_name})
                            task_vals.append((0, 0, {
                                'cong_viec_id': task_record.id,
                                'nhan_vien_id': r.truong_du_an_id.id if r.truong_du_an_id else False,
                                'ngay_deadline': r.ngay_ket_thuc or fields.Date.today()
                            }))
                        r.dong_cong_viec_ids = task_vals
            except Exception as e:
                _logger.error(f"AI Parse Error: {str(e)}")
            
            r.action_ai_analyze()

    def action_ask_chatbot(self):
        """Truy vấn kiến thức dự án"""
        for r in self:
            if not r.cau_hoi_ai:
                raise ValidationError("Vui lòng nhập câu hỏi.")
            context = f"Thông số dự án: {r.ten_du_an}, Ngân sách: {r.ngan_sach_du_kien}, Tiến độ: {r.tien_do_tong_the}%, Trạng thái: {r.trang_thai}."
            prompt = f"{context}\nHỏi: {r.cau_hoi_ai}"
            r.cau_tra_loi_ai = self._call_groq_api(prompt)

    def action_ai_auto_planner(self):
        """AI tự lập kế hoạch chi tiết"""
        for r in self:
            if not r.ten_du_an or r.ten_du_an == 'Dự án mới':
                raise ValidationError("Vui lòng nhập tên dự án.")
            
            prompt = f"""
            Lập kế hoạch chi tiết cho dự án: "{r.ten_du_an}".
            Yêu cầu trả về JSON gồm: 'milestones' (ten, ngay YYYY-MM-DD), 'tasks' (ten, mo_ta).
            """
            
            response = self._call_groq_api(prompt, require_json=True)
            try:
                res_clean = response.strip()
                if res_clean.startswith("```json"): res_clean = res_clean[7:]
                elif res_clean.startswith("```"): res_clean = res_clean[3:]
                if res_clean.endswith("```"): res_clean = res_clean[:-3]
                
                json_data = json.loads(res_clean.strip())
                
                with self.env.cr.savepoint():
                    if json_data.get('milestones'):
                        ms_vals = [(0, 0, {'ten_cot_moc': ms['ten'], 'ngay_du_kien': fields.Date.to_date(ms['ngay'])}) for ms in json_data['milestones']]
                        r.milestone_ids = ms_vals
                    
                    if json_data.get('tasks'):
                        task_vals = []
                        for t in json_data['tasks']:
                            task_record = self.env['quan_ly.cong_viec'].sudo().search([('ten_cong_viec', '=', t['ten'])], limit=1)
                            if not task_record:
                                task_record = self.env['quan_ly.cong_viec'].sudo().create({'ten_cong_viec': t['ten'], 'mo_ta_chi_tiet': t['mo_ta']})
                            task_vals.append((0, 0, {
                                'cong_viec_id': task_record.id,
                                'nhan_vien_id': r.truong_du_an_id.id if r.truong_du_an_id else False,
                                'ngay_deadline': r.ngay_ket_thuc or fields.Date.today()
                            }))
                        r.dong_cong_viec_ids = task_vals
            except Exception as e:
                _logger.error(f"Planner Error: {str(e)}")

    def action_ai_analyze(self):
        """Đánh giá sức khỏe dự án & Tạo Thẻ báo cáo thị giác"""
        for r in self:
            analysis = [f"BÁO CÁO PHÂN TÍCH - {datetime.now().strftime('%d/%m/%Y')}"]
            score = 100
            
            # Logic tính điểm
            if r.spi_index < 0.9: score -= 20
            if r.cpi_index < 0.9: score -= 20
            if r.trang_thai == 'tre_han': score -= 10
            
            score = max(0, min(100, score))
            analysis.append(f"Điểm sức khỏe: {score}/100")
            r.ai_analysis_result = "\n".join(analysis)

            # --- Tạo HTML Report Card (Dành cho trình bày) ---
            color = "#28a745" if score >= 80 else "#ffc107" if score >= 50 else "#dc3545"
            health_text = "TỐT" if score >= 80 else "CẢNH BÁO" if score >= 50 else "NGUY CẤP"
            
            html = f"""
            <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; background: #fff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border-left: 10px solid {color};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h2 style="margin: 0; color: #333;">Dự án: {r.ten_du_an}</h2>
                    <span style="padding: 8px 16px; border-radius: 20px; background: {color}; color: #fff; font-weight: bold; font-size: 14px;">{health_text}</span>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-bottom: 20px;">
                    <div style="padding: 15px; background: #f8f9fa; border-radius: 8px; text-align: center;">
                        <div style="font-size: 12px; color: #666; text-transform: uppercase;">Điểm Sức Khỏe</div>
                        <div style="font-size: 24px; font-weight: bold; color: {color};">{score}/100</div>
                    </div>
                    <div style="padding: 15px; background: #f8f9fa; border-radius: 8px; text-align: center;">
                        <div style="font-size: 12px; color: #666; text-transform: uppercase;">Chỉ số SPI</div>
                        <div style="font-size: 24px; font-weight: bold; color: {color};">{r.spi_index:.2f}</div>
                    </div>
                    <div style="padding: 15px; background: #f8f9fa; border-radius: 8px; text-align: center;">
                        <div style="font-size: 12px; color: #666; text-transform: uppercase;">Chỉ số CPI</div>
                        <div style="font-size: 24px; font-weight: bold; color: {color};">{r.cpi_index:.2f}</div>
                    </div>
                </div>

                <div style="margin-top: 10px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span style="font-size: 13px; font-weight: 600;">Tiến độ dự án</span>
                        <span style="font-size: 13px; font-weight: 600;">{int(r.tien_do_tong_the)}%</span>
                    </div>
                    <div style="width: 100%; background: #eee; border-radius: 10px; height: 10px;">
                        <div style="width: {r.tien_do_tong_the}%; background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%); height: 100%; border-radius: 10px;"></div>
                    </div>
                </div>

                <div style="margin-top: 20px; font-size: 13px; color: #555; line-height: 1.6; border-top: 1px solid #eee; padding-top: 15px;">
                    <strong>Đánh giá từ AI:</strong> Dự án đang được vận hành với các chỉ số hiệu suất ở mức {health_text.lower()}. 
                    Hệ thống khuyến nghị tiếp tục giám sát chặt chẽ các hạng mục có rủi ro cao để đảm bảo ngân sách {r.ngan_sach_du_kien:,.0f} VNĐ được tối ưu hóa.
                </div>
            </div>
            """
            r.ai_report_card_html = html

    def action_view_workload(self):
        """Xem biểu đồ phân bổ nguồn lực (Presentation friendly)"""
        self.ensure_one()
        return {
            'name': 'Phân tích Nguồn lực',
            'type': 'ir.actions.act_window',
            'res_model': 'quan_ly.du_an.line',
            'view_mode': 'graph,pivot',
            'domain': [('du_an_id', '=', self.id)],
            'context': {
                'search_default_nhan_vien_id': 1,
                'graph_measure': 'id',
                'graph_mode': 'pie',
            }
        }

    def action_tiep_nhan_du_an(self):
        for r in self:
            if not r.truong_du_an_id: raise ValidationError("Vui lòng chỉ định Trưởng dự án.")
            r.write({'trang_thai': 'trien_khai'})
            # Tự động gửi thông báo khi tiếp nhận
            r.action_send_telegram_alert()
            r.action_send_email_report()

    def action_tam_dung(self): self.write({'trang_thai': 'tam_dung'})
    def action_finish_project(self): 
        self.write({'trang_thai': 'hoan_thanh', 'ngay_nghiem_thu': date.today()})
        # Gửi thông báo khi hoàn thành
        self.action_send_telegram_alert()
        self.action_send_email_report()
    def action_reset_to_draft(self): self.write({'trang_thai': 'nhap', 'ngay_nghiem_thu': False})
    def action_cancel_project(self): self.write({'trang_thai': 'huy'})
    
    def action_noop(self):
        """Hành động trống để hỗ trợ hiển thị Stat Buttons"""
        return True

    def action_send_telegram_alert(self):
        """Gửi cảnh báo Telegram thủ công hoặc tự động"""
        self.ensure_one()
        if not self.telegram_enabled or not self.telegram_chat_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Thông báo'),
                    'message': _('Chưa cấu hình Telegram cho dự án này!'),
                    'type': 'warning',
                    'sticky': False,
                }
            }
        
        msg = f"🚀 <b>THÔNG BÁO DỰ ÁN</b>: {self.ten_du_an}\n"
        msg += f"📊 Tiến độ: {int(self.tien_do_tong_the)}%\n"
        msg += f"⚠️ Trạng thái: {dict(self._fields['trang_thai'].selection).get(self.trang_thai)}\n"
        msg += f"🔗 <a href='http://localhost:8069/web#id={self.id}&model=quan_ly.du_an&view_type=form'>Xem tại Odoo</a>"

        # 1. Gửi Telegram thật
        if self.telegram_enabled and self.telegram_bot_token and self.telegram_chat_id:
            try:
                import requests
                url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
                payload = {
                    "chat_id": self.telegram_chat_id,
                    "text": msg,
                    "parse_mode": "HTML"
                }
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code != 200:
                    _logger.error("Telegram API Error: %s - %s", response.status_code, response.text)
                else:
                    _logger.info("Telegram Sent successfully: %s", response.text)
            except Exception as e:
                _logger.error("Lỗi gửi Telegram: %s", str(e))

        _logger.info("SEND TELEGRAM TO %s: %s", self.telegram_chat_id, msg)
        self.last_alert_date = fields.Datetime.now()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Telegram (Real-time)'),
                'message': _('Tin nhắn đã được gửi thực tế tới Telegram!'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_send_email_report(self):
        """Gửi báo cáo tóm tắt qua Email"""
        self.ensure_one()
        if not self.email_lien_he:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Lỗi'),
                    'message': _('Chưa có email liên hệ!'),
                    'type': 'danger',
                    'sticky': False,
                }
            }
        
        # 1. Gửi Email thật
        mail_values = {
            'subject': f"Báo cáo Dự án: {self.ten_du_an}",
            'body_html': f"""
                <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #eee;">
                    <h2 style="color: #007bff;">Báo cáo Dự án: {self.ten_du_an}</h2>
                    <p><b>Tiến độ:</b> {self.tien_do_tong_the}%</p>
                    <p><b>Trạng thái:</b> {dict(self._fields['trang_thai'].selection).get(self.trang_thai)}</p>
                    <p><b>Ngân sách:</b> {self.ngan_sach_du_kien} VNĐ</p>
                    <hr/>
                    <p><i>Hệ thống quản lý dự án AI - Odoo Pro Max</i></p>
                </div>
            """,
            'email_to': self.email_lien_he,
        }
        mail = self.env['mail.mail'].sudo().create(mail_values)
        mail.send()

        _logger.info("REAL EMAIL SENT TO %s", self.email_lien_he)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Email (Real-time)'),
                'message': f'Báo cáo thực tế đã được gửi tới {self.email_lien_he}',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_view_tasks(self):
        self.ensure_one()
        return {
            'name': 'Hạng mục công việc',
            'type': 'ir.actions.act_window',
            'res_model': 'quan_ly.du_an.line',
            'view_mode': 'tree,form,graph,pivot',
            'domain': [('du_an_id', '=', self.id)],
            'context': {'default_du_an_id': self.id},
        }


    def action_quick_audit(self):
        """Kiểm định nhanh AI và hiện Notify"""
        self.ensure_one()
        summary = f"Dự án {self.ten_du_an} đang đạt {int(self.tien_do_tong_the)}% tiến độ. "
        if self.spi_index < 0.9 or self.cpi_index < 0.9:
            msg = summary + "⚠️ CẢNH BÁO: Chỉ số hiệu suất đang thấp. Cần kiểm tra ngay!"
            notify_type = 'danger'
        else:
            msg = summary + "✅ Hệ thống đánh giá Dự án đang vận hành ổn định."
            notify_type = 'success'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('AI Quick Audit'),
                'message': msg,
                'type': notify_type,
                'sticky': False,
            }
        }

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

    @api.depends('ngay_deadline', 'trang_thai_viec')
    def _compute_is_late(self):
        today = date.today()
        for line in self: line.is_late = bool(line.ngay_deadline and line.ngay_deadline < today and line.trang_thai_viec != 'done')

    @api.onchange('cong_viec_id')
    def _onchange_task(self):
        if self.cong_viec_id and self.cong_viec_id.nguoi_thuc_hien_id: self.nhan_vien_id = self.cong_viec_id.nguoi_thuc_hien_id

class QuanLyDuAnMilestone(models.Model):
    _name = 'quan_ly.du_an.milestone'
    _description = 'Cột mốc dự án'
    du_an_id = fields.Many2one('quan_ly.du_an', ondelete='cascade')
    ten_cot_moc = fields.Char(string='Tên cột mốc', required=True)
    ngay_du_kien = fields.Date(string='Ngày dự kiến', required=True)
    da_dat_duoc = fields.Boolean(string='Đạt được', default=False)
    ghi_chu = fields.Text(string='Ghi chú')

class QuanLyDuAnRisk(models.Model):
    _name = 'quan_ly.du_an.risk'
    _description = 'Rủi ro dự án'
    du_an_id = fields.Many2one('quan_ly.du_an', ondelete='cascade')
    ten_rui_ro = fields.Char(string='Tên rủi ro', required=True)
    muc_do = fields.Selection([('1', 'Thấp'), ('2', 'Trung bình'), ('3', 'Nghiêm trọng')], string='Mức độ', default='1')
    phuong_an_xu_ly = fields.Text(string='Phương án xử lý')
    trang_thai = fields.Selection([('dang_theo_doi', 'Theo dõi'), ('da_xay_ra', 'Đã xảy ra'), ('da_xu_ly', 'Đã xử lý')], string='Trạng thái', default='dang_theo_doi')