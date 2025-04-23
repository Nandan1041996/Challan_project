from flask import Flask, render_template, request, jsonify
import os
import json
from datetime import datetime
# import PyPDF2
from pypdf import PdfReader
import re
import ast 
from werkzeug.utils import secure_filename
import smtplib

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
print('base:',BASE_DIR)
UPLOAD_FOLDER = 'uploads/'
 # Use the 'uploads' folder in the current directory
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    
    
@app.route('/', methods=['GET', 'POST'])
def index():
    extracted_text = ""
    error_message = None
    
    if request.method == 'POST':
        file = request.files['pdf_file']
        print(file)
        if file.filename.endswith('.pdf'):
            filename = file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            print('file_path:',file_path)
            # Read all pages from PDF
            reader = PdfReader(file_path)
            text_chunks = []
            all_text = ""
            
            for page in reader.pages:
                text = page.extract_text(extraction_mode="layout")
                if text:
                    all_text += text
            
            # Validate truck numbers
            matches = re.findall(r"\bGJ\d{2}\D{1,3}\s?\d{4}\b", all_text)

            if len(matches) != 0 and (len(matches[0]) == 10 or len(matches[0]) == 9):
                # Process lines
                for page in reader.pages:
                    text = page.extract_text(extraction_mode="layout")
                    
                    if text:
                        # Process lines
                        lines = text.split('\n')
                        for line in lines:
                            processed_line = ""
                            
                            # Split by spaces and process each chunk
                            chunks = re.split(r'(\s{5,})', line)
                            for chunk in chunks:
                                # If chunk is just spaces, keep them as is
                                if re.match(r'^\s+$', chunk):
                                    processed_line += chunk
                                # Otherwise make it a link
                                elif chunk.strip():
                                    processed_line += f'<a href="javascript:void(0);" onclick="copyToClipboard(this.textContent)">{chunk}</a>'
                            
                            text_chunks.append(processed_line + '<br>')
                
                extracted_text = ''.join(text_chunks)
            else:
                error_message = "Invalid Truck Number"
            
        
        else:
            error_message = "Please upload a valid PDF file."
    
    return render_template('index.html', extracted_text=extracted_text, error_message=error_message)
    
    
# @app.route('/', methods=['GET', 'POST'])
# def index():
    
#     extracted_text = ""
    
#     if request.method == 'POST':
#         file = request.files.get('pdf_file')
        
#         if file and file.filename.endswith('.pdf'):
#             filename = secure_filename(file.filename)
#             filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#             file.save(filepath)
        
#             # Read all pages from PDF
#             reader = PdfReader(filepath)
#             text_chunks = []
#             all_text = ""
            
#             for page in reader.pages:
#                 text = page.extract_text(extraction_mode="layout")
#                 if text:
#                     all_text += text
            
#             # Validate truck numbers
#             matches = re.findall(r"\bGJ\d{2}\D{1,3}\s?\d{4}\b", all_text)

#             if len(matches)!=0:
#                 print(matches)
#                 if len(matches[0]) == 10 or len(matches[0]) ==9:
#                     # Process lines
#                     for page in reader.pages:
#                         text = page.extract_text(extraction_mode="layout")
                        
#                         if text:
#                             # Process lines
#                             lines = text.split('\n')
#                             for line in lines:
#                                 processed_line = ""
                                
#                                 # Split by spaces and process each chunk
#                                 chunks = re.split(r'(\s{5,})', line)
#                                 for chunk in chunks:
#                                     # If chunk is just spaces, keep them as is
#                                     if re.match(r'^\s+$', chunk):
#                                         processed_line += chunk
#                                     # Otherwise make it a link
#                                     elif chunk.strip():
#                                         processed_line += f'<a href="javascript:void(0);" onclick="copyToClipboard(this.textContent)">{chunk}</a>'
                                
#                                 text_chunks.append(processed_line + '<br>')
                    
#                     extracted_text = ''.join(text_chunks)
#             else:
#                 extracted_text = "Invalid Truck Number"
            
#             os.remove(filepath)  # Clean up after use
        
#         else:
#             extracted_text = "Please upload a valid PDF file."
            
    
#     return render_template('index.html', extracted_text=extracted_text)
    
    

# @app.route('/save_template', methods=['POST'])
# def save_template():
#     try:
#         data = request.json
        
#         # Create templates directory if it doesn't exist
#         if not os.path.exists("templates"):
#             os.makedirs("templates")
        
#         # Use the original filename from the request
#         original_filename = data.get('original_filename', 'template')
        
#         # Remove file extension if present
#         original_filename = os.path.splitext(original_filename)[0]
        
#         # Generate filename based on original filename and timestamp
#         timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
#         filename = f"{original_filename}_{timestamp}.json"
#         filepath = os.path.join("templates", filename)
        
#         # Save the template data to a file
#         with open(filepath, 'w') as f:
#             json.dump(data, f, indent=4)
        
#         return jsonify({
#             "success": True,
#             "filename": filename
#         })
    
#     except Exception as e:
#         return jsonify({
#             "success": False,
#             "error": str(e)
#         })

import gc

@app.route('/save_template', methods=['POST'])
def save_template():
    try:
        
        raw_data = request.json
   
        
        if not os.path.exists("templates"):
            os.makedirs("templates")
        
        original_filename = os.listdir(app.config['UPLOAD_FOLDER'])[0]
        # original_filename = os.path.splitext(original_filename)[0]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{original_filename}_{timestamp}.json"
        filepath = os.path.join("templates", filename)
        
        # Parse the CSV-like string into a dictionary
        csv_data_str = "{" + raw_data.get('csvData', '') + "}"
        try:
            fields_dict = ast.literal_eval(csv_data_str)
        except Exception as parse_error:
            return jsonify({
                "success": False,
                "error": f"CSV parse error: {str(parse_error)}"
            })
            
        for file_name in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
                    
        structured_data = {
            "template_name": original_filename,
            "created_at": raw_data.get("date", datetime.now().isoformat()),
            "fields": fields_dict
        }

        send_mail('mahendrayadav@ghcl.co.in',json.dumps(structured_data, indent=4))
        
        with open(filepath, 'w') as f:
            json.dump(structured_data, f, indent=4)
            
        
        
        return jsonify({
            "success": True,
            "filename": filename
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


def send_mail(receiver_email_id,message):
    try:
        sender_email_id = 'mayurnandanwar@ghcl.co.in'
        password = 'uvhr zbmk yeal ujhv'
        # creates SMTP session
        s = smtplib.SMTP('smtp.gmail.com', 587)
        # start TLS for security
        s.starttls()
        # Authentication
        s.login(sender_email_id, password)
        # message to be sent
        # sending the mail
        s.sendmail(sender_email_id, receiver_email_id, message)
        # terminating the session
        s.quit()

        del sender_email_id,password
        gc.collect()
        return 0
    except:
        return jsonify({'error':'The Message cannot be Sent.'})
    
if __name__ == '__main__':
    app.run(debug=True)
    
    
