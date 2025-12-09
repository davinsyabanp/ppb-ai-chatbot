from flask import Flask, request, render_template, jsonify, redirect, flash
from app.core import get_response, get_system_info, get_embedding_progress, get_file_status, split_documents_by_type
import os
from dotenv import load_dotenv, find_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from app.models import db, AdminUser, KnowledgeBaseFile
import click
from werkzeug.utils import secure_filename
import hashlib
from langchain_community.document_loaders import PyMuPDFLoader
from app.langchain_compat import Document
import pandas as pd
import io

load_dotenv()
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'devsecretkey')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'documents'
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32 MB

db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'admin_login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(AdminUser, int(user_id))

# Ensure templates directory exists for Flask
if not os.path.exists('templates'):
    os.makedirs('templates')

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

ALLOWED_EXTENSIONS = {'pdf', 'txt', 'csv'}

# Helper to check allowed file
def allowed_file(filename):
    return (
        '.' in filename
        and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    )


@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for monitoring.
    """
    return {
        "status": "healthy",
        "message": "RAG chatbot AI is running",
        "language": "Indonesian"
    }

@app.route('/', methods=['GET'])
def home():
    """
    Home endpoint with basic information.
    """
    return """
    <h1>🎓 Virtual Assistant Pusat Pengembangan Bahasa UIN Jakarta</h1>
    <p>Ini adalah chatbot AI Virtual Assistant untuk Pusat Pengembangan Bahasa UIN Syarif Hidayatullah Jakarta.</p>
    <p>Chatbot AI ini dapat menjawab pertanyaan dalam Bahasa Indonesia berdasarkan dokumen yang tersedia.</p>
    
    <h3>Akses:</h3>
    <ul>
        <li><a href="/chat">💬 Web Chat Interface</a></li>
        <li><code>/api/health</code> (health check)</li>
    </ul>
    
    <p><strong>Status:</strong> <span style="color: green;">🟢 Online</span></p>
    """

@app.route('/test', methods=['GET'])
def test_endpoint():
    """
    Test endpoint to verify the system is working.
    """
    try:
        system_info = get_system_info()
        return {
            "status": "success",
            "message": "Sistem berfungsi dengan baik",
            "system_info": system_info,
            "language": "Indonesian"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error: {str(e)}",
            "language": "Indonesian"
        }

@app.route('/chat', methods=['GET', 'POST'])
def web_chat():
    """
    Web chat endpoint: GET renders chat UI, POST handles AJAX chat.
    """
    if request.method == 'GET':
        return render_template('chat.html')
    if request.method == 'POST':
        data = request.get_json()
        user_message = data.get('message', '').strip()
        user_id = request.remote_addr  # Use IP as session/user id for demo
        if not user_message:
            return jsonify({'response': 'Silakan masukkan pesan.'})
        ai_response = get_response(user_message, user_id)
        return jsonify({'response': ai_response})

@app.cli.command('init-db')
@click.option('--username', prompt=True, help='Admin username')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Admin password')
def init_db(username, password):
    """Initialize the database and create an admin user."""
    with app.app_context():
        db.create_all()
        if AdminUser.query.filter_by(username=username).first():
            print('Admin user already exists.')
            return
        admin = AdminUser(username=username)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f'Admin user {username} created.')

# Admin login
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = AdminUser.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect('/admin')
        else:
            return render_template('admin_login.html', error='Invalid credentials')
    return render_template('admin_login.html')

# Admin logout
@app.route('/api/admin/logout', methods=['GET', 'POST'])
@login_required
def admin_logout():
    logout_user()
    return redirect('/admin/login')

# Admin dashboard
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    files = get_file_status()
    if request.method == 'POST':
        print('POST data:', request.form)
        print('FILES:', request.files)
        # Handle file upload
        if 'file' not in request.files:
            print('No file part in request.files')
            return render_template(
                'admin_dashboard.html',
                user=current_user,
                files=files,
                error='No file part'
            )
        file = request.files['file']
        if file.filename == '':
            print('No selected file')
            return render_template(
                'admin_dashboard.html',
                user=current_user,
                files=files,
                error='No selected file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            # Calculate file hash (re-open file after saving)
            with open(filepath, 'rb') as f:
                filehash = hashlib.sha256(f.read()).hexdigest()
            filetype = filename.rsplit('.', 1)[1].lower()
            # Check if file already exists (by hash)
            existing = KnowledgeBaseFile.query.filter_by(filehash=filehash).first()
            if existing:
                print('File already exists')
                return render_template(
                    'admin_dashboard.html',
                    user=current_user,
                    files=files,
                    error='File already exists')
            # Get chunking params from form
            chunk_size = int(request.form.get('chunk_size', 2000))
            chunk_overlap = int(request.form.get('chunk_overlap', 400))
            # Optionally: store these in the DB or pass to embedding logic
            kb_file = KnowledgeBaseFile(
                filename=filename,
                filetype=filetype,
                filepath=filepath,
                filehash=filehash
            )
            db.session.add(kb_file)
            db.session.commit()
            print(f'File uploaded successfully with chunk_size={chunk_size}, chunk_overlap={chunk_overlap}')
            files = get_file_status()
            return render_template(
                'admin_dashboard.html',
                user=current_user,
                files=files,
                message='File uploaded!'
            )
        else:
            print('Invalid file type')
            return render_template(
                'admin_dashboard.html',
                user=current_user,
                files=files,
                error='Invalid file type'
            )
    # GET: show dashboard
    return render_template('admin_dashboard.html', user=current_user, files=files)

# Delete file
@app.route('/api/admin/delete/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    kb_file = db.session.get(KnowledgeBaseFile, file_id)
    if not kb_file:
        if request.headers.get("Content-Type") == "application/json":
            return (
                jsonify(
                    {"success": False, "error": "File not found or already deleted."}
                ),
                404,
            )
        flash("File not found or already deleted.", "warning")
        return redirect("/admin")

    try:
        if os.path.exists(kb_file.filepath):
            os.remove(kb_file.filepath)
    except Exception:
        pass

    db.session.delete(kb_file)
    db.session.commit()

    # After deleting, check if there are any files left
    if KnowledgeBaseFile.query.count() == 0:
        import shutil

        vector_db_path = os.path.join("vector_db", "faiss_index")
        if os.path.exists(vector_db_path):
            shutil.rmtree(vector_db_path)

    if request.headers.get("Content-Type") == "application/json":
        return jsonify({"success": True, "message": "File deleted successfully!"})

    flash("File deleted!", "success")
    return redirect("/admin")

# Placeholder for embedding and progress
@app.route('/api/admin/embed', methods=['POST'])
@login_required
def embed_files():
    from app.core import start_embedding
    started = start_embedding(app, force_all=False)
    if started:
        msg = 'Embedding started for changed files! Progress will update below.'
    else:
        msg = 'Embedding is already running.'
    files = get_file_status()
    return render_template(
        'admin_dashboard.html',
        user=current_user,
        files=files,
        message=msg
    )

@app.route('/api/admin/embed_all', methods=['POST'])
@login_required
def embed_all_files():
    from app.core import start_embedding
    started = start_embedding(app, force_all=True)
    if started:
        msg = 'Embedding started for all files! Progress will update below.'
    else:
        msg = 'Embedding is already running.'
    files = get_file_status()
    return render_template(
        'admin_dashboard.html',
        user=current_user,
        files=files,
        message=msg
    )

@app.route('/api/admin/embed_progress')
@login_required
def embed_progress():
    return jsonify(get_embedding_progress())

@app.route('/api/chat', methods=['POST'])
def api_chat():
    data = request.get_json()
    message = data.get('message', '').strip()
    user_id = data.get('user_id', request.remote_addr)
    conversation_has_started = data.get("conversationHasStarted", False)
    is_initial_greeting_sent = data.get("isInitialGreetingSent", False)

    if not message:
        return jsonify({'error': 'No message provided'}), 400

    response = get_response(
        message,
        user_id,
        conversation_has_started,
        is_initial_greeting_sent
    )
    return jsonify({'response': response})

@app.route('/api/files', methods=['GET'])
def api_files():
    files = get_file_status()
    file_list = [
        {
            "id": f["id"],
            "filename": f["filename"],
            "filetype": f["filetype"],
            "uploaded_at": f["uploaded_at"],
            "changed": f["changed"],
        }
        for f in files
    ]
    return jsonify({'files': file_list})

@app.route('/api/preview-chunking', methods=['POST'])
def preview_chunking():
    print('[PREVIEW] Endpoint called')
    print(f'[PREVIEW] Request method: {request.method}')
    print(f'[PREVIEW] Request files: {list(request.files.keys())}')
    print(f'[PREVIEW] Request form: {list(request.form.keys())}')
    
    file = request.files.get('file')
    if file:
        print(f'[PREVIEW] File received: {file.filename}, size: {len(file.read())} bytes')
        file.seek(0)  # Reset file pointer after reading
    else:
        print('[PREVIEW] No file in request.files')
        return jsonify(
            {
                'success': False,
                'error': 'No file uploaded'
            }
        ), 400
    
    chunk_size = int(request.form.get('chunk_size', 1000))
    chunk_overlap = int(request.form.get('chunk_overlap', 200))
    print(f"[PREVIEW] Received file: {file.filename if file else None}, chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
    
    filename = file.filename
    if not filename:
        return jsonify(
            {
                "success": False,
                "error": "Uploaded file has no name."
            }
        ), 400
    filetype = filename.rsplit('.', 1)[-1].lower()
    print(f'[PREVIEW] File type detected: {filetype}')
    preview_docs = []
    
    try:
        if filetype == 'pdf':
            import tempfile
            try:
                print('[PREVIEW] Processing PDF file...')
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                    file.save(tmp)
                    tmp_path = tmp.name
                    print(f'[PREVIEW] PDF saved to temp file: {tmp_path}')
                
                loader = PyMuPDFLoader(tmp_path)
                docs = loader.load()
                print(f"[PREVIEW] PDF: loaded {len(docs)} pages")
                
                # Collect up to 3 pages with extractable text from the first 10 pages
                preview_docs = []
                for i, d in enumerate(docs[:10]):
                    d.metadata['file_type'] = 'pdf'
                    text_len = len(d.page_content.strip()) if d.page_content else 0
                    print(f"[PREVIEW] Page {i+1}: text length = {text_len}")
                    if d.page_content and d.page_content.strip():
                        preview_docs.append(d)
                    if len(preview_docs) >= 3:
                        break
                print(f"[PREVIEW] Using {len(preview_docs)} non-empty pages for preview")
                
                # Clean up temp file
                import os
                try:
                    os.unlink(tmp_path)
                except:
                    pass
                    
            except Exception as e:
                print(f"[PREVIEW] Exception during PDF processing: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({'success': False, 'error': f'Failed to process the PDF file: {str(e)}'}), 400
        elif filetype == 'csv':
            try:
                print('[PREVIEW] Processing CSV file...')
                df = pd.read_csv(file, nrows=100)
                for index, row in df.iterrows():
                    row_text = ""
                    for column, value in row.items():
                        if pd.notna(value):
                            row_text += f"{column}: {value}\n"
                    if row_text.strip():
                        metadata = {"source": filename, "row": index + 1, "file_type": "csv"}
                        preview_docs.append(Document(page_content=row_text.strip(), metadata=metadata))
                print(f"[PREVIEW] CSV: loaded {len(df)} rows, preview_docs={len(preview_docs)}")
            except Exception as e:
                print(f"[PREVIEW] Exception during CSV processing: {e}")
                return jsonify({'success': False, 'error': 'Failed to process the CSV file. It may be corrupt or unreadable.'}), 400
        elif filetype == 'txt':
            try:
                print('[PREVIEW] Processing TXT file...')
                text = file.read(5000).decode('utf-8', errors='ignore')
                preview_docs = [Document(page_content=text, metadata={"source": filename, "file_type": "txt"})]
                print(f"[PREVIEW] TXT: loaded {len(text)} chars")
            except Exception as e:
                print(f"[PREVIEW] Exception during TXT processing: {e}")
                return jsonify({'success': False, 'error': 'Failed to process the TXT file. It may be corrupt or unreadable.'}), 400
        else:
            print(f"[PREVIEW] Unsupported file type: {filetype}")
            return jsonify({'success': False, 'error': 'Unsupported file type'}), 400
            
        if not preview_docs:
            print('[PREVIEW] No extractable text found in the first 10 pages of the PDF.')
            return jsonify({'success': False, 'error': 'No extractable text found in the first 10 pages of the PDF. The file may be scanned images or empty.'}), 200
            
        print(f'[PREVIEW] About to call split_documents_by_type with {len(preview_docs)} docs')
        chunks = split_documents_by_type(preview_docs, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        print(f"[PREVIEW] Chunks generated: {len(chunks)}")
        
        if not chunks:
            print('[PREVIEW] No chunks could be generated from the file preview.')
            return jsonify({'success': False, 'error': 'No chunks could be generated from the file preview. The file may be empty or not contain extractable text.'}), 200
            
        preview_chunks = []
        for i, chunk in enumerate(chunks[:10]):
            preview_chunks.append({
                'chunk_number': i+1,
                'content': chunk.page_content
            })
        print(f'[PREVIEW] Returning {len(preview_chunks)} preview chunks')
        return jsonify({'success': True, 'preview_chunks': preview_chunks})
        
    except Exception as e:
        print(f"[PREVIEW] Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'An unexpected error occurred during preview: {str(e)}'}), 500

@app.route("/api/kb_status", methods=["GET"])
def kb_status():
    """
    Check if knowledge base needs embedding.
    Returns 'requires_embedding' if:
    - No embedding has been done at all, OR
    - There are files uploaded after the last embedding
    Returns 'active' if all files have been embedded and no new files since.
    """
    index_path = os.path.join("vector_db", "faiss_index")
    
    # Check if any files exist
    files = KnowledgeBaseFile.query.all()
    if not files:
        # No files at all - nothing to embed
        return jsonify({"status": "no_files"})
    
    # Check if index exists
    if not os.path.exists(index_path):
        # Files exist but no index - needs embedding
        return jsonify({"status": "requires_embedding"})
    
    # Check if all files have been embedded
    # If ANY file has embedded_at as None, it needs embedding
    from sqlalchemy import func
    unembed_files = KnowledgeBaseFile.query.filter(KnowledgeBaseFile.embedded_at == None).all()
    if unembed_files:
        return jsonify({"status": "requires_embedding"})
    
    # Check if any files were uploaded after the last embedding
    max_embedded_time = db.session.query(func.max(KnowledgeBaseFile.embedded_at)).scalar()
    max_uploaded_time = db.session.query(func.max(KnowledgeBaseFile.uploaded_at)).scalar()
    
    if max_embedded_time and max_uploaded_time and max_uploaded_time > max_embedded_time:
        # New files uploaded after last embedding
        return jsonify({"status": "requires_embedding"})
    
    # If we reach here, KB is already active/embedded with all files up to date
    return jsonify({"status": "active"})

@app.route("/api/admin/delete_vector_db", methods=["POST"])
@login_required
def delete_vector_db():
    import shutil
    vector_db_dir = os.path.abspath("vector_db")
    try:
        if os.path.exists(vector_db_dir):
            # Remove all contents inside vector_db
            for filename in os.listdir(vector_db_dir):
                file_path = os.path.join(vector_db_dir, filename)
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
        else:
            os.makedirs(vector_db_dir, exist_ok=True)
        msg = "Vector DB deleted successfully."
    except Exception as e:
        msg = f"Failed to delete Vector DB: {str(e)}"
    files = get_file_status()
    return render_template("admin_dashboard.html", user=current_user, files=files, message=msg)

if __name__ == "__main__":
    # Get port from environment or default to 5000
    port = int(os.environ.get("PORT", 5000))
    
    print(f"🚀 Starting Virtual Assistant Pusat Pengembangan Bahasa UIN Jakarta on port {port}")
    print("🇮🇩 Language: Indonesian")
    print("🎓 Service: Information & Support")
    print("\nMake sure to:")
    print("1. Set up your environment variables in .env file")
    print("2. Run ingest.py to create the vector store")
    print("3. Configure your Twilio webhook URL to point to this server")
    print("4. Test with /info or /help commands")
    print("5. Access web chat at: http://localhost:" + str(port) + "/chat")
    
    app.run(host="0.0.0.0", port=port, debug=True) 