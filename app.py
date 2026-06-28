from flask import Flask, render_template, request, redirect, session
import sqlite3
import qrcode
import os

app = Flask(__name__)
app.secret_key = "mysecretkey"
# Create database tables
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    password TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS passes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    passenger_name TEXT,
    source TEXT,
    destination TEXT,
    duration TEXT,
    pass_id TEXT,
    fare INTEGER
)
''')

conn.commit()
conn.close()

# Home Page
@app.route('/')
def home():
    return render_template('index.html')

# Register Page
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            password TEXT
        )
        ''')

        cursor.execute(
            "INSERT INTO users(name,email,password) VALUES(?,?,?)",
            (name, email, password)
        )

        conn.commit()
        conn.close()


        return render_template('success.html')

    return render_template('register.html')


# Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:
         session['user'] = email
         session['email'] = email         
         return redirect('/dashboard')

        else:
            return render_template('error.html')

    return render_template('login.html')


# Book Pass Page
@app.route('/book', methods=['GET', 'POST'])
def book():

    if request.method == 'POST':

        name = request.form['name']
        source = request.form['source']
        destination = request.form['destination']
        duration = request.form['duration']

        # Calculate fare
        if duration == "Daily":
            fare = 50
        elif duration == "Weekly":
            fare = 250
        elif duration == "Monthly":
            fare = 1000
        else:
            fare = 50

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Create passes table if it does not exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS passes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            passenger_name TEXT,
            source TEXT,
            destination TEXT,
            duration TEXT,
            pass_id TEXT,
            fare INTEGER
        )
        ''')

        # Generate pass ID
        cursor.execute("SELECT COUNT(*) FROM passes")
        count = cursor.fetchone()[0]
        
        pass_id = "PASS" + str(count + 1).zfill(3)

        qr_data = f"""
        Pass ID: {pass_id}
        Name: {name}
        Source: {source}
        Destination: {destination}
        Duration: {duration}
        Fare: ₹{fare}
        """

        qr = qrcode.make(qr_data)

        qr_path = os.path.join("static", f"{pass_id}.png")

        qr.save(qr_path)


        # Save pass details
        cursor.execute(
            '''
            INSERT INTO passes
            (passenger_name, source, destination, duration, pass_id, fare)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (name, source, destination, duration, pass_id, fare)
        )

        conn.commit()
        conn.close()

        return render_template(
            'pass.html',
            pass_id=pass_id,
            name=name,
            source=source,
            destination=destination,
            duration=duration,
            fare=fare,
            qr_image=f"{pass_id}.png"
        )

    return render_template('book.html')

@app.route('/history')
def history():

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(
        "SELECT pass_id, passenger_name, source, destination, duration, fare FROM passes"
    )

    passes = cursor.fetchall()

    conn.close()

    return render_template(
        'history.html',
        passes=passes
    )
@app.route('/profile')
def profile():
    return render_template(
        'profile.html',
        email=session.get('email')
        )


@app.route('/logout')
def logout():
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    return render_template('dashboard.html')

@app.route('/admin')
def admin():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    search = request.args.get('search')

    if search:
        cursor.execute(
        "SELECT * FROM users WHERE name LIKE ?",
        ('%' + search + '%',)
    )
    else:
      cursor.execute("SELECT * FROM users")

    users = cursor.fetchall()  

    conn.close()

    return render_template(
        'admin.html',
        users=users
    )
@app.route('/delete/<int:user_id>')
def delete(user_id):

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE id=?", (user_id,))

    conn.commit()
    conn.close()

    return redirect('/admin')

if __name__ == "__main__":
    app.run(debug=True) 