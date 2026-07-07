import os
import base64
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload-post', methods=['POST'])
def upload_post():
    token = request.form.get('token')
    gemini_key = request.form.get('gemini_key')
    uploaded_files = request.files.getlist('file')
    
    if not uploaded_files or not token or not gemini_key:
        return jsonify({"status": "Error", "message": "Missing fields"}), 400

    # ফেসবুক সার্ভার থেকে অটোমেটিক পেজ আইডি (Page ID) বের করা
    try:
        acc_url = f"https://facebook.com{token.strip()}"
        res = requests.get(acc_url).json()
        actual_page_id = res["data"][0]["id"]
    except Exception:
        return "<h1>Error: আপনার পেজ টোকেনটি সঠিক নয় অথবা পেজ আইডি খুঁজে পাওয়া যায়নি।</h1>"
        
    # ছবিগুলোকে বেস৬৪ ফরম্যাটে কনভার্ট করা
    parts = []
    for file in uploaded_files:
        if file.filename != '':
            parts.append({
                "inline_data": {
                    "mime_type": file.mimetype,
                    "data": base64.b64encode(file.read()).decode('utf-8')
                }
            })
            
    parts.append({"text": "Analyze these product images and create an engaging, highly professional promotional Facebook post in Bengali. Include relevant hashtags."})

    try:
        # সরাসরি গুগলের অফিশিয়াল v1 ইউআরএল (কোনো টাইপো বা ওল্ড লাইব্রেরির এরর আসবে না)
        g_url = f"https://googleapis.com{gemini_key.strip()}"
        g_res = requests.post(g_url, json={"contents": [{"parts": parts}]}).json()
        caption = g_res['candidates'][0]['content']['parts'][0]['text']
        
        # ফেসবুকে অটো-পোস্ট পাঠানো
        fb_url = f"https://facebook.com{actual_page_id}/photos"
        
        first_file = uploaded_files[0]
        first_file.seek(0)
        files = {'source': (first_file.filename, first_file.read(), first_file.mimetype)}
        
        fb_res = requests.post(fb_url, data={'caption': caption, 'access_token': token.strip()}, files=files).json()
        
        if "id" in fb_res:
            return f"<h1>Success! Post Published Successfully on your Facebook Page.</h1><p>Page ID: {actual_page_id}</p><p>Post ID: {fb_res['id']}</p><br><a href='/'>Back to Dashboard</a>"
        else:
            return jsonify({"status": "Facebook Error", "message": fb_res}), 400
            
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
