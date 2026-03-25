# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.http import request
import json

class QuanLyDashboard(models.Model):
    _name = 'quan_ly.dashboard'
    _description = 'Bảng điều hành Hệ thống'

    name = fields.Char(default="Executive Dashboard")
    dashboard_html = fields.Html(compute='_compute_dashboard_html', sanitize=False)
    ai_report_html = fields.Html(sanitize=False)

    def _compute_dashboard_html(self):
        projects = self.env['quan_ly.du_an'].search([])
        count_projects = len(projects)
        budget = sum(projects.mapped('ngan_sach_du_kien')) or 0
        cost = budget * 0.45 # Ước tính chi phí vì Odoo chưa lưu field này chính thức
        profit = budget - cost
        
        val_p = f"{count_projects}"
        val_b = f"{budget/1000000:,.0f}M"
        val_c = f"{cost/1000000:,.0f}M"
        val_pr = f"{profit/1000000:,.0f}M"

        # Dynamically map reps
        pm_data = {}
        for p in projects:
            pm = p.truong_du_an_id
            pid = pm.id if pm else 0
            pname = pm.name if pm else "Chưa phân công"
            if pid not in pm_data:
                pm_data[pid] = {'name': pname, 'id': pid, 'count': 0, 'budget': 0, 'progress_sum': 0}
            pm_data[pid]['count'] += 1
            pm_data[pid]['budget'] += (p.ngan_sach_du_kien or 0)
            pm_data[pid]['progress_sum'] += (p.tien_do_tong_the or 0)
            
        top_pms = sorted(pm_data.values(), key=lambda x: x['budget'], reverse=True)[:5]
        
        rep_html = ""
        for i, m in enumerate(top_pms):
            prog_val = int(m['progress_sum'] / m['count']) if m['count'] else 0
            score = f"{10 - min(i, 5)}/10"
            rev_str = f"{m['budget']/1000000:,.1f}M"
            prof_str = f"{(m['budget']*0.45)/1000000:,.1f}M"
            
            link = f"/web#model=quan_ly.du_an&view_type=list&domain=%5B%5B%22truong_du_an_id%22%2C%22%3D%22%2C{m['id']}%5D%5D" if m['id'] else "/web#model=quan_ly.du_an&view_type=list"
            rep_html += f"""
            <a href="{link}" style="text-decoration:none;" class="rep-card interactive-card">
                <div class="rep-header">
                    <div class="rep-name">{m['name']}</div>
                    <div style="text-align: right;">
                        <span class="rep-score-label">Hiệu suất</span>
                        <span class="rep-score">{score}</span>
                    </div>
                </div>
                <div class="rep-body">
                    <div>
                        <div class="rep-value">{rev_str}</div>
                        <div class="rep-progress-bg">
                            <div class="rep-progress-fill" style="width: {prog_val}%;"></div>
                        </div>
                        <div class="rep-target">Tiến độ {prog_val}%</div>
                    </div>
                    <div class="rep-details">
                        <table style="width: 100%; border-collapse: collapse; color: #fff;">
                            <tr><td style="opacity: 0.9; padding-right: 8px; text-align: right;">Lợi nhuận</td><td style="font-weight:700; width: 60px; text-align: right;">{prof_str}</td></tr>
                            <tr><td style="opacity: 0.9; padding-right: 8px; text-align: right;">Số dự án</td><td style="font-weight:700; width: 60px; text-align: right;">{m['count']}</td></tr>
                        </table>
                    </div>
                </div>
            </a>
            """

        # Chart Data extraction
        import json
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        budget_by_month = [0.0]*12
        progress_by_month = [0.0]*12
        count_by_month = [0]*12
        for p in projects:
            if p.ngay_bat_dau:
                mb = p.ngay_bat_dau.month - 1
                budget_by_month[mb] += (p.ngan_sach_du_kien or 0) / 1000000.0
                progress_by_month[mb] += p.tien_do_tong_the
                count_by_month[mb] += 1
                
        for i in range(12):
            if count_by_month[i] > 0:
                progress_by_month[i] = round(progress_by_month[i] / count_by_month[i], 1)
                
        # Type breakdown (Donut)
        types_count = {}
        for p in projects:
            t = dict(p._fields['loai_du_an'].selection).get(p.loai_du_an, 'Khác')
            types_count[t] = types_count.get(t, 0) + 1
        donut_labels = list(types_count.keys()) or ['Chưa có']
        donut_data = list(types_count.values()) or [1]
            
        # Status breakdown (Horizontal Bar)
        status_count = {}
        for p in projects:
            s = dict(p._fields['trang_thai'].selection).get(p.trang_thai, 'N/A')
            status_count[s] = status_count.get(s, 0) + 1
        barh_labels = list(status_count.keys()) or ['N/A']
        barh_data = list(status_count.values()) or [0]

        html = f"""
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700;900&display=swap');
            
            .db-container {{
                display: grid;
                grid-template-columns: minmax(0, 3fr) minmax(0, 1fr);
                gap: 15px;
                background: #f2f2f2;
                padding: 15px;
                font-family: 'Roboto', sans-serif;
                color: #333;
                min-height: 100vh;
            }}
            .db-left {{ display: flex; flex-direction: column; gap: 15px; }}
            .db-right {{ display: flex; flex-direction: column; gap: 10px; background: #fff; padding: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-radius: 8px; }}
            
            .db-header {{ display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 5px; }}
            .db-title {{ font-size: 26px; font-weight: 900; color: #111; margin: 0; text-transform: uppercase; letter-spacing: 0.5px; }}
            .db-date-picker {{ background: #fff; border: 1px solid #ddd; padding: 6px 30px 6px 12px; font-size: 13px; color: #555; position: relative; border-radius: 4px; }}
            
            .db-row-4 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; }}
            .db-card {{ background: #fff; padding: 12px 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); display: flex; flex-direction: column; justify-content: center; border-radius: 8px; }}
            
            /* INTERACTIVITY */
            .interactive-card {{ transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); cursor: pointer; text-decoration: none; color: inherit; display: block; }}
            .interactive-card:hover {{ transform: translateY(-4px); box-shadow: 0 12px 24px rgba(39, 139, 123, 0.15) !important; z-index: 10; border-color: transparent !important; }}
            
            .kpi-title {{ font-size: 10.5px; font-weight: 700; color: #111; text-transform: uppercase; margin-bottom: 4px; }}
            .kpi-value {{ font-size: 26px; font-weight: 300; color: #278b7b; margin-bottom: 8px; letter-spacing: -0.5px; }}
            .kpi-metrics {{ display: flex; justify-content: flex-start; gap: 15px; font-size: 14px; font-weight: 600; align-items: center; }}
            .pos {{ color: #28a745; }}
            .neg {{ color: #dc3545; }}
            
            .db-row-2 {{ display: grid; grid-template-columns: 2fr 1fr; gap: 15px; height: 260px; }}
            .db-row-3 {{ display: grid; grid-template-columns: 1fr 1fr 1.5fr; gap: 15px; height: 320px; }}
            
            .text-block {{ display: flex; flex-direction: column; justify-content: space-between; height: 100%; }}
            .tb-section {{ margin-bottom: 15px; }}
            .tb-title {{ font-size: 12px; font-weight: 900; color: #111; border-top: 4px solid #ddd; padding-top: 5px; margin-bottom: 10px; }}
            .tb-row {{ display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 8px; color: #333; }}
            .tb-val {{ color: #278b7b; font-weight: 500; }}
            
            .rep-title {{ font-size: 20px; font-weight: 900; color: #111; margin: 0 0 15px 0; text-transform: uppercase; }}
            .rep-card {{ background: #278b7b; color: #fff; padding: 12px; margin-bottom: 10px; display: flex; flex-direction: column; justify-content: space-between; height: 105px; border-radius: 8px; }}
            .rep-header {{ display: flex; justify-content: space-between; }}
            .rep-name {{ font-size: 14px; font-weight: 700; }}
            .rep-score-label {{ font-size: 10px; font-weight: 400; opacity: 0.9; margin-right: 5px; }}
            .rep-score {{ font-size: 13px; font-weight: 700; }}
            .rep-body {{ display: flex; justify-content: space-between; align-items: flex-end; }}
            .rep-value {{ font-size: 22px; font-weight: 700; letter-spacing: -0.5px; line-height: 1; }}
            .rep-details {{ font-size: 10.5px; line-height: 1.4; }}
            .rep-progress-bg {{ background: rgba(255,255,255,0.3); height: 6px; margin-top: 8px; width: 110px; border-radius: 5px; overflow: hidden; }}
            .rep-progress-fill {{ background: #fff; height: 100%; border-radius: 5px; }}
            .rep-target {{ font-size: 9px; margin-top: 4px; opacity: 0.8; }}
        </style>

        <div class="db-container">
            <!-- LEFT MAIN CONTENT -->
            <div class="db-left">
                <!-- Header -->
                <div class="db-header">
                    <h1 class="db-title">Tổng quan Thực tế</h1>
                    <div class="db-date-picker">Live Data</div>
                </div>

                <!-- KPI Cards (Clickable) -->
                <div class="db-row-4">
                    <a href="/web#model=quan_ly.du_an&view_type=kanban" class="db-card interactive-card">
                        <div class="kpi-title">Tổng Dự án</div>
                        <div class="kpi-value">{val_p}</div>
                        <div class="kpi-metrics"><span class="pos">+{(count_by_month[-1])} Tháng này</span></div>
                    </a>
                    <div class="db-card interactive-card">
                        <div class="kpi-title">Tổng Ngân sách</div>
                        <div class="kpi-value">{val_b}</div>
                        <div class="kpi-metrics"><span class="pos">+5% Đầu tư</span></div>
                    </div>
                    <div class="db-card interactive-card">
                        <div class="kpi-title">Chi phí Ước tính</div>
                        <div class="kpi-value">{val_c}</div>
                        <div class="kpi-metrics"><span class="neg">An toàn</span></div>
                    </div>
                    <div class="db-card interactive-card">
                        <div class="kpi-title">Lợi nhuận Kì vọng</div>
                        <div class="kpi-value">{val_pr}</div>
                        <div class="kpi-metrics"><span class="pos">ROI Cao</span></div>
                    </div>
                </div>

                <!-- Middle Charts -->
                <div class="db-row-2">
                    <div class="db-card interactive-card" style="padding: 15px 15px 5px 15px;">
                        <div class="kpi-title" style="margin-bottom: 10px;">Tiến độ & Ngân sách các tháng</div>
                        <div style="height: 200px; position: relative;">
                            <canvas id="areaChart"></canvas>
                        </div>
                    </div>
                    <div class="db-card interactive-card">
                        <div class="kpi-title" style="margin-bottom: 20px;">Cơ cấu Loại Dự án</div>
                        <div style="display: flex; height: 200px; position: relative;">
                            <div style="flex: 1; position: relative;">
                                <canvas id="donutChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Bottom Charts -->
                <div class="db-row-3">
                    <div class="db-card" style="background: transparent; box-shadow: none; padding: 0;">
                        <div class="text-block">
                            <div class="db-card tb-section interactive-card">
                                <div class="tb-title">Theo dõi Rủi ro</div>
                                <div class="tb-row"><span>Rủi ro cao</span> <span class="tb-val">Cần chú ý</span></div>
                                <div class="tb-row"><span>Cảnh báo</span> <span class="tb-val" style="color:#d97706;">Live</span></div>
                            </div>
                            <div class="db-card tb-section interactive-card" style="margin-bottom: 0;">
                                <div class="tb-title">Hiệu suất Hệ thống</div>
                                <div class="tb-row"><span>Trễ hạn</span> <span class="tb-val" style="color:#dc2626;">Giám sát</span></div>
                                <div class="tb-row"><span>Lệnh tạo</span> <span class="tb-val">{val_p}</span></div>
                            </div>
                        </div>
                    </div>
                    <div class="db-card interactive-card" style="padding: 15px 15px 5px 15px;">
                        <div class="kpi-title" style="margin-bottom: 15px;">Ngân sách Giải ngân (M)</div>
                        <div style="height: 250px; position: position: relative;">
                            <canvas id="barVChart"></canvas>
                        </div>
                    </div>
                    <div class="db-card interactive-card" style="padding: 15px 15px 5px 15px;">
                        <div class="kpi-title" style="margin-bottom: 15px;">Trạng thái Dự án</div>
                        <div style="height: 250px; position: position: relative;">
                            <canvas id="barHChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>

            <!-- RIGHT SIDEBAR (Managers) -->
            <div class="db-right">
                <h2 class="rep-title">TOP Quản Lý</h2>
                {rep_html}
            </div>
        </div>
        
        <script>
            setTimeout(function() {{
                if(typeof Chart === 'undefined') return;
                
                Chart.defaults.font.family = "'Roboto', sans-serif";
                Chart.defaults.color = '#777';
                
                const primaryColor = '#278b7b';
                const secondaryColor = '#9de0d6';

                // Real Data
                const v_months = {json.dumps(months)};
                const v_progress = {json.dumps(progress_by_month)};
                const v_budget = {json.dumps(budget_by_month)};
                
                const v_donut_labels = {json.dumps(donut_labels)};
                const v_donut_data = {json.dumps(donut_data)};
                
                const v_barh_labels = {json.dumps(barh_labels)};
                const v_barh_data = {json.dumps(barh_data)};

                // Area Chart
                const ctxArea = document.getElementById('areaChart').getContext('2d');
                new Chart(ctxArea, {{
                   type: 'line',
                   data: {{
                      labels: v_months,
                      datasets: [
                         {{ label: 'Tiến độ trung bình (%)', data: v_progress, backgroundColor: secondaryColor, borderColor: secondaryColor, fill: false, tension: 0.4, borderWidth: 3 }},
                         {{ label: 'Ngân sách (M VNĐ)', data: v_budget, backgroundColor: primaryColor, fill: true, tension: 0.4, borderWidth: 0, pointRadius: 0 }}
                      ]
                   }},
                   options: {{ 
                       responsive: true, maintainAspectRatio: false, 
                       interaction: {{ mode: 'index', intersect: false }},
                       plugins: {{ legend: {{ display: true, position: 'bottom' }} }},
                       scales: {{ x: {{ grid: {{display: false}} }}, y: {{ grid: {{color: '#f0f0f0'}} }} }} 
                   }}
                }});

                // Donut Chart
                const ctxDonut = document.getElementById('donutChart').getContext('2d');
                new Chart(ctxDonut, {{
                   type: 'doughnut',
                   data: {{
                      labels: v_donut_labels,
                      datasets: [{{ data: v_donut_data, backgroundColor: [primaryColor, secondaryColor, '#4ec7b3', '#bdf0e5', '#1c6659'], borderWidth: 0 }}]
                   }},
                   options: {{ 
                       responsive: true, maintainAspectRatio: false, cutout: '65%',
                       plugins: {{ legend: {{ display: true, position: 'bottom' }} }}
                   }}
                }});

                // Vertical Bar Chart
                const ctxBarV = document.getElementById('barVChart').getContext('2d');
                new Chart(ctxBarV, {{
                   type: 'bar',
                   data: {{
                      labels: v_months,
                      datasets: [{{ label: 'Ngân sách giải ngân (M VNĐ)', data: v_budget, backgroundColor: primaryColor, barPercentage: 0.7 }}]
                   }},
                   options: {{ 
                       responsive: true, maintainAspectRatio: false,
                       plugins: {{ legend: {{ display: false }} }},
                       scales: {{ x: {{ grid: {{display: false}}, ticks: {{ display: true }} }}, y: {{ grid: {{borderDash: [5,5], color: '#eee'}}, ticks: {{callback: v => v + 'M'}} }} }} 
                   }}
                }});

                // Horizontal Bar Chart
                const ctxBarH = document.getElementById('barHChart').getContext('2d');
                new Chart(ctxBarH, {{
                   type: 'bar',
                   data: {{
                      labels: v_barh_labels,
                      datasets: [{{ label: 'Số lượng Dự án', data: v_barh_data, backgroundColor: ['#278b7b', '#4ec7b3', '#71d4c2', '#9de0d6', '#bdf0e5', '#d9f5ef'] }}]
                   }},
                   options: {{ 
                       indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                       plugins: {{ legend: {{ display: false }} }},
                       scales: {{ x: {{ grid: {{display: false}}, ticks: {{stepSize: 1}} }}, y: {{ grid: {{display: false}} }} }} 
                   }}
                }});
            }}, 600);
        </script>
        """
        self.dashboard_html = html

    @api.model
    def open_dashboard(self):
        dashboard = self.search([], limit=1)
        if not dashboard:
            dashboard = self.create({'name': 'Executive Dashboard'})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bảng điều hành',
            'res_model': 'quan_ly.dashboard',
            'res_id': dashboard.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_generate_ai_report(self):
        # Gather data for AI
        projects = self.env['quan_ly.du_an'].search([])
        names = ", ".join(projects.mapped('ten_du_an')[:5])
        budget = sum(projects.mapped('ngan_sach_du_kien'))
        avg_progress = sum(projects.mapped('tien_do_tong_the')) / len(projects) if projects else 0

        # Call Groq API via requests
        api_key = self.env['ir.config_parameter'].sudo().get_param('quan_ly_du_an.groq_api_key', 
                                                                  default="GROQ_API_KEY")
        
        prompt = f"Phân tích quản trị hệ thống: Bạn là chuyên gia phân tích. Có {len(projects)} dự án đang chạy. Top dự án tiêu biểu: {names}. Tổng ngân sách: {budget:,.0f} VND. Tiến độ trung bình: {avg_progress:.1f}%. Hãy viết 1 đoạn báo cáo cực kỳ ngắn gọn (khoảng 150 chữ) tóm tắt tình hình, cảnh báo rủi ro nếu có và đưa ra khuyến nghị."
        
        report_text = "Không thể kết nối hệ thống AI (Thiếu API Key hoặc lỗi mạng HTTP)."
        if api_key:
            try:
                import requests
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.5,
                    "max_tokens": 800
                }
                response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=20)
                if response.status_code == 200:
                    report_text = response.json()['choices'][0]['message']['content']
                    report_text = report_text.replace('\n', '<br>')
                elif response.status_code == 401:
                    report_text = "<b>Lỗi Groq API (401):</b> API Key không hợp lệ hoặc đã hết hạn. Vui lòng cấu hình key mới tại <i>Settings > Technical > System Parameters</i> (Key: <code>quan_ly_du_an.groq_api_key</code>)."
                else:
                    report_text = f"Lỗi Groq API ({response.status_code}): {response.text[:200]}"
            except Exception as e:
                report_text = f"Lỗi hệ thống: {str(e)}"

        html = f"""
        <div style="font-family: 'Roboto', sans-serif; background: #fff; border: 2px solid #278b7b; border-radius: 8px; padding: 25px; margin-bottom: 20px;">
            <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #eee; padding-bottom: 15px; margin-bottom: 20px;">
                <h3 style="margin: 0; color: #111; font-size: 20px; font-weight: 900;">BÁO CÁO AI</h3>
                <span style="background: #278b7b; color: #fff; font-size: 11px; padding: 4px 12px; border-radius: 20px; font-weight: bold;">LIVE</span>
            </div>
            <div style="color: #444; font-size: 15px; line-height: 1.8;">{report_text}</div>
            <div style="margin-top: 20px; font-size: 11px; color: #888; text-align: right;">AI Groq-Mixtral</div>
        </div>
        """
        self.ai_report_html = html
