from flask import Flask, render_template, redirect, session, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import os
import csv
from fpdf import FPDF
from io import BytesIO
from flask import send_file
import random
import smtplib
from email.message import EmailMessage
from flask_mail import Mail, Message



app = Flask(__name__)
bcrypt = Bcrypt(app)

app.config['SECRET_KEY'] = 'school_management'

# Database Configuration - MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost/school_management'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Creating class to define models

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)  
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Staff(db.Model):
    ID = db.Column(db.Integer, primary_key= True, autoincrement=True)
    Staff_ID = db.Column(db.String(100), unique=True)
    Name = db.Column(db.String(100), nullable=False)
    Email = db.Column(db.String(100), unique=True, nullable=False)
    Password = db.Column(db.String(100), nullable=False)  
    Role = db.Column(db.String(20), nullable=False) 

class Students(db.Model):
    student_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    class_year = db.Column(db.Integer, nullable=False)
    academic_year = db.Column(db.String(9), nullable=False)
    tamil_mark = db.Column(db.Integer, nullable=True)
    english_mark = db.Column(db.Integer, nullable=True)
    maths_mark = db.Column(db.Integer, nullable=True)
    science_mark = db.Column(db.Integer, nullable=True)
    social_mark = db.Column(db.Integer, nullable=True)

@app.route('/')
def home():
    return render_template('index.html')

# Route for user login page
@app.route('/user_login')
def user_login():
    return render_template('login.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/admission')
def admission():
    return render_template('admission.html')

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

@app.route('/activities')
def activities():
    return render_template('activities.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        # Create the email
        msg = Message('Contact Form Submission', recipients=['dhanushiyaayyadurai18@gmail.com'])
        msg.body = f'Name: {name}\nEmail: {email}\n\nMessage:\n{message}'

        # Send the email
        Mail.send(msg)
        flash('Your message has been sent successfully!', 'success')  # Flash a success message
        return redirect(url_for('contact'))  # Redirect back to contact page

    return render_template('contact.html')


@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        roll_num = request.form['roll_number']
        dob = request.form['dob']  # Ensure you're getting 'dob' here

        # Query the student
        student = Students.query.filter_by(roll_number=roll_num, dob=dob).first()

        if student:
            return render_template('mark_report_portal.html', student=student)
        else:
            flash("Invalid credentials!")
            return redirect(url_for("student_login"))
    return render_template('student_login.html')


@app.route('/student_login/mark_report', methods=['GET', 'POST'])
def mark_report():
    if 'student' not in session:
        return redirect(url_for('student_login'))

    if request.method == 'POST':
        roll_number = request.form.get('roll_number')
        academic_year = request.form.get('academic_year')
        class_year = request.form.get('class_year')

        # Fetch the student details from the Students table
        student = Students.query.filter_by(roll_number=roll_number, academic_year=academic_year, class_year=class_year).first()

        if student:
            # Pass the student and marks data to the template
            return render_template('mark_report_portal.html', student=student)
        else:
            flash('No student found with the provided details.', 'danger')

    return render_template('mark_report_portal.html')


@app.route('/mark_report/download_pdf_report/<roll_number>/<academic_year>/<class_year>', methods=['GET'])
def download_pdf_report(roll_number, academic_year, class_year):
    # Fetch the student details from the database based on roll_number, academic_year, and class_year
    student = Students.query.filter_by(roll_number=roll_number, academic_year=academic_year, class_year=class_year).first()

    if not student:
        flash('Student not found', 'danger')
        return redirect(url_for('student_login'))

    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # PDF content for student report
    pdf.cell(200, 10, txt="Student Mark Report", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Name: {student.name}", ln=True)
    pdf.cell(200, 10, txt=f"Roll Number: {student.roll_number}", ln=True)
    pdf.cell(200, 10, txt=f"Class Year: {class_year}", ln=True)
    pdf.cell(200, 10, txt=f"Academic Year: {academic_year}", ln=True)

    # Marks with Pass/Fail status
    subjects = {
        'Tamil': student.tamil_mark,
        'English': student.english_mark,
        'Maths': student.maths_mark,
        'Science': student.science_mark,
        'Social': student.social_mark
    }

    for subject, mark in subjects.items():
        status = "Pass" if mark >= 35 else "Fail"
        pdf.cell(200, 10, txt=f"{subject}: {mark} ({status})", ln=True)

    # Save PDF to bytes
    pdf_output = pdf.output(dest='S').encode('latin1')

    # Wrap the PDF bytes in a BytesIO stream
    pdf_stream = BytesIO(pdf_output)

    # Send the PDF as a downloadable file
    return send_file(
        pdf_stream,
        as_attachment=True,
        download_name="student_mark_report.pdf",
        mimetype='application/pdf'
    )


@app.route('/admin_login', methods=['GET', 'POST'])  
def admin_login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        admin = Admin.query.filter_by(username=uname).first()
        if admin:
            print(f"Admin found: {admin.username}")
            print(f"Stored hashed password: {admin.password}")
        else:
            print(f"No admin found with username: {uname}")
            return redirect(url_for("admin_login"))
        
        if admin and bcrypt.check_password_hash(admin.password, pwd):
            session['admin']=True
            flash('You have logged in successfully!','success')
            return render_template('admin_dashboard.html')
        else:
            flash('Login failed! Please check your credentials.','error')
            return redirect(url_for("admin_login"))
    return render_template('admin_login.html')

@app.route('/admin_login/admin_dashboard',methods=['GET','POST'])
def admin_dashboard():
    if 'admin' in session:
        return render_template('admin_dashboard.html')
    

@app.route('/admin_dashboard/students')

def admin_student_manage():
    students = Students.query.all()  # Fetch all students from the database
    return render_template('admin_student_manage.html', students=students)


@app.route('/admin_dashboard/staff')
def admin_staff_manage():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    # Fetch all staff from the database
    staff = Staff.query.all()

    # Check if staff list is empty
    if not staff:
        flash("No staff records found!")

    return render_template('admin_staff_manage.html', staff=staff)


@app.route('/admin/create_staff', methods=['GET', 'POST'])
def create_staff():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        staff_id = request.form['staff_id']
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        # Hash the password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
         # Check if the staff already exists
        existing_staff = Staff.query.filter_by(Staff_ID=staff_id).first()
        if existing_staff:
            flash('Staff  already exists!')
        else:
            # Create a new staff member
            new_staff = Staff(Staff_ID=staff_id,Name=name, Email=email, Password=hashed_password, Role=role)
            db.session.add(new_staff)
            db.session.commit()
            flash('Staff member created successfully!')
            return redirect(url_for('admin_staff_manage'))
    
    return render_template('create_staff.html')

@app.route('/admin/update_staff', methods=['GET', 'POST'])
def update_staff():
    if request.method == 'POST':
        staff_id = request.form['staff_id']
        staff = Staff.query.filter_by(Staff_ID=staff_id).first()

        if staff:
            staff.Name = request.form['name']
            staff.Email = request.form['email']
            staff.Role = request.form['role']

            # Commit the changes to the database
            db.session.commit()
            flash('Staff details updated successfully!')
            return redirect(url_for('admin_staff_manage'))
        else:
            flash('Oops! Staff not found!')
            return redirect(url_for('admin_staff_manage'))

    # For GET request, fetch the staff data to pre-fill the form
    staff_id = request.args.get('staff_id')  # Get staff ID from query parameters
    staff = Staff.query.filter_by(Staff_ID=staff_id).first()  # Corrected field name
    if staff:
        return render_template('update_staff.html', staff=staff)  # Pass staff data to the template
    else:
        flash('Staff not found!')
        return redirect(url_for('admin_staff_manage'))

    
@app.route('/admin/delete_staff/<staff_id>', methods=['POST'])
def delete_staff(staff_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    # Find the staff member by ID and delete them
    staff_member = Staff.query.filter_by(Staff_ID=staff_id).first()
    if staff_member:
        db.session.delete(staff_member)
        db.session.commit()
        flash('Staff member deleted successfully.', 'success')
    else:
        flash('Staff member not found.', 'danger')

    return redirect(url_for('admin_staff_manage'))


# Staff login route
@app.route('/staff_login', methods=['GET', 'POST'])
def staff_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Query the database for the staff member
        staff_member = Staff.query.filter_by(Email=email).first()
        
        # Check if the staff member exists and if the password matches
        if staff_member and bcrypt.check_password_hash(staff_member.Password, password):
            session['staff_id'] = staff_member.Staff_ID  # Store staff ID in session
            session['role'] = staff_member.Role  # Store role in session
            flash('Login successful!', 'success')
            return render_template('staff_dashboard.html') # Redirect to staff dashboard
        else:
            flash('Invalid email or password!', 'danger')

    return render_template('staff_login.html') 

@app.route("/staff_login/forgot", methods=['GET','POST'])
def getemail():
    if request.method == 'POST':
        e_id = request.form['email']
        exist = Staff.query.filter_by(Email=e_id).first()

        if exist:
            def generate_otp():
                otp = random.randint(100000, 999999) #generates random six digit number
                return otp

            def send_otp(otp, receiver_email):
                sender_email = "dhanushiyaayyadurai18@gmail.com"
                sender_password = "beld jocl drjk ptah" #gmail app password

                msg = EmailMessage() 
                msg.set_content(f"Your OTP for password recovery is: {otp}\nNEVER SHARE THIS WITH ANYONE!")
                msg['Subject'] = "OTP for Password Recovery"
                msg['From'] = sender_email
                msg['To'] = receiver_email

                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp: #465 port number used for SSL-Encrypted email communication
                    smtp.login(sender_email, sender_password)
                    smtp.send_message(msg)

            otp = generate_otp()
            send_otp(otp, e_id) #calling the function
            
            session['otp'] = otp  # Store OTP in session
            session['email'] = e_id  # Store email in session 
            flash("OTP sent to your email.")
            return redirect(url_for('validateotp'))

        else:
            flash("Invalid email.")
            
    return render_template('get_email.html')


@app.route('/admin/forgot/validateotp', methods=['GET', 'POST'])
def validateotp():
    if request.method == 'POST':
        otp = request.form['otp']
        
        if 'otp' in session and str(session['otp']) == otp:
            return redirect(url_for('newpwd'))  # OTP is correct, redirect to password reset
        else:
            flash("Invalid OTP.")
            return redirect(url_for('getemail'))

    return render_template('validate_otp.html')

@app.route('/staff_login/forgot/validate/otp/reset_password', methods=['GET', 'POST'])
def newpwd():
    if request.method == 'POST':
        pwd = request.form['new_password']
        cpwd = request.form['confirm_password']

        if pwd == cpwd:
            hashed_pwd = bcrypt.generate_password_hash(pwd).decode('utf-8')
            staff_check = Staff.query.filter_by(Email=session.get('email')).first()  # Fetch staff by stored email

            if staff_check:
                staff_check.Password = hashed_pwd
                db.session.commit()
                flash("Password changed successfully.")
                  # Clear the OTP and email from the session
                session.pop('otp', None)
                session.pop('email', None)
                

                return redirect(url_for('staff_login'))
        else:
            flash("Passwords do not match.")
    
    return render_template('reset_password.html')


@app.route('/staff_dashboard/upload_marks', methods=['POST'])
def upload_marks():
    # Retrieve form data
   
    selected_class = request.form.get('class_year')
    academic_year = request.form.get('academic_year')
    subject = request.form.get('subject')
    csv_file = request.files['csv_file']

    # Ensure the uploaded file is a CSV
    if csv_file and csv_file.filename.endswith('.csv'):
        filename = secure_filename(csv_file.filename)
        csv_file.save(os.path.join('uploads', filename))  # Save the CSV file

        # Process the CSV file
        with open(os.path.join('uploads', filename), 'r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header row

            for row in reader:
                # Assuming CSV structure: RollNumber, Mark
                if row and len(row) >= 2:  # Ensure there are enough columns
                    roll_number = row[0]  # Roll number from CSV
                    mark = row[1]   # Mark from CSV

                    try:
                        mark = int(mark)  # Convert mark to integer
                    except ValueError:
                        flash(f'Invalid mark value for roll number {roll_number}: {mark}', 'danger')
                        continue  # Skip this row if conversion fails

                    # Find the student by roll_number, class_year, and academic_year
                    student = Students.query.filter_by(
                        roll_number=roll_number,
                        class_year=selected_class,
                        academic_year=academic_year
                    ).first()

                    if student:
                        # Update the relevant subject's mark based on the selected subject
                        if subject == 'Tamil':
                            student.tamil_mark = mark
                        elif subject == 'English':
                            student.english_mark = mark
                        elif subject == 'Maths':
                            student.maths_mark = mark
                        elif subject == 'Science':
                            student.science_mark = mark
                        elif subject == 'Social':
                            student.social_mark = mark
                        else:
                            flash(f'Unknown subject: {subject}', 'danger')
                            continue  # Skip this row if subject is not valid

                        # Add the updated student record to the session
                        db.session.add(student)
                    else:
                        flash(f'Student with roll number {roll_number} not found in class {selected_class} for the academic year {academic_year}.', 'warning')
                        continue

            # Commit the updates to the database
            db.session.commit()
            flash('Marks uploaded successfully!', 'success')
    else:
        flash('Invalid file format! Please upload a CSV file.', 'danger')

    return render_template('staff_dashboard.html')

@app.route('/admin/create_student', methods=['GET','POST'])
def create_student():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        
        name = request.form['name']
        email = request.form['email'] # Ensure email is fetched correctly
        dob = request.form['dob']
        roll_number = request.form['roll_number']
        password = request.form['password']
        class_year=request.form['class_year']
        academic_year=request.form['academic_year']

    # Debug: Print values to see if class_year is being captured
        print("Captured values: ", {
            'name': name,
            'email': email,
            'dob': dob,
            'roll_number': roll_number,
            'password': password,
            'class_year': class_year,
            'academic_year':academic_year  # Check if this is None
        })
        # Hash the password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
         # Check if the student already exists
        existing_student = Students.query.filter_by(roll_number=roll_number).first()
        if existing_student:
            flash('Student with this Roll Number already exists!')
        else:
            new_student = Students(name=name, email=email, dob=dob,roll_number=roll_number, password=hashed_password,class_year=class_year, academic_year=academic_year)
            # Add to the database
            db.session.add(new_student)
            db.session.commit()
            flash('Student created successfully!')
        return redirect(url_for('admin_student_manage'))
    
    return render_template('create_student.html')

@app.route('/admin/update', methods=['GET', 'POST'])
def update_student():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        roll_num = request.form['roll_number']
        student = Students.query.filter_by(roll_number=roll_num).first()
        if student:
            # Update only the fields that are filled
            if request.form['name']:
                student.name = request.form['name']
            if request.form['dob']:
                student.dob = request.form['dob']  # Parsing date
            if request.form['class_year']:
                student.class_year = request.form['class_year']
            if request.form['academic_year']:
                student.academic_year = request.form['academic_year']     

            db.session.commit()
            flash('Student details updated successfully!')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Oops! Student not found!')

    # For GET request, fetch the student data to pre-fill the form
    roll_num = request.args.get('roll_number')  # Get roll number from query parameters
    student = Students.query.filter_by(roll_number=roll_num).first()  # Fetch student data
    if student:
        return render_template('update_student.html', student=student)  # Pass student data to the template
    else:
        flash('Student not found!')
        return redirect(url_for('admin_student_manage'))

@app.route('/admin/delete_student/<string:student_id>', methods=['GET', 'POST'])
def delete_student(student_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    student = Students.query.filter_by(student_id=student_id).first()
    if student:
        db.session.delete(student)  # Delete the student record
        db.session.commit()
        flash('Student record deleted successfully!')
    else:
        flash('Student not found!')

    return redirect(url_for('admin_student_manage'))


# Admin logout route
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('admin', None)  # Remove the admin session
    return redirect(url_for('home'))  # Redirect to the login page

# Student logout route
@app.route('/login/logout', methods=['POST'])
def student_logout():
    session.pop('student', None)  # Remove the student session
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, port=8000)

