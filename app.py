from flask import Flask, request, render_template, redirect, url_for, session, send_from_directory
import openai
import os
from PIL import Image
import pytesseract
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
# Initialize the Flask application
app = Flask(__name__)
app.secret_key = '123'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
openai.api_key = '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'
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'conversation' not in session:
        session['conversation'] = [
            {"role": "system", "content": "I'm ChatDOC, a Document Question Answering assistant focuses on visually understanding the information on a document image in order to perform Visual Question Answering task. Please upload a document image to start a conversation."}
        ]
    if 'conversation_m' not in session:
        session['conversation_m'] = session['conversation'].copy()
    if 'image' not in session:
        session['image'] = None
    if request.method == 'POST':
        user_message = request.form.get('message')
        if user_message:
            # Continue the conversation with the new message
            conversation = session.get('conversation', [])
            conversation.append({"role": "user", "content": user_message})
            
            conversation_m = session.get('conversation_m', [])
            conversation_m.append({"role": "user", "content": user_message})
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=conversation
            )
            assistant_message = response.choices[0].message['content']
            conversation.append({"role": "assistant", "content": assistant_message})
            conversation_m.append({"role": "assistant", "content": assistant_message})
            session['conversation'] = conversation  # Save updated conversation back to session
            
        return redirect(url_for('index'))
    else:
        conversation_m = session.get('conversation_m', [])
        image=session['image']
        print(image)
        return render_template('index.html', conversation_m=conversation_m, image=image)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == ''or not allowed_file(file.filename):
        return redirect(request.url)
    if file:
        # Here you can add functionality to handle the uploaded file
        # For example, save it to a directory
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        img = Image.open("uploads/"+filename)
        text = pytesseract.image_to_string(img)
        # Add any processing you need here
        conversation = session.get('conversation', [])
        
        conversation_m=conversation.copy()
        conversation.append({"role": "user", "content": f"Based on the following text \"{text}\", I will ask you so questions."})
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation
        )
        assistant_message = response.choices[0].message['content']
        conversation.append({"role": "assistant", "content": assistant_message})
        session['conversation'] = conversation 
        conversation_m.append({"role": "assistant", "content": "File received! How may I help you?"})
        session['conversation_m'] = conversation_m
        session['image']="/uploads/"+file.filename
        return redirect(url_for('uploaded_file', filename=filename))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/restart', methods=['POST'])
def restart():
    # Clear the conversation in the session
    session['conversation'] = [
        {"role": "system", "content": "I'm ChatDOC, a Document Question Answering assistant focuses on visually understanding the information on a document image in order to perform Visual Question Answering task. Please upload a document image to start a conversation. "}
    ]
    session['conversation_m'] = [
        {"role": "system", "content": "I'm ChatDOC, a Document Question Answering assistant focuses on visually understanding the information on a document image in order to perform Visual Question Answering task. Please upload a document image to start a conversation."}
    ]
    session['image'] = None
    return redirect(url_for('index'))
if __name__ == '__main__':
    app.run(debug=True)
