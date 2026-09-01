import json
from django.conf import settings
from django.core.mail import EmailMessage
from weasyprint import HTML


def generate_pdf_and_send_email(user_email: str, data: dict):
    """
    Hàm dịch vụ tạo PDF và gửi email đính kèm.
    Đã bổ sung Logo và Slogan thương hiệu Reconnect 360°.
    """
    if not user_email:
        print("Lỗi: user_email không được để trống!")
        return

    # 1. Trích xuất dữ liệu an toàn
    total_score = data.get('total_score', data.get('total', 0))

    # Nhóm A + B + C (Thu mình)
    abc_score = data.get('abc_score', data.get('score_abc', 0))
    abc_level = data.get('abc_level', data.get('level_abc', 'Chưa xác định'))
    abc_comment = data.get('abc_comment', data.get('comment_abc', 'Chưa có nhận xét chi tiết.'))
    abc_recommendation = data.get('abc_recommendation', data.get('recommendation_abc', ''))

    # Nhóm D (Kết nối xã hội)
    d_score = data.get('d_score', data.get('score_d', 0))
    d_level = data.get('d_level', data.get('level_d', 'Chưa xác định'))
    d_comment = data.get('d_comment', data.get('comment_d', 'Chưa có nhận xét chi tiết.'))
    d_recommendation = data.get('d_recommendation', data.get('recommendation_d', ''))

    # Đổi ký tự xuống dòng thành <br>
    abc_comment_html = str(abc_comment).replace('\n', '<br>')
    abc_recommendation_html = str(abc_recommendation).replace('\n', '<br>') if abc_recommendation else ''
    d_comment_html = str(d_comment).replace('\n', '<br>')
    d_recommendation_html = str(d_recommendation).replace('\n', '<br>') if d_recommendation else ''

    # 2. Các mốc giới hạn điểm
    thresholds_abc = [
        {'label': 'Mức 1<br>(0-17đ)', 'max': 17},
        {'label': 'Mức 2<br>(18-35đ)', 'max': 35},
        {'label': 'Mức 3<br>(36-54đ)', 'max': 54},
        {'label': 'Mức 4<br>(55-72đ)', 'max': 72},
    ]

    thresholds_d = [
        {'label': 'Mức 1<br>(0-6đ)', 'max': 6},
        {'label': 'Mức 2<br>(7-12đ)', 'max': 12},
        {'label': 'Mức 3<br>(13-18đ)', 'max': 18},
        {'label': 'Mức 4<br>(19-24đ)', 'max': 24},
    ]

    # Hàm tạo HTML cho Biểu đồ Cột + Đường (Căn chỉnh chính xác vị trí cho WeasyPrint)
    def render_combo_chart_html(user_score, thresholds, max_scale=80):
        user_line_percent = min(100, max(0, float(user_score) / max_scale * 100))
        line_px = int(120 * user_line_percent / 100)

        cols_html = ""
        for item in thresholds:
            bar_height_percent = min(100, max(0, float(item['max']) / max_scale * 100))
            bar_px = int(120 * bar_height_percent / 100)

            cols_html += f"""
            <td class="chart-col-td">
                <div class="col-canvas-box">
                    <!-- Cột xám mọc từ đáy lên -->
                    <div class="bar-fill-bg" style="height: {bar_px}px;"></div>
                    <!-- Điểm chấm tròn người dùng -->
                    <div class="point-dot" style="bottom: {line_px - 4}px;"></div>
                </div>
                <div class="col-label">{item['label']}</div>
            </td>
            """

        return f"""
        <div class="combo-chart-box">
            <div class="chart-canvas-area">
                <!-- Đường đứt nét điểm người dùng -->
                <div class="user-score-line" style="bottom: {line_px + 24}px;"></div>

                <table class="chart-table">
                    <tr>
                        {cols_html}
                    </tr>
                </table>
            </div>

            <div class="chart-legend">
                <span class="legend-box grey-box"></span>
                <span style="margin-right: 15px;">Giới hạn mức điểm</span>
                <span class="legend-box blue-line"></span>
                <span>Điểm của bạn ({user_score}đ)</span>
            </div>
        </div>
        """

    chart_abc_html = render_combo_chart_html(abc_score, thresholds_abc, max_scale=80)
    chart_d_html = render_combo_chart_html(d_score, thresholds_d, max_scale=30)

    # Lấy URL Logo từ Settings hoặc Dùng đường dẫn static/logo chuẩn
    logo_url = getattr(settings, 'COMPANY_LOGO_URL', 'https://reconnect360.vn/static/images/reconnect360_logo.png')

    # 3. HTML Template xuất PDF
    html_template = f"""
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: A4;
                margin: 10mm 15mm;
            }}
            body {{
                font-family: 'Helvetica Neue', Arial, sans-serif;
                color: #0d121b;
                line-height: 1.4;
                padding: 0;
                margin: 0;
            }}
            
            /* Branding Header (Logo + Slogan) */
            .brand-header-table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 8px;
            }}
            .brand-logo-td {{
                width: 40%;
                vertical-align: middle;
            }}
            .brand-slogan-td {{
                width: 60%;
                text-align: right;
                vertical-align: middle;
            }}
            .logo-img {{
                max-height: 38px;
                width: auto;
            }}
            .logo-fallback {{
                font-size: 18px;
                font-weight: bold;
                color: #1152d4;
                letter-spacing: -0.5px;
            }}
            .brand-slogan {{
                font-size: 10px;
                font-style: italic;
                color: #4c669a;
                font-weight: 500;
            }}

            .header {{
                text-align: center;
                border-bottom: 2px solid #1152d4;
                padding-bottom: 6px;
                margin-bottom: 10px;
            }}
            h2 {{
                color: #1152d4;
                font-size: 16px;
                font-weight: bold;
                margin: 0 0 4px 0;
                text-transform: uppercase;
            }}
            .subtitle {{
                color: #4c669a;
                font-size: 10px;
                margin: 0;
            }}

            /* Card Tổng điểm */
            .total-card {{
                background-color: #f8fafc;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 6px;
                text-align: center;
                margin-bottom: 10px;
            }}
            .total-label {{
                font-size: 10px;
                font-weight: bold;
                color: #4c669a;
                text-transform: uppercase;
            }}
            .total-val {{
                font-size: 20px;
                font-weight: bold;
                color: #1152d4;
            }}

            /* Khối từng Nhóm */
            .group-card {{
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 10px;
                margin-bottom: 10px;
                background-color: #ffffff;
            }}
            .group-title {{
                font-size: 12px;
                font-weight: bold;
                color: #0d121b;
            }}
            .group-score {{
                font-size: 11px;
                color: #4c669a;
                margin-bottom: 8px;
            }}

            /* ================= CHART TABLE STYLES (FIX WEASYPRINT) ================= */
            .combo-chart-box {{
                background-color: #fafafa;
                border: 1px solid #f1f5f9;
                border-radius: 6px;
                padding: 10px 8px 6px 8px;
                margin-bottom: 10px;
            }}
            .chart-canvas-area {{
                position: relative;
            }}
            .chart-table {{
                width: 100%;
                border-collapse: collapse;
                table-layout: fixed;
            }}
            .chart-col-td {{
                width: 25%;
                vertical-align: bottom;
                text-align: center;
                padding: 0;
            }}
            .col-canvas-box {{
                height: 120px;
                position: relative;
                border-bottom: 2px solid #94a3b8;
            }}
            .bar-fill-bg {{
                width: 32px;
                background-color: #e2e8f0;
                border: 1px solid #cbd5e1;
                border-bottom: none;
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                margin: 0 auto;
            }}
            .point-dot {{
                position: absolute;
                width: 8px;
                height: 8px;
                background-color: #1d4ed8;
                border-radius: 50%;
                left: 0;
                right: 0;
                margin: 0 auto;
                z-index: 10;
            }}
            .user-score-line {{
                position: absolute;
                left: 0;
                right: 0;
                border-top: 2px dashed #1d4ed8;
                z-index: 5;
            }}
            .col-label {{
                font-size: 8px;
                color: #334155;
                font-weight: bold;
                padding-top: 6px;
                line-height: 1.2;
                text-align: center;
            }}

            /* Legend */
            .chart-legend {{
                text-align: center;
                margin-top: 6px;
                font-size: 9px;
                color: #475569;
            }}
            .legend-box {{
                display: inline-block;
                vertical-align: middle;
            }}
            .grey-box {{ width: 10px; height: 8px; background-color: #e2e8f0; border: 1px solid #cbd5e1; }}
            .blue-line {{ width: 12px; height: 2px; background-color: #1d4ed8; }}

            /* Khối Nhận xét */
            .feedback-box {{
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 8px;
            }}
            .level-badge {{
                font-size: 11px;
                font-weight: bold;
                color: #b45309;
                margin-bottom: 4px;
            }}
            .section-label {{
                font-size: 9px;
                font-weight: bold;
                text-transform: uppercase;
                color: #4c669a;
                margin-top: 4px;
            }}
            .section-content {{
                font-size: 10px;
                color: #1e293b;
                line-height: 1.35;
            }}
            .divider {{
                border: 0;
                border-top: 1px dashed #cbd5e1;
                margin: 6px 0;
            }}

            /* Footer */
            .footer-box {{
                margin-top: 15px;
                border-top: 1px solid #e2e8f0;
                padding-top: 6px;
                text-align: center;
                font-size: 8px;
                color: #64748b;
            }}
        </style>
    </head>
    <body>
        <table class="brand-header-table">
            <tr>
                <td class="brand-logo-td">
                    <!-- Thay thế thẻ text bằng thẻ <img> chứa Logo -->
                    <img src="{logo_url}" class="logo-img" alt="Logo" />
                </td>
                <td class="brand-slogan-td">
                    <div class="brand-slogan">"Kết nối thấu hiểu - Đồng hành cùng con"</div>
                </td>
            </tr>
        </table>

        <div class="header">
            <h2>KẾT QUẢ KHẢO SÁT TÂM LÝ</h2>
            <div class="subtitle">Khảo sát xu hướng thu mình và mức độ kết nối xã hội ở học sinh THCS - THPT</div>
        </div>

        <div class="total-card">
            <div class="total-label">Tổng điểm toàn bài</div>
            <div class="total-val">{total_score} <span style="font-size: 12px; color: #4c669a;">điểm</span></div>
        </div>

        <!-- NHÓM 1: ALL_ABC (THU MÌNH) -->
        <div class="group-card">
            <div class="group-title">1. Phân mức: Nhóm A + B + C (Xu hướng thu mình)</div>
            <div class="group-score">Điểm của bạn: <strong style="color: #1152d4;">{abc_score} điểm</strong></div>

            {chart_abc_html}

            <div class="feedback-box">
                <div class="level-badge">► Mức độ: {abc_level}</div>
                <div class="section-label">Nhận xét chi tiết:</div>
                <div class="section-content">{abc_comment_html}</div>
                {f"<div class='divider'></div><div class='section-label'>Lời khuyên:</div><div class='section-content'>{abc_recommendation_html}</div>" if abc_recommendation_html else ""}
            </div>
        </div>

        <!-- NHÓM 2: ALL_D (KẾT NỐI XÃ HỘI) -->
        <div class="group-card">
            <div class="group-title">2. Phân mức: Nhóm D (Mức độ kết nối xã hội)</div>
            <div class="group-score">Điểm của bạn: <strong style="color: #059669;">{d_score} điểm</strong></div>

            {chart_d_html}

            <div class="feedback-box">
                <div class="level-badge">► Mức độ: {d_level}</div>
                <div class="section-label">Nhận xét chi tiết:</div>
                <div class="section-content">{d_comment_html}</div>
                {f"<div class='divider'></div><div class='section-label'>Lời khuyên:</div><div class='section-content'>{d_recommendation_html}</div>" if d_recommendation_html else ""}
            </div>
        </div>

        <!-- Footer -->
        <div class="footer-box">
            Báo cáo được khởi tạo tự động bởi Hệ thống Đánh giá Tâm lý Reconnect 360° • Mọi thắc mắc vui lòng liên hệ hotline hỗ trợ.
        </div>
    </body>
    </html>
    """

    try:
        pdf_bytes = HTML(string=html_template).write_pdf()

        subject = "Báo cáo kết quả khảo sát chi tiết - Reconnect 360°"
        body = "Chào bạn,\n\nĐính kèm email này là Báo cáo PDF phân tích chi tiết kết quả khảo sát của bạn.\n\nTrân trọng,\nĐội ngũ Reconnect 360°"

        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', 'noreply@reconnect360.com')

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=from_email,
            to=[user_email],
        )

        email.attach('Bao-cao-khao-sat-Reconnect360.pdf', pdf_bytes, 'application/pdf')
        email.send(fail_silently=False)
        print(f"[SUCCESS] Gửi email thành công tới: {user_email}")

    except Exception as e:
        import traceback
        print(f"[ERROR] Lỗi xuất PDF hoặc gửi mail:\n{traceback.format_exc()}")