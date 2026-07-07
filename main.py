import os
import json
import base64
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload-post', methods=['POST'])
def upload_post():
    page_id_input = request.form.get('page_id')
    token = request.form.get('token')
    gemini_key = request.form.get('gemini_key')
    uploaded_files = request.files.getlist('file')
    
    if not uploaded_files or not token or not gemini_key:
        return jsonify({"status": "Error", "message": "Missing fields"}), 400

    # অটোমেটিক ফেসবুক সার্ভার থেকে পেজ আইডি (Page ID) খুঁজে বের করার ট্রিক
    actual_page_id = None
    try:
        accounts_url = f"https://facebook.com{token.strip()}"
        accounts_res = requests.get(accounts_url).json()
        if "data" in accounts_res and len(accounts_res["data"]) > 0:
            # প্রথম যে পেজটি টোকেনের সাথে কানেক্টেড, সেটির আইডি অটো সিলেক্ট হবে
            actual_page_id = accounts_res["data"][0]["id"]
        elif page_id_input:
            actual_page_id = page_id_input.strip()
    except Exception:
        if page_id_input:
            actual_page_id = page_id_input.strip()

    if not actual_page_id:
        return "<h1>Error: আপনার পেজ আইডিটি ফেসবুক সার্ভার থেকে খুঁজে পাওয়া যায়নি। দয়া করে সঠিক টোকেন ব্যবহার করুন।</h1>"
        
    contents_parts = []
    for file in uploaded_files:
        if file.filename != '':
            file_bytes = file.read()
            base64_data = base64.b64encode(file_bytes).decode('utf-8')
            contents_parts.append({
                "inline_data": {
                    "mime_type": file.mimetype,
                    "data": base64_data
                }
            })
            
    if not contents_parts:
        return jsonify({"status": "Error", "message": "No valid images uploaded"}), 400

    contents_parts.append({
        "text": "Analyze these product images and create an engaging, highly professional promotional Facebook post in Bengali. Include relevant hashtags."
    })

    try:
        gemini_url = f"https://googleapis.com{gemini_key.strip()}"
        headers = {'Content-Type': 'application/json'}
        payload = {"contents": [{"parts": contents_parts}]}
        
        gemini_response = requests.post(gemini_url, headers=headers, json=payload)
        gemini_res_data = gemini_response.json()
        
        if 'candidates' in gemini_res_data and len(gemini_res_data['candidates']) > 0:
            caption = gemini_res_data['candidates']['content']['parts']['text']
        else:
            return jsonify({"status": "Gemini API Error", "message": gemini_res_data}), 400
        
        # স্বয়ংক্রিয়ভাবে খুঁজে পাওয়া পেজ আইডি দিয়ে ফেসবুকে পোস্ট পাঠানো হচ্ছে
        fb_url = f"

{actual_page_id}/photos"
        fb_payload = {
            'caption': caption,
            'access_token': token
        }
        
        first_file = uploaded_files
        first_file.seek(0)
        files = {
            'source': (first_file.filename, first_file.read(), first_file.mimetype)
        }
        
        fb_response = requests.post(fb_url, data=fb_payload, files=files)
        fb_res_data = fb_response.json()
        
        if "id" in fb_res_data:
            return f"<h1>Success! Post Published Successfully on your Facebook Page.</h1><p>Facebook Page ID Used: {actual_page_id}</p><p>Post ID: {fb_res_data['id']}</p><br><a href='/'>Back to Dashboard</a>"
        else:
            return jsonify({"status": "Facebook Error", "message": fb_res_data}), 400
            
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
