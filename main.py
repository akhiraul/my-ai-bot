import os
import requests
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload-post', methods=['POST'])
def upload_post():
    page_id = request.form.get('page_id')
    token = request.form.get('token')
    gemini_key = request.form.get('gemini_key')
    uploaded_files = request.files.getlist('file')
    
    if not uploaded_files or not page_id or not token or not gemini_key:
        return jsonify({"status": "Error", "message": "Missing fields"}), 400
        
    try:
        # এখানে সরাসরি লেটেস্ট v1 এপিআই ভার্সনটি লক করে দেওয়া হলো
        client_options = {"api_version": "v1"}
        genai.configure(api_key=gemini_key, client_options=client_options)
        model = genai.GenerativeModel('gemini-pro')
    except Exception as e:
        return jsonify({"status": "Gemini Configuration Error", "message": str(e)}), 400
        
    images_data = []
    for file in uploaded_files:
        if file.filename != '':
            file_bytes = file.read()
            images_data.append({
                "mime_type": file.mimetype,
                "data": file_bytes
            })
            
    if not images_data:
        return jsonify({"status": "Error", "message": "No valid images uploaded"}), 400

    try:
        prompt = "Analyze these product images and create an engaging, highly professional promotional Facebook post in Bengali. Include relevant hashtags."
        content_parts = images_data + [prompt]
        response = model.generate_content(content_parts)
        caption = response.text
        
        fb_url = f"https://facebook.com{page_id}/photos"
        payload = {
            'caption': caption,
            'access_token': token
        }
        
        first_file = uploaded_files[0]
        first_file.seek(0)
        files = {
            'source': (first_file.filename, first_file.read(), first_file.mimetype)
        }
        
        fb_response = requests.post(fb_url, data=payload, files=files)
        fb_res_data = fb_response.json()
        
        if "id" in fb_res_data:
            return f"<h1>Success! Post Published Successfully on your Facebook Page.</h1><p>Post ID: {fb_res_data['id']}</p><br><a href='/'>Back to Dashboard</a>"
        else:
            return jsonify({"status": "Facebook Error", "message": fb_res_data}), 400
            
    except Exception as e:
        return jsonify({"status": "Error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
