from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from PIL import Image
import pytesseract
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@127.0.0.1/qube_task?charset=utf8mb4&collation=utf8mb4_general_ci'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class OCRData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    registration_number = db.Column(db.String(255), nullable=False)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
   
    file = request.files['file']
   
    if file.filename == '':
        return redirect(request.url)

    if file and allowed_file(file.filename):
        # Create the 'uploads' directory if it doesn't exist
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        # Secure the filename to prevent any potential security issues
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
       
        # Perform OCR using pytesseract
        image = Image.open(filepath)
        
        # Print intermediate result for debugging
        print("OCR Result (English):")
        print(pytesseract.image_to_string(image, lang='eng'))
        
        # Perform OCR with specified configuration
        registration_number = pytesseract.image_to_string(image, lang='eng', config='--psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        
        # Print OCR result for further debugging
        print("Extracted Registration Number:")
        print(registration_number)

        new_data = OCRData(filename=filename, registration_number=registration_number)
        db.session.add(new_data)
        db.session.commit()

        return render_template('result.html', filename=filename, registration_number=registration_number)

@app.route('/list_ocr')
def list_ocr_data():
    # Fetch all OCRData entries from the database
    ocr_data = OCRData.query.order_by(OCRData.id.desc()).all()
    
    return render_template('list_ocr.html', ocr_data=ocr_data, index=1  )

if __name__ == '__main__':
    app.run(debug=True)
