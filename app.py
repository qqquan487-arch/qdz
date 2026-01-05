from flask import Flask, request, jsonify
import cloudscraper
import os

app = Flask(__name__)

# Khởi tạo CloudScraper với cấu hình giả lập Chrome trên Windows
# Việc tạo scraper ở đây giúp tái sử dụng session, xử lý nhanh hơn
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'mobile': False
    }
)

@app.route('/')
def home():
    return "Render Cloudflare Bypass Service is Running!"

@app.route('/shorten', methods=['GET', 'POST'])
def proxy_shorten():
    # 1. Lấy dữ liệu từ GAS
    token = request.args.get('token') or request.form.get('token')
    url = request.args.get('url') or request.form.get('url')

    if not token or not url:
        data = request.get_json(silent=True)
        if data:
            token = data.get('token')
            url = data.get('url')

    if not token or not url:
        return jsonify({"status": "error", "message": "Render: Thiếu token hoặc url"}), 400

    # 2. Cấu hình gọi sang 4MMO
    target_api = "https://4mmo.net/api"
    params = {
        "api": token,
        "url": url,
        "format": "json"
    }

    try:
        # --- THAY ĐỔI QUAN TRỌNG: DÙNG CLOUDSCRAPER ---
        # scraper.get sẽ tự động giải mã Cloudflare challenge nếu gặp phải
        response = scraper.get(target_api, params=params, timeout=20)
        
        # Kiểm tra nếu status code không phải 200 (ví dụ 403, 503 do vẫn bị chặn)
        if response.status_code != 200:
             return jsonify({
                "status": "error", 
                "message": f"Cloudflare Blocked or Server Error. Status: {response.status_code}"
            })

        # Cố gắng parse JSON
        try:
            json_data = response.json()
            return jsonify(json_data)
        except ValueError:
            # Trường hợp 4MMO trả về HTML lỗi thay vì JSON
            return jsonify({
                "status": "error", 
                "message": "Không nhận được JSON từ 4MMO (Có thể lỗi Server hoặc CAPTCHA quá khó)"
            })

    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"Render Error: {str(e)}"
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
