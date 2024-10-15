from flask import Flask, render_template, redirect, session, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt


app = Flask(__name__)
bcrypt = Bcrypt(app)

app.config['SECRET_KEY'] = 'school_management'

# Database Configuration - MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost/school_management'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Added primary key
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
@app.route('/', methods=['GET','POST'])
def admin_creation():
    
    if request.method == 'POST':
        print(request.form)
        uname = request.form.get('username')
        email=request.form.get('email')
        pwd = request.form.get('password')

        # Hash the password and create the admin
        hashed_password = bcrypt.generate_password_hash(pwd).decode('utf-8')
        new_admin = Admin(username=uname,email=email,password=hashed_password)
    
        db.session.add(new_admin)
        db.session.commit()

        flash('Admin created successfully!')
    return render_template('create_admin.html')

if __name__=='__main__':
    app.run(debug=True)