import os
import psutil
import time
import re
import uuid
import subprocess
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

ADMIN_USER = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASS = os.environ.get('ADMIN_PASS', 'admin123')

PUSH_DIR = '/etc/nginx/rtmp-push'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def is_safe_filename(filename):
    return bool(re.match(r'^[a-zA-Z0-9_\-\.]+\.conf$', filename))

def generate_filename():
    timestamp = int(datetime.utcnow().timestamp())
    unique_id = str(uuid.uuid4())[:8]
    return f"push_{timestamp}_{unique_id}.conf"

def reload_nginx():
    try:
        subprocess.run(
            ['docker', 'exec', 'rtmp-nginx', 'nginx', '-s', 'reload'],
            check=True,
            capture_output=True,
            text=True
        )
        app.logger.info("Nginx reloaded successfully")
    except Exception as e:
        app.logger.error(f"Failed to reload nginx: {e}")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USER and request.form['password'] == ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('index'))
        flash('Неверные учётные данные')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    files = []
    for fname in os.listdir(PUSH_DIR):
        if fname.endswith('.conf'):
            path = os.path.join(PUSH_DIR, fname)
            with open(path, 'r') as f:
                content = f.read().strip()
            match = re.search(r'push\s+(.+)', content)
            url = match.group(1) if match else content
            files.append({'name': fname, 'url': url})
    return render_template('index.html', files=files)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        url = request.form['url'].strip()
        if not url:
            flash('URL не может быть пустым')
            return redirect(url_for('add'))
        if not url.startswith('rtmp://'):
            flash('URL должен начинаться с rtmp://')
            return redirect(url_for('add'))
        filename = generate_filename()
        filepath = os.path.join(PUSH_DIR, filename)
        while os.path.exists(filepath):
            filename = generate_filename()
            filepath = os.path.join(PUSH_DIR, filename)
        with open(filepath, 'w', newline='\n') as f:
            f.write(f'push {url};')
        reload_nginx()
        flash('Push-адрес добавлен')
        return redirect(url_for('index'))
    return render_template('add.html')

@app.route('/edit/<filename>', methods=['GET', 'POST'])
@login_required
def edit(filename):
    if not is_safe_filename(filename):
        flash('Некорректное имя файла')
        return redirect(url_for('index'))
    filepath = os.path.join(PUSH_DIR, filename)
    if not os.path.exists(filepath):
        flash('Файл не найден')
        return redirect(url_for('index'))
    if request.method == 'POST':
        new_url = request.form['url'].strip()
        if not new_url.startswith('rtmp://'):
            flash('URL должен начинаться с rtmp://')
            return redirect(url_for('edit', filename=filename))
        with open(filepath, 'w', newline='\n') as f:
            f.write(f'push {new_url};')
        reload_nginx()
        flash('Push-адрес обновлён')
        return redirect(url_for('index'))
    with open(filepath, 'r') as f:
        content = f.read().strip()
    match = re.search(r'push\s+(.+)', content)
    current_url = match.group(1) if match else content
    return render_template('edit.html', filename=filename, url=current_url)

@app.route('/delete/<filename>')
@login_required
def delete(filename):
    if not is_safe_filename(filename):
        flash('Некорректное имя файла')
        return redirect(url_for('index'))
    filepath = os.path.join(PUSH_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        reload_nginx()
        flash('Файл удалён')
    else:
        flash('Файл не найден')
    return redirect(url_for('index'))

@app.route('/system-stats')
def system_stats():
    # Собираем данные с помощью psutil
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    net_io = psutil.net_io_counters()
    uptime = time.time() - psutil.boot_time()

    # Передаём данные в шаблон
    return render_template("system_stats.html",
                           cpu_percent=cpu_percent,
                           memory_percent=memory.percent,
                           memory_used_gb=memory.used / (1024**3),
                           memory_total_gb=memory.total / (1024**3),
                           disk_percent=disk.percent,
                           disk_used_gb=disk.used / (1024**3),
                           disk_total_gb=disk.total / (1024**3),
                           bytes_sent_mb=net_io.bytes_sent / (1024**2),
                           bytes_recv_mb=net_io.bytes_recv / (1024**2),
                           uptime_seconds=uptime)

@app.route('/api/system-metrics')
def api_system_metrics():
    # Собираем метрики аналогично предыдущему примеру
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent

    return { "cpu": cpu, "memory": mem, "disk": disk }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
