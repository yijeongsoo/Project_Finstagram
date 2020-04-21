#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect, send_file
import os
import uuid
import hashlib
import pymysql.cursors
from functools import wraps
import time

#Path for image file
IMAGES_DIR = os.path.join(os.getcwd(), "images")


#Initialize the app from Flask
app = Flask(__name__)

#Configure MySQL
conn = pymysql.connect(host='localhost',
                       port = 3306,
                       user='root',
                       password='',
                       db='FlaskDemo',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor,
                       autocommit=True)


def login_required(f):
    @wraps(f)
    def dec(*args, **kwargs):
        if not "username" in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return dec


#Define a route to hello function
@app.route('/')
def hello():
    return render_template('index.html')

#Define route for login
@app.route('/login')
def login():
    return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM user WHERE username = %s and password = %s'
    cursor.execute(query, (username, password))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    cursor.close()
    error = None
    if(data):
        #creates a session for the the user
        #session is a built in
        session['username'] = username
        return redirect(url_for('home'))
    else:
        #returns an error message to the html page
        error = 'Invalid login or username'
        return render_template('login.html', error=error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    #grabs information from the forms
    username = request.form['username']
    password = request.form['password']

    #cursor used to send queries
    cursor = conn.cursor()
    #executes query
    query = 'SELECT * FROM user WHERE username = %s'
    cursor.execute(query, (username))
    #stores the results in a variable
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #If the previous query returns data, then user exists
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO user VALUES(%s, %s)'
        cursor.execute(ins, (username, password))
        conn.commit()
        cursor.close()
        return render_template('index.html')

@app.route('/home')
@login_required
def home():
    return render_template('home.html', username = session['username'])

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

@app.route('/create_closeFriendGroup')
@login_required
def create_closeFriendGroup():
    return render_template('create_closeFriendGroup.html')


@app.route('/friendGroup_auth',methods=['POST'])
@login_required
def friendGroup_auth():
    username = session['username']
    groupName = request.form['groupName']
    cursor0 = conn.cursor()
    query0 = 'SELECT * FROM closeFriendGroup WHERE groupName = %s AND groupOwner = %s'
    cursor0.execute(query0, (groupName, username))
    data = cursor0.fetchone()
    if (data): #Meaning the group already exists
        error = "You already have this closeFriendGroup"
        return render_template('create_closeFriendGroup.html', error=error)
    else:
        cursor1 = conn.cursor()
        query1 = 'INSERT INTO closeFriendGroup VALUES(%s, %s)'
        cursor1.execute(query1, (groupName, username))
        
        cursor2 = conn.cursor()
        query2 = 'INSERT INTO belong VALUES(%s, %s, %s)'
        cursor2.execute(query2,(groupName, username, username))
        return redirect(url_for('home'))

@app.route('/add_friend')
@login_required
def add_friend():
    username = session['username']
    #Query to find all Friend Groups
    cursor = conn.cursor();
    query = 'SELECT DISTINCT groupName FROM closefriendgroup WHERE groupOwner = %s'
    cursor.execute(query,(username))
    data = cursor.fetchall()
    cursor.close()
    return render_template('add_friend.html', user_list=data, username=username)

@app.route('/add_friend_auth', methods=['POST', 'GET'])
@login_required
def add_friend_auth():    
    username = session['username']
    friendName = request.form['friendName']
    groupName = request.form['groupName']

    #cursor used to find if friend is there
    cursor = conn.cursor()
    #executes query
    query = 'SELECT username FROM user WHERE username = %s'
    cursor.execute(query, (friendName))
    #stores the results in a variab\e
    data = cursor.fetchone()
    #use fetchall() if you are expecting more than 1 data row
    error = None
    if(data):
        #If the previous query returns data, then user exists. Now we check if user is already in the group:
        query = 'SELECT username FROM belong WHERE username = %s AND groupName = %s AND groupOwner = %s'
        cursor.execute(query, (friendName, groupName, username))
        data = cursor.fetchone()
        #use fetchall() if you are expecting more than 1 data row
        error = None
        if(data):
            error = "User already in Group!"
            cursor = conn.cursor();
            query = 'SELECT DISTINCT groupName FROM closefriendgroup WHERE groupOwner = %s'
            cursor.execute(query,(username))
            data = cursor.fetchall()
            return render_template('add_friend.html', user_list = data, error = error)
        else:
            ins = 'INSERT INTO belong VALUES(%s, %s, %s)'
            cursor.execute(ins, (groupName, username, friendName))
            conn.commit()
            cursor.close()
            return redirect(url_for('home'))
    else:
        error = "Invalid username"
        cursor = conn.cursor();
        query = 'SELECT DISTINCT groupName FROM closefriendgroup WHERE groupOwner = %s'
        cursor.execute(query,(username))
        data = cursor.fetchall()
        return render_template('add_friend.html', user_list=data,    error = error)

@app.route("/upload", methods=["GET"])
@login_required
def upload():
    return render_template("upload.html")

@app.route("/images", methods=["GET"])
@login_required
def images():
    username = session['username']
    query0 = "SELECT DISTINCT photoID, photoOwner, filepath, timestamp, allFollowers FROM photo, follow WHERE (allFollowers = 1 AND photoOwner=followeeUsername AND followerUsername=%s) OR photoID IN (SELECT photoID FROM share NATURAL JOIN belong WHERE username = %s) OR photoOwner = %s ORDER BY timestamp DESC"
    with conn.cursor() as cursor0:
        cursor0.execute(query0,(username, username, username))
    data0 = cursor0.fetchall()
    query1 = "SELECT photoID, username FROM tag WHERE acceptedTag = 1"
    with conn.cursor() as cursor1:
        cursor1.execute(query1)
    data1 = cursor1.fetchall()
    return render_template("images.html", images=data0, taggees=data1)

@app.route("/image/<image_name>", methods=["GET"])
def image(image_name):
    image_location = os.path.join(IMAGES_DIR, image_name)
    if os.path.isfile(image_location):
        return send_file(image_location, mimetype="image/jpg")

@app.route("/upload_image", methods=["POST"])
@login_required
def upload_image():
    username = session['username']

    if request.files:
        image_file = request.files.get("imageToUpload", "")
        image_name = image_file.filename

        if (request.form['allFollowers'] == 'private'):
            allFollow = False
        else:
            allFollow = True

        filepath = os.path.join(IMAGES_DIR, image_name)
        image_file.save(filepath)
        query = "INSERT INTO photo (photoOwner, timestamp, filePath, allFollowers) VALUES (%s, %s, %s, %s)"
        with conn.cursor() as cursor:
            cursor.execute(query, (username, time.strftime('%Y-%m-%d %H:%M:%S'), image_name, allFollow))
        message = "Image has been successfully uploaded."

        if (allFollow == False):
            query0 = 'SELECT photoID FROM photo WHERE filePath = %s'
            cursor0 = conn.cursor()
            cursor0.execute(query0, (image_name))
            data0 = cursor0.fetchone()
            
            query1 = 'SELECT * FROM closeFriendGroup WHERE groupOwner = %s'
            cursor1 = conn.cursor()
            cursor1.execute(query1, (username))
            data1 = cursor1.fetchall()
            message = "Image upload successful"
            return render_template("share.html", photoID=data0, group_data=data1)
        else:    
            return render_template("upload.html", message = message)
    else:
        message = "Failed to upload image."
        return render_template("upload.html", message=message)

@app.route("/share", methods=["POST"])
@login_required
def share():
    username = session['username']
    groupName = request.form['groupName']
    
    query0 = 'SELECT photoID FROM photo WHERE allFollowers = 0 AND (photoID) NOT IN (SELECT photoID FROM share)'
    cursor0 = conn.cursor()
    cursor0.execute(query0)
    data = cursor0.fetchone()
    photoID = data['photoID']

    query = "INSERT INTO share VALUES (%s, %s, %s)"
    cursor = conn.cursor()
    cursor.execute(query, (groupName, username, photoID))
    cursor.close()
    message = "Image upload successful"
    return render_template("upload.html", message=message)

@app.route("/send_request", methods=["GET"])
@login_required
def send_request():
    return render_template("send_request.html")

@app.route("/send_request_auth", methods=['POST', 'GET'])
@login_required
def send_request_auth():
    username = session['username']
    acceptedFollow = False
    followName = request.form['followName']

    if (username == followName):
        message = "You cannot follow yourself."
        return render_template("send_request.html", message=message)

    cursor1 = conn.cursor();
    check1 = 'SELECT username FROM user WHERE username = %s'
    cursor1.execute(check1, (username))
    data = cursor1.fetchone()
    if (data):
        check2 = 'SELECT followerUsername, followeeUsername FROM follow WHERE followerUsername = %s AND followeeUsername = %s'
        cursor2 = conn.cursor();
        cursor2.execute(check2, (username, followName))
        data2 = cursor2.fetchall()
        if(data2):
            message = "You already sent this user a follow request."
            return render_template("send_request.html", message=message)
        else:
            cursor = conn.cursor()
            query = 'INSERT INTO follow VALUES(%s, %s, %s)'
            cursor.execute(query, (username, followName, acceptedFollow))
            message = "Request has been successfully sent"
            return render_template("send_request.html", message=message)
    else:
        message = "Invalid username"
        return render_template("send_request.html", message=message)


@app.route("/manage_follow", methods=["GET"])
@login_required
def manage_follow():
    return render_template("manage_follow.html")

@app.route("/requests_received", methods=["GET"])
@login_required
def requests_received():
    username = session['username']
    query = "SELECT * FROM follow WHERE followeeUsername = %s AND acceptedFollow = 'False'"
    with conn.cursor() as cursor:
        cursor.execute(query,(username))
    data = cursor.fetchall()
    return render_template("requests_received.html", requests=data)

@app.route("/requests_received_auth", methods=['POST', 'GET'])
@login_required
def requests_received_auth():
    username = session['username']
    followName = request.args['followerUsername']
    accept = request.args['Yes']
    if (accept == 'Yes'):
        query = "UPDATE follow SET acceptedFollow = 1 WHERE followerUsername = %s AND followeeUsername = %s"
        with conn.cursor() as cursor:
            cursor.execute(query, (followName, username))
        message = "Request has been successfully accepted"
        query = "SELECT * FROM follow WHERE followeeUsername = %s AND acceptedFollow = 'False'"
        with conn.cursor() as cursor:
            cursor.execute(query,(username))
        data = cursor.fetchall()
        return render_template("requests_received.html", message=message, requests=data)


@app.route("/manage_tag", methods=["POST","GET"])
@login_required
def manage_tag():
    username = session['username']
    query = "SELECT filepath, photoID, username, acceptedTag FROM tag NATURAL JOIN photo WHERE username = %s AND acceptedTag = 'False'"
    with conn.cursor() as cursor:
        cursor.execute(query,(username))
    data = cursor.fetchall()
    return render_template("manage_tag.html", requests = data)

@app.route("/manage_tag_auth", methods=["POST","GET"])
@login_required
def manage_tag_auth():
    username = session['username']
    query2 = "SELECT photoID FROM tag where username = %s AND acceptedTag = 0"
    cursor2 = conn.cursor()
    cursor2.execute(query2, (username))
    data2 = cursor2.fetchone()
    photoID = data2['photoID']
    query0 = "UPDATE tag SET acceptedTag = 1 WHERE username = %s AND photoID = %s"
    cursor0 = conn.cursor()
    cursor0.execute(query0, (username, photoID))
    cursor0.close()
    query1 = "SELECT filepath, photoID, username, acceptedTag FROM tag NATURAL JOIN photo WHERE username = %s AND acceptedTag = 'False'"
    message = "Tag request Accepted"
    with conn.cursor() as cursor1:
        cursor1.execute(query1,(username))
    data = cursor1.fetchall()
    return render_template("manage_tag.html", requests=data, message = message)

@app.route("/tag_photo", methods=["POST","GET"])
@login_required
def tag_photo():
    photoID = request.form['photoID']
    return render_template("tag_photo.html", photoID = photoID)

@app.route("/tag_auth", methods=["POST","GET"])
@login_required
def tag_auth():
    username = session['username']
    taggee = request.form['tagName']
    photoID = request.form['photoID']
    check0 = 'SELECT * FROM tag WHERE username = %s AND photoID = %s'
    cursor0 = conn.cursor()
    cursor0.execute(check0, (taggee, photoID))
    data0 = cursor0.fetchone()
    if (data0):
        message = "Already tagged in this photo! Try a different person."
        return render_template("tag_photo.html", photoID = photoID, message = message)
    else:
        check1 = "SELECT username FROM user WHERE username = %s"
        cursor1 = conn.cursor()
        cursor1.execute(check1, (username))
        data1 = cursor1.fetchone()
        if (not data1):
            message = "Invalid Username! Try a different person."
            return render_template("tag_photo.html", photoID = photoID, message = message)
        if (username == taggee):
            query = "INSERT INTO tag VALUES (%s, %s, 1)"
            cursor = conn.cursor()
            cursor.execute(query, (taggee, photoID))
            message = "Tag successful"
            return render_template("tag_photo.html", photoID = photoID, message = message)
        check2 = 'SELECT * FROM belong, follow, photo WHERE (followerUsername = %s AND photoID = %s AND followeeUsername = photoOwner) OR (photoOwner = %s) OR username IN (SELECT username FROM belong NATURAL JOIN share WHERE username = %s AND photoID = %s)'
        cursor2 = conn.cursor()
        cursor2.execute(check2, (taggee, photoID, taggee, taggee, photoID))
        data2 = cursor2.fetchall()
        if (not data2):
            message = "You do not have access to tag this person"
            return render_template("tag_photo.html", photoID = photoID, message = message)
        else:
            query = "INSERT INTO tag VALUES (%s, %s, 0)"
        cursor = conn.cursor()
        cursor.execute(query, (taggee, photoID))
        message = "Tag request sent."
        return render_template("tag_photo.html", photoID = photoID, message = message)
    cursor0.close()
    cursor1.close()
    cursor.close()



app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    if not os.path.isdir("images"):
        os.mkdir(IMAGES_DIR)
    app.run('127.0.0.1', 5000, debug = True)
