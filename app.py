# Import necessary libraries
import os
import datetime
import smtplib
from collections import namedtuple
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import mysql.connector
import pandas
from flask import (Flask, jsonify, redirect, render_template, request,
                   send_file, session, url_for)

from PyPDF2 import PdfFileReader, PdfFileWriter
from flask import flash

from flask_mail import Mail, Message
from flask import request, render_template_string
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

# Create a Flask web application
app = Flask(__name__)
app.secret_key = 'anything_info'  # Replace with your actual secret key

# Establish a connection to the database
db = mysql.connector.connect(
    host='localhost',
    user='root',
    password='12345Allen@',
    database='registration',
    auth_plugin='mysql_native_password'
)
def get_database_connection():
    return mysql.connector.connect(**db)

def close_database_connection(connection, cursor):
    cursor.close()
    connection.close()

cursor = db.cursor()

# Define a function to create the database table
def create_onboards_table():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_onboards (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            last_name VARCHAR(255),
            email VARCHAR(255),
            phone_number VARCHAR(20),
            gender VARCHAR(10),
            date_of_birth DATE,
            address VARCHAR(255),
            educational_qualification VARCHAR(50),
            experience_on_previous_jobs VARCHAR(50),
            total_experience VARCHAR(50),
            additional_certifications VARCHAR(255),
            salary_expectations VARCHAR(50),
            field_of_application VARCHAR(50),
            position_for_selected_field VARCHAR(50)
        )
    ''')

# Create an empty list for regularization requests
regularization_requests = []

# Define the root route
@app.route('/')
def index():
    return render_template('login.html')



# Define a route to submit regularization requests
@app.route('/submit_regularization', methods=['POST'])
def submit_regularization():
    if request.method == 'POST':
        date = request.form['date']
        login_time = request.form['login_time']
        logout_time = request.form['logout_time']
        reason = request.form['reason']

        # Store the regularization request (you would save this to your database)
        regularization_requests.append({
            'date': date,
            'login_time': login_time,
            'logout_time': logout_time,
            'reason': reason,
        })

        return "Request submitted for approval"

# Define a route to download salary slips
@app.route('/download')
def download():
    # Retrieve user data from the database 
    cursor.execute('SELECT id, name, salary_pdf_path FROM regis')
    users_data = cursor.fetchall()

    # Convert the data into a named tuple
    User = namedtuple('User', ['id', 'name', 'salary_pdf_path'])
    users = [User(*record) for record in users_data]

    return render_template('download.html', users=users)

# Define a route for user login
@app.route('/login', methods=['POST'])
def login_post():
    username = request.form['username']
    password = request.form['password']

    cursor.execute('SELECT * FROM regis WHERE username = %s AND password = %s', (username, password))
    user = cursor.fetchone()

    if user:
        session['user_id'] = user[0]
        
        cursor.execute('UPDATE regis SET login_count = login_count + 1 WHERE id = %s', (user[0],))
        db.commit()
        
        return redirect('/dashboard')
    else:
        error_msg = 'Invalid username or password. Please try again.'
        return render_template('login.html', error_msg=error_msg)

# Define a route for user registration
@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_post():
    # Retrieve form data
    name = request.form['name']
    last_name = request.form['last_name']
    email = request.form['email']
    phone_number = request.form['phone_number']
    gender = request.form['gender']
    date_of_birth = request.form['date_of_birth']
    address = request.form['address']
    educational_qualification = request.form['educational_qualification']
    experience_on_previous_jobs = request.form['experience_on_previous_jobs']
    total_experience = request.form['total_experience']
    additional_certifications = request.form['additional_certifications']
    salary_expectations = request.form['salary_expectations']
    field_of_application = request.form['field_of_application']
    position_for_selected_field = request.form['position_for_selected_field']

    # Insert data into the onboards table
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO user_onboards (
            name, last_name, email, phone_number, gender, date_of_birth, address,
            educational_qualification, experience_on_previous_jobs, total_experience,
            additional_certifications, salary_expectations, field_of_application,
            position_for_selected_field
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        name, last_name, email, phone_number, gender, date_of_birth, address,
        educational_qualification, experience_on_previous_jobs, total_experience,
        additional_certifications, salary_expectations, field_of_application,
        position_for_selected_field
    ))
    db.commit()

    success_msg = 'Registration successful! Please log in.'
    return render_template('login.html', success_msg=success_msg)

# Define the dashboard route
@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        user_id = session['user_id']
        cursor.execute('SELECT username, login_count FROM regis WHERE id = %s', (user_id,))
        user = cursor.fetchone()

        if user:
            username = user[0]
            login_count = user[1]
            
            if user_id == 5 or user_id == 6:
                # Fetch registration details 
                df = pandas.read_sql_query('SELECT * FROM regis', db)
                pandas.set_option('colheader_justify', 'center')   # For creating table headers
                
                return render_template('dashboard.html', admin_access=True, user_table=df.to_html(classes='mystyle'))

            # Fetch registration details of the logged-in user
            cursor.execute('SELECT name, last_name, address, mobile_number, alternate_mobile_number, alternate_address, date_of_birth, date_of_joining, date_of_registration, last_working_day, qualifications, experience FROM regis WHERE id = %s', (user_id,))
            registration_details = cursor.fetchone()

            return render_template('dashboard_user.html', username=username, login_count=login_count, registration_details=registration_details)

    return redirect('/')

# -----salary slips ------- #


# Define a route to log out the user
@app.route('/logout', methods=['POST'])
def logout():
    if 'user_id' in session:
        session.pop('user_id', None)
        return render_template('logout.html', username='Unknown')
    else:
        return redirect('/')



# Define a function to create the attendance regularization table
def create_attendance_regularization_table():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance_regularization (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            regularization_date DATE,
            FOREIGN KEY (user_id) REFERENCES regis(id)
        )
    ''')

# Call the function to create the table



admin_ids = [1]

team_leader_hr_ids = [2]



from flask import session, render_template, redirect
from collections import namedtuple
team_leader_hr_ids = [1, 2, 3,5,6] 
@app.route('/leave_approval_list')
def leave_approval_list():
    # Debug: Print session data
    print('Session data:', session)
    
    if 'user_id' in session and session['user_id'] in team_leader_hr_ids:
        # Initialize database cursor
        cursor = db.cursor()
        
        # Fetch leave requests from the database
        cursor.execute('SELECT id, employee_name, leave_type, start_date, end_date, email FROM leaves')
        leave_requests_data = cursor.fetchall()
        
        # Convert the data into a named tuple
        LeaveRequest = namedtuple('LeaveRequest', ['id', 'employee_name', 'leave_type', 'start_date', 'end_date', 'email'])
        leave_requests = [LeaveRequest(*record) for record in leave_requests_data]

        # Close cursor after use
        cursor.close()

        return render_template('leave_approval_list.html', leave_requests=leave_requests)
    else:
        # Debug: Print message when redirecting
        print('Redirecting to login page.')
        return redirect('/')  # Ensure your login route is correct



#     return render_template('attendance_regularization.html')
# ------------- Assets pannel start ----------#
@app.route('/Assets_Mangement')
def Assets_Mangement():
    return render_template('Assets_Mangement.html') 
# ------------- Assets pannel end  ----------#

# ------------- On Boarding pannel start ----------#
@app.route('/on_boarding')
def on_boarding():
    return render_template('on_boarding.html') 

#---attendance_regularization ---- #
@app.route('/attendance_regularization')
def attendance_regularization():
    return render_template('attendance_regularization.html') 

# ------------- On Boarding pannel end  ----------#

# ------------- OF Boarding pannel start ----------#
@app.route('/offboarding')
def OF_boarding():
    return render_template('offboarding.html') 

@app.route('/joining', methods=['GET','POST'])
def joining():
    try:
        # Create a cursor to execute queries
        cursor = db.cursor(dictionary=True)

        # Fetch resignation details from the database
        cursor.execute("SELECT * FROM resignations")
        resignation_details = cursor.fetchall()

        # Close the cursor (do not close the connection here)
        cursor.close()

        return render_template('joining.html', resignations=resignation_details)
    except mysql.connector.Error as error:
        # Handle database errors
        print("Error fetching resignation details:", error)
        return "An error occurred while fetching resignation details", 500
# ------------- OF Boarding pannel end  ----------#

# ------------- Insurances start ----------#
@app.route('/on_Insurance')
def insurance():
    return render_template('insurance.html') 
# ------------- Insurance end  ----------#


#------ Assets Life Cycle------#
@app.route('/asset-life')
def assets_life():
    return render_template('assets_life.html')

# ------------Assets Assining------- #

# Define a function to fetch user onboards from the database
def get_user_onboards():
    cursor = db.cursor()
    cursor.execute("SELECT name FROM user_onboards")
    names = [row[0] for row in cursor.fetchall()]  # Extract names from the query result
    cursor.close()
    return names

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '12345Allen@',
    'database': 'registration',
    'auth_plugin': 'mysql_native_password'
}

@app.route('/assing_assets')
def assing_assets():
    # Fetch names from the database
    names = get_user_onboards()
    # Pass the names to the HTML template for rendering
    # Fetch assigned assets from the database
    assigned_assets = []
    try:
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()
        cursor.execute("SELECT user_name, asset FROM assigned_assets")
        assigned_assets = cursor.fetchall()
        cursor.close()
    except mysql.connector.Error as err:
        print("Error:", err)

    # Pass the names and assigned assets to the HTML template for rendering
    return render_template('assing_assets.html', names=names, assigned_assets=assigned_assets)

def get_database_connection():
    try:
        db = mysql.connector.connect(**db_config)
        return db
    except mysql.connector.Error as err:
        print("Error:", err)
        return None

@app.route('/assign_asset', methods=['POST'])
def assign_asset():
    name = request.form['name']
    asset = request.form['asset']
    db = get_database_connection()
    if db:
        try:
            cursor = db.cursor()
            cursor.execute("INSERT INTO assigned_assets (user_name, asset) VALUES (%s, %s)", (name, asset))
            db.commit()
            cursor.close()
            db.close()  # Close the database connection
            return "Asset assigned successfully"
        except mysql.connector.Error as err:
            print("Error:", err)
            return "Error assigning asset"
    else:
        return "Database connection error"



#------  Latter    ------#
@app.route('/On_latter')
def On_latter():
    return render_template('On_latter.html')


@app.route('/users_del')
def users():
    try:
        # Create a cursor to execute queries
        cursor = db.cursor(dictionary=True)

        # Fetch resignation details from the database
        cursor.execute("SELECT * FROM user_onboards")
        users = cursor.fetchall()

        # Close the cursor (do not close the connection here)
        cursor.close()

        return render_template('users_del.html', user_details=users)
    except mysql.connector.Error as error:
        # Handle database errors
        print("Error fetching resignation details:", error)
        return "An error occurred while fetching resignation details", 500
    
@app.route('/accepted_users')
def accepted_users():
    try:
        # Connect to the database
        db = mysql.connector.connect(
            host='localhost',
            user='root',
            password='12345Allen@',
            database='registration'
        )

        # Create a cursor to execute queries
        cursor = db.cursor(dictionary=True)

        # Execute SQL query to retrieve accepted users
        cursor.execute("SELECT * FROM user_onboards WHERE status = 'accepted'")
        accepted_users = cursor.fetchall()

        # Close the cursor and database connection
        cursor.close()
        db.close()

        # Render the HTML template with the accepted users data
        return render_template('accepted_users.html', accepted_users=accepted_users)

    except mysql.connector.Error as error:
        # Handle database errors
        return 'Error accessing database: ' + str(error)

    except Exception as e:
        # Handle other exceptions
        return 'Error: ' + str(e)

from mysql.connector import Error   
@app.route('/accept_form', methods=['POST'])
def accept_form():
    try:
        email = request.form['email']  

        # Email configuration
        sender_email = 'allenpereira1107@gmail.com'
        receiver_email = email
        password = 'tasr cfkt vitt mcie'
        
        # Update the database
        update_query = "UPDATE user_onboards SET status = 'accepted' WHERE email = %s"
        cursor = db.cursor()
        cursor.execute(update_query, (email,))
        db.commit()

        # Send the email
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = receiver_email
        message['Subject'] = 'Form Accepted'

        body = 'Your form request has been accepted. Please send your document on this link - https://docs.google.com/forms/d/11U-QOx5t8yupvTmzyxyMB0vgnCFb8ByK1gBB3n62Zz4/edit?usp=drivesdk'
        message.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())

        return 'Email sent successfully and database updated.'
    except Error as e:
        return 'Database error: ' + str(e)
    except Exception as e:
        return 'Error: ' + str(e)

#---- resign -----#
@app.route('/resignation_form')
def resignation_form():
    return render_template('resign_on.html')

# Route to handle form submission

@app.route('/submit_resignation', methods=['POST'])
def submit_resignation():
    # Extract form data
    name = request.form['name']
    email = request.form['email']
    position = request.form['position']
    reason = request.form['reason']
    assets_taken = request.form['assets_taken']
    assets_list = request.form.get('assets_list', '')  # Optional field, default to empty string

    try:
        # Use the existing database connection object
        cursor = db.cursor()

        # Insert resignation details into the database
        sql = "INSERT INTO resignations (name, email, position, reason, assets_taken, assets_list) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(sql, (name, email, position, reason, assets_taken, assets_list))
        db.commit()

        # Close cursor (connection remains open for future use)
        cursor.close()

        # Redirect to user dashboard or any other page
        return redirect('/dashboard_user')
    except mysql.connector.Error as error:
        # Handle database errors
        print("Error inserting into MySQL table:", error)
        return "An error occurred while processing your request", 500

#HR OFFBOARD PAGE
    
@app.route('/F_boarding')
def offboarding_page():
    try:
        # Create a cursor to execute queries
        cursor = db.cursor(dictionary=True)

        # Fetch resignation details from the database
        cursor.execute("SELECT * FROM resignations")
        resignation_details = cursor.fetchall()

        # Close the cursor (do not close the connection here)
        cursor.close()

        return render_template('F_boarding.html', resignations=resignation_details)
    except mysql.connector.Error as error:
        # Handle database errors
        print("Error fetching resignation details:", error)
        return "An error occurred while fetching resignation details", 500

 # MAIL
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Replace with your SMTP server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'allenpereira1107@gmail.com'
app.config['MAIL_PASSWORD'] = 'tasr cfkt vitt mcie'
app.config['MAIL_DEFAULT_SENDER'] = 'allenpereira1107@gmail.com'
mail = Mail(app)

@app.route('/accept_resignation', methods=['POST'])
def accept_resignation():
    resignation_id = request.form.get('resignation_id')
    email = request.form.get('email')

    try:
        # Re-establish the connection and create a new cursor
        cursor = db.cursor()

        # Update the status of the resignation in the database to "accepted"
        cursor.execute("UPDATE resignations SET status = 'accepted' WHERE id = %s", (resignation_id,))
        db.commit()

        # Close the cursor
        cursor.close()

        # Send an email notification to the employee
        subject = "Your resignation has been accepted"
        message = "Dear Employee,\n\nYour resignation has been accepted. We wish you the best in your future endeavors."
        send_email(email, subject, message)

        return redirect(url_for('offboarding_page'))
    except mysql.connector.Error as error:
        # Handle database errors
        print("Error accepting resignation:", error)
        return "An error occurred while accepting resignation", 500


def send_email(to_email, subject, message):
    # Configure SMTP server details
    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 587
    SMTP_USERNAME = 'allenpereira1107@gmail.com'
    SMTP_PASSWORD = 'tasr cfkt vitt mcie'

    try:
        # Create a connection to the SMTP server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)

        # Construct the email message
        email_message = f"Subject: {subject}\n\n{message}"

        # Send the email
        server.sendmail(SMTP_USERNAME, to_email, email_message)

        # Close the connection
        server.quit()
    except smtplib.SMTPAuthenticationError as auth_error:
        # Handle authentication errors
        print("SMTP Authentication Error:", auth_error)
    except Exception as e:
        # Handle other email sending errors
        print("Error sending email:", e)



#---- Leave --- #
# Route to render the leave request form
@app.route('/leave_request_form')
def leave_request_form():
    return render_template('leave_request_form.html')

# Route to handle form submission
@app.route('/submit_leave', methods=['POST'])
def submit_leave():
    try:
        # Extract form data
        employee_name = request.form['employeeName']
        employee_email = request.form['employeeMail']
        leave_type = request.form['leaveType']
        start_date = request.form['startDate']
        end_date = request.form['endDate']
        
        # Insert the form data into the leaves table
        cursor = db.cursor()
        insert_query = "INSERT INTO leaves (employee_name, email, leave_type, start_date, end_date) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(insert_query, (employee_name, employee_email, leave_type, start_date, end_date))
        db.commit()
        cursor.close()

        return 'Leave request submitted successfully!'
    except Exception as e:
        return f"An error occurred: {str(e)}"



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)

