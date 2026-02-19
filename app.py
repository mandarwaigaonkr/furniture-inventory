from flask import Flask, render_template, request, redirect, url_for, session, flash
import oracledb
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_demo'

# Database Configuration (Updated per your request)
db_user = "system"
db_password = "123456"

def get_db_connection():
    try:
        dsn = oracledb.makedsn("localhost", 1521, service_name="XEPDB1")
        connection = oracledb.connect(user=db_user, password=db_password, dsn=dsn)
        return connection
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

@app.route('/')
def index():
    if 'login_time' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['login_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        flash('Successfully logged in!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('login_time', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'login_time' not in session: return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/rooms', methods=['GET', 'POST'])
def rooms():
    if 'login_time' not in session: return redirect(url_for('login'))
    
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed.", "error")
        return redirect(url_for('dashboard'))

    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['room_name']
        length = float(request.form['length'])
        width = float(request.form['width'])
        height = float(request.form['height'])

        try:
            cursor.execute(
                "INSERT INTO ROOM (room_id, room_name, length, width, height) VALUES (room_seq.NEXTVAL, :1, :2, :3, :4)",
                (name, length, width, height)
            )
            conn.commit()
            flash('Room added successfully!', 'success')
        except Exception as e:
            flash(f'Error adding room: {e}', 'error')
        
        return redirect(url_for('rooms'))

    cursor.execute("SELECT room_id, room_name, length, width, height FROM ROOM ORDER BY room_id DESC")
    rooms_data = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('rooms.html', rooms=rooms_data)

@app.route('/furniture', methods=['GET', 'POST'])
def furniture():
    if 'login_time' not in session: return redirect(url_for('login'))
    
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed.", "error")
        return redirect(url_for('dashboard'))

    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['furniture_name']
        length = float(request.form['length'])
        width = float(request.form['width'])
        height = float(request.form['height'])

        try:
            cursor.execute(
                "INSERT INTO FURNITURE (furniture_id, furniture_name, length, width, height) VALUES (furniture_seq.NEXTVAL, :1, :2, :3, :4)",
                (name, length, width, height)
            )
            conn.commit()
            flash('Furniture added successfully!', 'success')
        except Exception as e:
            flash(f'Error adding furniture: {e}', 'error')
        
        return redirect(url_for('furniture'))

    cursor.execute("SELECT furniture_id, furniture_name, length, width, height FROM FURNITURE ORDER BY furniture_id DESC")
    furniture_data = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('furniture.html', furniture=furniture_data)

@app.route('/fit_checker', methods=['GET', 'POST'])
def fit_checker():
    if 'login_time' not in session: return redirect(url_for('login'))
    
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed.", "error")
        return redirect(url_for('dashboard'))

    cursor = conn.cursor()
    cursor.execute("SELECT room_id, room_name FROM ROOM")
    rooms_list = cursor.fetchall()
    
    cursor.execute("SELECT furniture_id, furniture_name FROM FURNITURE")
    furniture_list = cursor.fetchall()

    result_message = None
    is_fit = False

    if request.method == 'POST':
        room_id = request.form.get('room_id')
        furniture_id = request.form.get('furniture_id')

        if room_id and furniture_id:
            try:
                cursor.execute("SELECT length, width, height FROM ROOM WHERE room_id = :1", (room_id,))
                r_dim = cursor.fetchone()
                cursor.execute("SELECT length, width, height FROM FURNITURE WHERE furniture_id = :1", (furniture_id,))
                f_dim = cursor.fetchone()

                if r_dim and f_dim:
                    r_len, r_wid, r_hgt = r_dim
                    f_len, f_wid, f_hgt = f_dim
                    
                    # Core Logic: Check if furniture fits
                    if (f_len <= r_len) and (f_wid <= r_wid) and (f_hgt <= r_hgt):
                        is_fit = True
                        result_message = "Furniture FITS in the room"
                    else:
                        is_fit = False
                        result_message = "Furniture DOES NOT FIT in the room"
            except Exception as e:
                flash(f"Error checking fit: {e}", "error")

    cursor.close()
    conn.close()
    return render_template('fit_checker.html', rooms=rooms_list, furniture=furniture_list, result=result_message, is_fit=is_fit)

@app.route('/sessions')
def sessions_page():
    if 'login_time' not in session: return redirect(url_for('login'))
    login_time = session.get('login_time')
    return render_template('sessions.html', login_time=login_time)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
