# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import xlrd

class ImportNhanVien(models.TransientModel):
    _name = 'quan_ly.import.nhan.vien'
    _description = 'Import Nhân viên từ Excel'

    file_excel = fields.Binary(string='File Excel (.xls, .xlsx)', required=True)
    file_name = fields.Char(string='Tên file')

    def action_import(self):
        try:
            # 1. Giải mã file upload
            data = base64.b64decode(self.file_excel)
            
            # 2. Đọc file bằng xlrd
            workbook = xlrd.open_workbook(file_contents=data)
            sheet = workbook.sheet_by_index(0) # Lấy sheet đầu tiên
            
            # 3. Lặp qua từng dòng (Bỏ qua dòng tiêu đề - dòng 0)
            for row_index in range(1, sheet.nrows):
                row = sheet.row_values(row_index)
                
                # --- CẬP NHẬT INDEX CỘT CHO KHỚP FILE EXCEL ---
                # Cột 0: STT (Bỏ qua)
                
                # Cột 1 (B): Mã NV 
                # (Xử lý .split('.')[0] để tránh trường hợp Excel tự biến 123 thành 123.0)
                ma_nv = str(row[1]).split('.')[0].strip()
                
                # Cột 2 (C): Họ và tên
                ten_nv = str(row[2]).strip()
                
                # Cột 3 (D): Phòng Ban (Đơn vị)
                ten_don_vi = str(row[3]).strip()

                # Cột 4 (E): Lương cơ bản
                # (Xử lý xóa dấu phẩy ngăn cách hàng nghìn nếu có: "30,000,000" -> "30000000")
                try:
                    raw_luong = str(row[4]).replace(',', '').replace('.', '')
                    # Kiểm tra xem có phải số không
                    if not raw_luong.isnumeric():
                        # Trường hợp float thuần trong excel
                        luong_cb = float(row[4])
                    else:
                        luong_cb = float(raw_luong)
                except:
                    luong_cb = 0

                # Cột 5 (F): Phụ cấp
                try:
                    raw_phu_cap = str(row[5]).replace(',', '').replace('.', '')
                    if not raw_phu_cap.isnumeric():
                        phu_cap = float(row[5])
                    else:
                        phu_cap = float(raw_phu_cap)
                except:
                    phu_cap = 0

                # Cột 6 (G): Số ngày công chuẩn
                try:
                    ngay_cong = int(float(row[6]))
                except:
                    ngay_cong = 26 # Mặc định

                # 4. Tìm ID Đơn vị (Nếu chưa có thì TỰ TẠO MỚI luôn cho tiện)
                don_vi = self.env['quan_ly.don_vi'].search([('name', '=', ten_don_vi)], limit=1)
                if not don_vi and ten_don_vi:
                    don_vi = self.env['quan_ly.don_vi'].create({
                        'name': ten_don_vi, 
                        'ma_don_vi': 'NEW' # Mã tạm
                    })
                
                # 5. Kiểm tra Nhân viên đã tồn tại chưa (Dựa vào Mã NV)
                nhan_vien_exist = self.env['quan_ly.nhan_vien'].search([('ma_nv', '=', ma_nv)], limit=1)
                
                vals = {
                    'ma_nv': ma_nv,
                    'name': ten_nv,
                    'luong_co_ban': luong_cb,
                    'phu_cap_mac_dinh': phu_cap,
                    'ngay_cong_chuan': ngay_cong,
                    'don_vi_id': don_vi.id if don_vi else False,
                }

                if not nhan_vien_exist:
                    # Nếu chưa có -> Tạo mới
                    self.env['quan_ly.nhan_vien'].create(vals)
                else:
                    # Nếu đã có -> Cập nhật thông tin
                    nhan_vien_exist.write(vals)
            
            # Thông báo thành công (Odoo tự load lại trang)
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
            
        except Exception as e:
            # Hiện thông báo lỗi chi tiết dòng nào bị sai
            raise UserError(f"Lỗi tại dòng {row_index + 1}: {str(e)}")