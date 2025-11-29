# ---- START of app.py (replace your current file with exactly this) ----
from flask import Flask, request, jsonify, send_from_directory, render_template
from PIL import Image
import imagehash, os, uuid, sqlite3, json
from datetime import datetime

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
DB_PATH = os.path.join(os.path.dirname(__file__), 'images.db')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder='static', template_folder='templates')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS images (
        uid TEXT PRIMARY KEY, phash TEXT, filename TEXT, mac TEXT, ip TEXT, origin TEXT, ts TEXT, deleted INTEGER DEFAULT 0
    )''')
    conn.commit()
    conn.close()

init_db()

def compute_phash(path):
    try:
        img = Image.open(path).convert('RGB')
        return str(imagehash.phash(img))
    except Exception:
        return ''

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/images', methods=['GET'])
def images():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT uid, phash, filename, mac, ip, origin, ts, deleted FROM images')
    rows = c.fetchall()
    conn.close()
    imgs = []
    for r in rows:
        imgs.append({
            'uid': r[0], 'phash': r[1], 'filename': r[2], 'mac': r[3], 'ip': r[4], 'origin': r[5], 'ts': r[6], 'deleted': bool(r[7])
        })
    return jsonify({'images': imgs})

@app.route('/api/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error':'file required'}), 400
    f = request.files['file']
    mac = request.form.get('mac','')
    ip = request.form.get('ip','')
    origin = request.form.get('origin','original')
    fname = f.filename or (f"upload_{uuid.uuid4().hex}.jpg")
    save_path = os.path.join(UPLOAD_FOLDER, fname)
    f.save(save_path)
    phash = compute_phash(save_path)
    uid = uuid.uuid4().hex
    ts = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO images (uid, phash, filename, mac, ip, origin, ts) VALUES (?, ?, ?, ?, ?, ?, ?)',
              (uid, phash, fname, mac, ip, origin, ts))
    conn.commit()
    conn.close()
    return jsonify({'uid':uid, 'phash':phash, 'filename':fname})

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/delete/<uid>', methods=['POST'])
def delete(uid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE images SET deleted=1 WHERE uid=?', (uid,))
    conn.commit()
    conn.close()
    return jsonify({'status':'deleted'})

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
# ---- END of app.py ----
