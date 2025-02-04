
from flask import Blueprint,render_template,request,flash,redirect, url_for,session,jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from . import db   ##means from __init__.py import db
from flask_login import login_user, login_required, logout_user, current_user
from .models import User, Finger,UserLog
from datetime import datetime
import time,json
import paho.mqtt.client as mqtt

auth = Blueprint('auth',__name__)


@auth.route('/login',methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if user.email ==  email:
                if check_password_hash(user.password,password):
                    flash('Logged in successfully!', category='success')
                    login_user(user, remember=True)
                    return redirect(url_for('views.home'))
                else:
                    flash('Invalid credentials', category='error')
        else:
            flash('Invalid credentials', category='error')
    return render_template("login.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/signup',methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters', category='error')
        elif len(name) < 2:
            flash('Name must be greater than 1 character', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match', category='error')
        elif len(password1) < 8 or len(password1) > 12:
            flash('Password must have 8-12 characters', category='error')
        else:
            new_user = User(email=email, name=name, password=generate_password_hash(
                password1,method='pbkdf2:sha256'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('User created!',category = 'success')
            return redirect(url_for('views.home'))
        

    return render_template("signup.html", user=current_user)

@auth.route('/')
@login_required
def index():
    return render_template('home.html', user=current_user)
    
@auth.route('/ManageUsers')
@login_required
def manage_users():
    return render_template('manage_users.html', user=current_user)

@auth.route('/UsersLog')
@login_required
def users_log():
    return render_template('users.html', user=current_user)


# AWS IoT and Database Configuration
AWS_IOT_ENDPOINT = "a368shk9lnz2qk-ats.iot.ap-south-1.amazonaws.com"  # replace with your AWS IoT endpoint
AWS_TOPIC_PUBLISH = "user/fingerprint/request"
AWS_TOPIC_SUBSCRIBE = "user/fingerprint/response"

# Global variable to store fingerprint data
fingerprint_data = None

# MQTT Client setup for AWS IoT
mqtt_client = mqtt.Client()

# Connect to AWS IoT with certificate-based authentication
mqtt_client.tls_set(ca_certs="certificates\AmazonRootCA1.pem",
                certfile="certificates\84e570e386037d61ac618ca7796533de5f53484cfb5baff93d918668488a35a5-certificate.pem.crt",
                keyfile="certificates\84e570e386037d61ac618ca7796533de5f53484cfb5baff93d918668488a35a5-private.pem.key")
mqtt_client.connect(AWS_IOT_ENDPOINT, 8883, 60)

# Function to handle incoming MQTT messages
def on_message(client, userdata, message):
    global fingerprint_data
    try:
        # Decode the payload and update the global fingerprint_data
        fingerprint_data = json.loads(message.payload.decode())
        print("Received response data:", fingerprint_data)
    except json.JSONDecodeError:
        print("Failed to decode JSON response:", message.payload.decode())
    



@auth.route('/add_user', methods=['POST'])
def add_user():
    global fingerprint_data 
    data = request.get_json()
    new_user = Finger(
        username=data['username'],
        registernumber=data['registernumber'],
        email=data['email'],
        time_in=data['time_in'],
        gender=data['gender'],
        checkindate=datetime.now().strftime('%Y-%m-%d')
    )
     # Publish user information to AWS IoT Core to request fingerprint
    request_payload = {
        "username": "enroll"
    }
    mqtt_client.publish(AWS_TOPIC_PUBLISH, json.dumps(request_payload))
    print("Published fingerprint request:", request_payload)

    # Wait for fingerprint data response
    mqtt_client.on_message = on_message
    mqtt_client.subscribe(AWS_TOPIC_SUBSCRIBE)
    mqtt_client.loop_start()  # Start MQTT client loop to handle messages asynchronously


    start_time = time.time()
    while fingerprint_data is None and time.time() - start_time < 20:
        time.sleep(0.1)  # Polling loop to check for response
    if fingerprint_data is None:
        return jsonify({"message": "Fingerprint data not received in time"}), 408
    data = request.get_json()
    # new_user = Finger(
    #     username=data['username'],
    #     registernumber=data['registernumber'],
    #     email=data['email'],
    #     time_in=data['time_in'],
    #     gender=data['gender'],
    #     checkindate=datetime.now().strftime('%Y-%m-%d'),
    #     template=fingerprint_data
    # )
    #new_user = Finger(template=fingerprint_data)

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User added successfully!"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error adding user: " + str(e)}), 500
    

@auth.route('/update_user', methods=['POST'])
def update_user():
    # Get user data from request
    data = request.json
    username = data.get('username')
    registernumber = data.get('registernumber')
    email = data.get('email')
    gender = data.get('gender')


    # Find the user and update their details
    try:
        user = Finger.query.filter_by(registernumber=registernumber).first()


        if user:
            user.username = username
            user.registernumber = registernumber
            user.email = email
            user.gender = gender
            print(f"Attempting to update user with register number: {Finger.username}")  # Debug line

            db.session.commit()
            return jsonify({"success": True, "message": "User updated successfully!"})
        else:
            print("No user found.")  # Debug line
            return jsonify({"success": False, "message": "User not found."}), 404

    except Exception as e:
        db.session.rollback()
        print(f"Error updating user: {e}")
        return jsonify({"success": False, "message": "Failed to update user."}), 500
    

@auth.route('/delete_user', methods=['POST'])
@login_required
def delete_user():
    data = request.json
    registernumber = data.get('registernumber')
    print("reg num",registernumber)
    try:
        # Find the user by registernumber
        user = Finger.query.filter_by(registernumber=registernumber).first()
        print(f"Attempting to delete user with register number: {registernumber}")  # Debug line

        if user:
            db.session.delete(user)  # Delete the user from the session
            db.session.commit()  # Commit the changes to the database
            return jsonify({"success": True, "message": "User deleted successfully!"}), 200
        else:
            return jsonify({"success": False, "message": "User not found."}), 404

    except Exception as e:
        db.session.rollback()  # Rollback if there's an error
        print(f"Error deleting user: {e}")
        return jsonify({"success": False, "message": "Failed to delete user."}), 500


@auth.route('/user_logs', methods=['GET', 'POST'])
@login_required
def user_logs():
    selected_date = request.form.get('date_sel') or datetime.now().date().strftime("%Y-%m-%d")

    # Fetch logs from the database based on the selected date
    logs = Finger.query.filter_by(checkindate=selected_date).order_by(Finger.id.desc()).all()

    # If the request is AJAX (coming from the periodic JavaScript fetch), respond with a partial template
    if request.is_json:
        return jsonify(render_template('partials/user_logs_table.html', logs=logs))

    return render_template('users.html', logs=logs, selected_date=selected_date, user=current_user)
