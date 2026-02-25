from flask import Flask, render_template, request, redirect, url_for, session, flash
import oracledb
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_demo'

# Database Configuration (Updated per your request)
db_user = "system"
db_password = "123456"

def ensure_delete_archive_objects(conn):
    cursor = conn.cursor()
    try:
        cursor.execute("""
            BEGIN
                EXECUTE IMMEDIATE '
                    CREATE TABLE DELETED_ITEMS (
                        source_table VARCHAR2(20) NOT NULL,
                        source_id NUMBER NOT NULL,
                        item_name VARCHAR2(100) NOT NULL,
                        length NUMBER NOT NULL,
                        width NUMBER NOT NULL,
                        height NUMBER NOT NULL,
                        deleted_at TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
                    )';
            EXCEPTION
                WHEN OTHERS THEN
                    IF SQLCODE != -955 THEN RAISE; END IF;
            END;
        """)

        cursor.execute("""
            CREATE OR REPLACE TRIGGER trg_room_delete_archive
            BEFORE DELETE ON ROOM
            FOR EACH ROW
            BEGIN
                INSERT INTO DELETED_ITEMS (source_table, source_id, item_name, length, width, height)
                VALUES ('ROOM', :OLD.room_id, :OLD.room_name, :OLD.length, :OLD.width, :OLD.height);
            END;
        """)

        cursor.execute("""
            CREATE OR REPLACE TRIGGER trg_furniture_delete_archive
            BEFORE DELETE ON FURNITURE
            FOR EACH ROW
            BEGIN
                INSERT INTO DELETED_ITEMS (source_table, source_id, item_name, length, width, height)
                VALUES ('FURNITURE', :OLD.furniture_id, :OLD.furniture_name, :OLD.length, :OLD.width, :OLD.height);
            END;
        """)
    finally:
        cursor.close()

def get_db_connection():
    try:
        dsn = oracledb.makedsn("localhost", 1521, service_name="XEPDB1")
        connection = oracledb.connect(user=db_user, password=db_password, dsn=dsn)
        ensure_delete_archive_objects(connection)
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

@app.route('/rooms/delete/<int:room_id>', methods=['POST'])
def delete_room(room_id):
    if 'login_time' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if not conn:
        flash("Database connection failed.", "error")
        return redirect(url_for('rooms'))

    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM ROOM WHERE room_id = :1", (room_id,))
        conn.commit()
        if cursor.rowcount:
            flash('Room deleted successfully!', 'success')
        else:
            flash('Room not found.', 'error')
    except Exception as e:
        flash(f'Error deleting room: {e}', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('rooms'))

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

@app.route('/furniture/delete/<int:furniture_id>', methods=['POST'])
def delete_furniture(furniture_id):
    if 'login_time' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if not conn:
        flash("Database connection failed.", "error")
        return redirect(url_for('furniture'))

    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM FURNITURE WHERE furniture_id = :1", (furniture_id,))
        conn.commit()
        if cursor.rowcount:
            flash('Furniture deleted successfully!', 'success')
        else:
            flash('Furniture not found.', 'error')
    except Exception as e:
        flash(f'Error deleting furniture: {e}', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('furniture'))

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

@app.route('/ar_viewer')
def ar_viewer():
    if 'login_time' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if not conn:
        flash("Database connection failed.", "error")
        return redirect(url_for('dashboard'))

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT room_id, room_name, length, width, height FROM ROOM ORDER BY room_name")
        rooms_rows = cursor.fetchall()
        cursor.execute("SELECT furniture_id, furniture_name, length, width, height FROM FURNITURE ORDER BY furniture_name")
        furniture_rows = cursor.fetchall()
    except Exception as e:
        cursor.close()
        conn.close()
        flash(f"Error loading AR data: {e}", "error")
        return redirect(url_for('dashboard'))

    cursor.close()
    conn.close()

    rooms_data = [
        {"id": int(r[0]), "name": r[1], "length": float(r[2]), "width": float(r[3]), "height": float(r[4])}
        for r in rooms_rows
    ]
    furniture_data = [
        {"id": int(f[0]), "name": f[1], "length": float(f[2]), "width": float(f[3]), "height": float(f[4])}
        for f in furniture_rows
    ]

    selected_room_id = request.args.get('room_id', type=int)
    selected_furniture_id = request.args.get('furniture_id', type=int)

    selected_room = next((r for r in rooms_data if r["id"] == selected_room_id), rooms_data[0] if rooms_data else None)
    selected_furniture = next((f for f in furniture_data if f["id"] == selected_furniture_id), furniture_data[0] if furniture_data else None)

    return render_template(
        'ar_viewer.html',
        rooms=rooms_data,
        furniture=furniture_data,
        selected_room=selected_room,
        selected_furniture=selected_furniture
    )

@app.route('/sessions')
def sessions_page():
    if 'login_time' not in session: return redirect(url_for('login'))
    login_time = session.get('login_time')
    return render_template('sessions.html', login_time=login_time)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
