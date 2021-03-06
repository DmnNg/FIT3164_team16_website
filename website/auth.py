from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User, Patient, Result
# coverts password so that it does not store password as plain text, generates a hash
# the password that is typed in MUST be equal to the hash that is stored
# sha256 is the hashing algorithm
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user

from keras.models import load_model
from keras.preprocessing import image

import os



auth = Blueprint('auth', __name__)

# Login Route
# This route appears on the login page of the website
# It checks if the login details are correct
# Input: Email and Password
# Output: Redirects users to the home page
# Error: Flashes an error and returns the user to the login page again
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')
    return render_template("login.html", user=current_user)

# Logout Route
# This route appears on the home screen where the user is able to log out
# Input: Log out Button
# Output: Redirects user to login page
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

# Sign up Route
# This route appears on the Login page where the user is able to sign up
# Input: Email, Name, Password
# Output: Redirects user to the home page
# Error: Returns user to the sign up page with appropraite error messages if inputs are not satisfied
@auth.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
	if request.method == 'POST':
		email = request.form.get('email')
		first_name = request.form.get('firstName')
		password1 = request.form.get('password1')
		password2 = request.form.get('password2')

		user = User.query.filter_by(email=email).first()
		if user:
			flash('Email already exists.', category='error')
			return render_template("sign_up.html", user=current_user)
		if len(email) < 4:
			flash('Email must be greater than 3 characters.', category='error')
			return render_template("sign_up.html", user=current_user)
		elif len(first_name) < 2:
			flash('First name must be greater than 1 character.', category='error')
			return render_template("sign_up.html", user=current_user)
		elif password1 != password2:
			flash('Passwords don\'t match.', category='error')
			return render_template("sign_up.html", user=current_user)
		elif len(password1) < 7:
			flash('Password must be at least 7 characters.', category='error')
			return render_template("sign_up.html", user=current_user)
		else:
			new_user = User(email=email, first_name=first_name, password=generate_password_hash(password1, method='sha256'))
			db.session.add(new_user)
			db.session.commit()
			login_user(new_user, remember=True)
			flash('Account created!', category='success')
			return redirect(url_for('views.home'))

	return render_template("sign_up.html", user=current_user)

# Create patient route
# This route appears on as a button on the navigation bar where the user is able to create a patient
# Input: Name
# Output: Saves patient in database and patient can be seen on the home page
# Error: If the first name is not at least 1 character long, the user returns to the create patient page
@auth.route('/create_patient', methods=['GET', 'POST'])
@login_required
def create_patient():
	if request.method == 'POST':
		first_name = request.form.get('firstName')
		if len(first_name) < 2:
			flash('First name must be greater than 1 character.', category='error')
		else: 
			new_patient = Patient(first_name=first_name, user_id=current_user.id)
			db.session.add(new_patient)
			db.session.commit()
			flash('Patient created!', category='success')
			return redirect(url_for('views.home'))

	return render_template("create_patient.html", user=current_user)

# Result history route
# This route appears on the home page where the user is able to see the patients result history
@auth.route('/result_history/<int:patient_id>')
@login_required
def result_history(patient_id):
	patient = Patient.query.get_or_404(patient_id)
	return render_template("result_history.html", patient=patient, user=current_user)


# Save result route
# This route appears on the upload image page and ensures that the details the user uploads and saved are correct
# Input: Selection of patients, cancer image, additional notes
# Output: Saved result to selected patient
# Error: If requirements are not met, appropriate error messages are flashed to the user 
@auth.route('/save_result', methods=['GET', 'POST'])
@login_required
def save_result():
	if request.method == 'POST':
		# select a patient ID
		selected_patient = request.form.get('patientID')
		
		# percentage of the cancer image
		cancer_percentage = request.form.get('percentage')
		
		# note created by user
		add_note = request.form.get('note')
		

		# user has not uploaded image, redirect to home page
		if cancer_percentage==" ":
			flash('No Image Submitted', category='error')
		else: 
			new_result = Result(note=add_note, percentage=cancer_percentage, patient_id=selected_patient)
			db.session.add(new_result)
			db.session.commit()
			flash('Saved Result', category='success')
			return redirect(url_for('views.home'))
	return render_template("upload_image.html", user=current_user)


# Upload Image route
# Takes the user to the upload image page
@auth.route('/upload_image', methods=['GET', 'POST'])
@login_required
def upload_image():
	return render_template("upload_image.html", user=current_user)


########################
# machine learning model
########################

# loads the model
model = load_model('best_model.h5')

# converts the input image into the correct image size for the model
def predict_label(img_path):
	i = image.load_img(img_path, target_size=(200,200))
	i = image.img_to_array(i) 
	i = i.reshape(1, 200,200,3)
	p = model.predict(i)
	return p

# Get output route
# Takes the image that the user has uploaded and puts it through the machine learning model
# Input: Cancer Image
# Output: Result from the machine learning model
# Error: If requirements are not met, appropriate error messages are flashed to the user 
@auth.route("/get_output", methods = ['GET', 'POST'])
@login_required
def get_output():
	if request.method == 'POST':
		if request.files['my_image'].filename == '':
			flash('No Image Selected', category='error')
			return render_template("upload_image.html", user=current_user)
		
		list_ext = ['.jpg', '.png', '.jpeg']
		upload_ext = os.path.splitext(request.files['my_image'].filename)
		if upload_ext[1] not in list_ext:
			flash('File must be .jpg, .jpeg, or .png', category='error')
			return render_template("upload_image.html", user=current_user)
			
		img = request.files['my_image']

		show_image = "static/" + img.filename

		img_path = "website/static/" + img.filename	
		img.save(img_path)

		p = predict_label(img_path)
		labels = ['MSI', 'MSS']

		if p[0][0]>p[0][1]:
			pred_perc = str(round(p[0][0] * 100, 2)) + '%'
			# print(pred_perc)
			pred_lab = labels[0]

		if p[0][0]<p[0][1]:
			pred_perc = str(round(p[0][1] * 100, 2)) + '%'
			# print(pred_perc)
			pred_lab = labels[1]
	return render_template("upload_image.html", user=current_user, pred_perc = pred_perc, pred_lab = pred_lab, show_image = show_image)
