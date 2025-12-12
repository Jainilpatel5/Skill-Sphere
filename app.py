from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import bcrypt

app = Flask(__name__)

# --- CONFIGURATION ---
app.secret_key = 'your_super_secret_key' # Change this in production!

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'username' # Your MySQL username
app.config['MYSQL_PASSWORD'] = 'password' # Your MySQL password
app.config['MYSQL_DB'] = 'website_db'
app.config['MYSQL_CURSORCLASS'] = 'cursor' # Returns results as dictionaries

mysql = MySQL(app)

# --- HELPER FUNCTIONS ---
def is_logged_in():
    return 'user_id' in session

def get_user_role():
    return session.get('role', None)

# --- MAIN ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')

# --- AUTHENTICATION ROUTES ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        role = request.form['role']

        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

        cur = mysql.connection.cursor()
        try:
            cur.execute("INSERT INTO Users(name, email, password_hash, role) VALUES(%s, %s, %s, %s)",
                        (name, email, hashed_password, role))
            mysql.connection.commit()

            # If tutor, create a tutor profile
            if role == 'tutor':
                user_id = cur.lastrowid
                cur.execute("INSERT INTO TutorProfile(tutor_id) VALUES (%s)", [user_id])
                mysql.connection.commit()

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'An error occurred: {e}', 'danger')
        finally:
            cur.close()

    return render_template('auth/register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password_candidate = request.form['password'].encode('utf-8')

        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM Users WHERE email = %s", [email])

        if result > 0:
            user = cur.fetchone()
            cur.close()
            password_hash = user['password_hash'].encode('utf-8')

            if bcrypt.checkpw(password_candidate, password_hash):
                # Password matches
                session['is_logged_in'] = True
                session['user_id'] = user['user_id']
                session['name'] = user['name']
                session['role'] = user['role']
                
                flash('You are now logged in.', 'success')
                # Redirect based on role
                if session['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif session['role'] == 'tutor':
                    return redirect(url_for('tutor_dashboard'))
                else: # student
                    return redirect(url_for('student_dashboard'))
            else:
                flash('Invalid login.', 'danger')
        else:
            flash('Email not found.', 'danger')
            
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out.', 'success')
    return redirect(url_for('login'))


# --- ADMIN ROUTES ---
@app.route('/admin/dashboard')
def admin_dashboard():
    if not is_logged_in() or get_user_role() != 'admin':
        flash('Unauthorized Access', 'danger')
        return redirect(url_for('login'))
        
    cur = mysql.connection.cursor()
    # Fetch some stats for the dashboard
    total_users = cur.execute("SELECT * FROM Users")
    total_tutors = cur.execute("SELECT * FROM Users WHERE role='tutor'")
    total_sessions = cur.execute("SELECT * FROM Sessions WHERE status='completed'")
    cur.close()
    
    stats = {
        'total_users': total_users,
        'total_tutors': total_tutors,
        'total_sessions': total_sessions
    }
        
    return render_template('admin/dashboard.html', stats=stats)

@app.route('/admin/manage_users')
def manage_users():
    if not is_logged_in() or get_user_role() != 'admin':
        flash('Unauthorized Access', 'danger')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    # Query to get all users and their tutor verification status if they are a tutor
    cur.execute("""
        SELECT u.*, tp.verification_status
        FROM Users u
        LEFT JOIN TutorProfile tp ON u.user_id = tp.tutor_id
        ORDER BY u.created_at DESC
    """)
    users = cur.fetchall()
    cur.close()
    return render_template('admin/manage_users.html', users=users)

@app.route('/admin/tutor/approve/<int:tutor_id>', methods=['POST'])
def approve_tutor(tutor_id):
    if not is_logged_in() or get_user_role() != 'admin':
        flash('Unauthorized Access', 'danger')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    cur.execute("UPDATE TutorProfile SET verification_status = 'verified' WHERE tutor_id = %s", [tutor_id])
    mysql.connection.commit()
    cur.close()

    flash('Tutor has been verified successfully!', 'success')
    return redirect(url_for('manage_users'))
    
# --- TUTOR ROUTES ---
@app.route('/tutor/dashboard')
def tutor_dashboard():
    if not is_logged_in() or get_user_role() != 'tutor':
        flash('Unauthorized Access', 'danger')
        return redirect(url_for('login'))
    return render_template('tutor/dashboard.html')

@app.route('/tutor/profile/edit', methods=['GET', 'POST'])
def edit_tutor_profile():
    if not is_logged_in() or get_user_role() != 'tutor':
        flash('Unauthorized Access', 'danger')
        return redirect(url_for('login'))

    tutor_id = session['user_id']
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        bio = request.form['bio']
        hourly_rate = request.form['hourly_rate']
        skill_ids = request.form.getlist('skills') # Gets a list of checked skill IDs

        # Update Users table
        cur.execute("UPDATE Users SET name = %s, bio = %s WHERE user_id = %s", (name, bio, tutor_id))
        
        # Update TutorProfile table
        cur.execute("UPDATE TutorProfile SET hourly_rate = %s WHERE tutor_id = %s", (hourly_rate, tutor_id))

        # Update TutorSkills (many-to-many relationship)
        # 1. Delete existing skills for this tutor
        cur.execute("DELETE FROM TutorSkills WHERE tutor_id = %s", [tutor_id])
        # 2. Insert the new selection of skills
        for skill_id in skill_ids:
            cur.execute("INSERT INTO TutorSkills (tutor_id, skill_id) VALUES (%s, %s)", (tutor_id, skill_id))

        mysql.connection.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('tutor_dashboard'))

    # GET request: Fetch current data to populate the form
    # Fetch tutor's main details
    cur.execute("""
        SELECT u.name, u.bio, tp.hourly_rate
        FROM Users u
        JOIN TutorProfile tp ON u.user_id = tp.tutor_id
        WHERE u.user_id = %s
    """, [tutor_id])
    tutor = cur.fetchone()

    # Fetch all available skills
    cur.execute("SELECT * FROM Skills")
    all_skills = cur.fetchall()

    # Fetch skill IDs this tutor currently has
    cur.execute("SELECT skill_id FROM TutorSkills WHERE tutor_id = %s", [tutor_id])
    tutor_skills_raw = cur.fetchall()
    tutor_skills = {item['skill_id'] for item in tutor_skills_raw} # Use a set for efficient lookup
    
    cur.close()

    return render_template('tutor/edit_profile.html', tutor=tutor, all_skills=all_skills, tutor_skills=tutor_skills)


# --- STUDENT ROUTES ---
@app.route('/student/dashboard')
def student_dashboard():
    if not is_logged_in() or get_user_role() != 'student':
        flash('Unauthorized Access', 'danger')
        return redirect(url_for('login'))
    return render_template('student/dashboard.html')

@app.route('/student/browse')
def browse_tutors():
    if not is_logged_in() or get_user_role() != 'student':
        flash('Unauthorized Access', 'danger')
        return redirect(url_for('login'))
        
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT u.user_id, u.name, u.bio, tp.hourly_rate, tp.rating_avg
        FROM Users u
        JOIN TutorProfile tp ON u.user_id = tp.tutor_id
        WHERE u.role = 'tutor' AND tp.verification_status = 'verified'
    """)
    tutors = cur.fetchall()
    cur.close()

    return render_template('student/browse_tutors.html', tutors=tutors)

@app.route('/tutor/manage_sessions')
def manage_sessions():
    if not is_logged_in() or get_user_role() != 'tutor':
        flash('Unauthorized Access', 'danger')
        return redirect(url_for('login'))

    tutor_id = session['user_id']
    cur = mysql.connection.cursor()
    # Query to get sessions for the logged-in tutor, joining other tables for more info
    cur.execute("""
        SELECT s.*, u_student.name as student_name, sk.skill_name
        FROM Sessions s
        JOIN Users u_student ON s.student_id = u_student.user_id
        JOIN Skills sk ON s.skill_id = sk.skill_id
        WHERE s.tutor_id = %s
        ORDER BY s.start_time DESC
    """, [tutor_id])
    sessions = cur.fetchall()
    cur.close()
    return render_template('tutor/manage_sessions.html', sessions=sessions)

@app.route('/tutor/profile/<int:tutor_id>')
def tutor_profile(tutor_id):
    if not is_logged_in():
        flash('Please log in to view profiles.', 'danger')
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()
    # Fetch tutor's main details
    cur.execute("""
        SELECT u.user_id, u.name, u.bio, tp.hourly_rate, tp.rating_avg
        FROM Users u
        JOIN TutorProfile tp ON u.user_id = tp.tutor_id
        WHERE u.user_id = %s
    """, [tutor_id])
    tutor = cur.fetchone()

    # Fetch skills offered by this specific tutor
    cur.execute("""
        SELECT s.skill_id, s.skill_name
        FROM Skills s
        JOIN TutorSkills ts ON s.skill_id = ts.skill_id
        WHERE ts.tutor_id = %s
    """, [tutor_id])
    skills = cur.fetchall()
    cur.close()

    if not tutor:
        flash('Tutor not found.', 'danger')
        return redirect(url_for('browse_tutors'))

    return render_template('student/tutor_profile.html', tutor=tutor, skills=skills)


@app.route('/session/book', methods=['POST'])
def book_session():
    if not is_logged_in() or get_user_role() != 'student':
        flash('You must be logged in as a student to book sessions.', 'danger')
        return redirect(url_for('login'))

    # Get data from form
    tutor_id = request.form['tutor_id']
    skill_id = request.form['skill_id']
    start_time = request.form['session_date'] # Format: YYYY-MM-DDTHH:MM
    student_id = session['user_id']
    
    # For a 1-hour session
    from datetime import datetime, timedelta
    end_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M') + timedelta(hours=1)
    
    # Simplified session link
    session_link = f"https://meet.example.com/{tutor_id}-{student_id}-{datetime.now().timestamp()}"

    cur = mysql.connection.cursor()
    
    # Get tutor's hourly rate to calculate payment amount
    cur.execute("SELECT hourly_rate FROM TutorProfile WHERE tutor_id = %s", [tutor_id])
    tutor = cur.fetchone()
    amount = tutor['hourly_rate']

    # 1. Create the session
    cur.execute("""
        INSERT INTO Sessions (tutor_id, student_id, skill_id, start_time, end_time, session_link, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'booked')
    """, (tutor_id, student_id, skill_id, start_time, end_time, session_link))
    
    session_id = cur.lastrowid

    # 2. Create the payment record (simulating a successful payment)
    cur.execute("""
        INSERT INTO Payments (session_id, amount, payment_status)
        VALUES (%s, %s, 'completed')
    """, (session_id, amount))

    mysql.connection.commit()
    cur.close()

    flash('Session booked successfully!', 'success')
    return redirect(url_for('student_dashboard'))


if __name__ == '__main__':
    app.run(debug=True)