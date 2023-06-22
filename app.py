######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

###################################################
# Boston University CS 460
# Edits made by Sinforiano Terada and Miles Clemons
# Last Edit on 03/03/2023
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = ''  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT psword FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT psword FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		firstname=request.form.get('firstname')
		lastname=request.form.get('lastname')
		dob=request.form.get('dob')
		password=request.form.get('password')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, f_name, l_name, dob, psword) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}')".format(email, firstname, lastname, dob, password)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print("couldn't find all tokens")
		#return render_template('register.html', errormessage='Error. Email already exists.')
		return flask.redirect(flask.url_for('register'))

def getUsersPhotos(uid):
	cursor = conn.cursor()
	#cursor.execute("SELECT p_data, photo_id, caption FROM Pictures WHERE u_id = '{0}'".format(uid))
	cursor.execute('''SELECT p.p_data, p.photo_id, p.caption
					  FROM Pictures p 
					  WHERE u_id = %s''', uid)
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT u_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

@app.route('/profile', methods=['GET', 'POST'])
@flask_login.login_required
def protected():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		return render_template("hello.html")
	else:
		friends=get_user_friends(uid)
		friendrecs = getfriendrecs(friends, uid)
		usetags = you_may_also_like(uid)
		if usetags == None:
			return render_template("hello.html", name=flask_login.current_user.id, message="Here's your profile",
											 photos=getUsersPhotos(uid), base64=base64, user=get_user_data(uid), 
											 friends=friends, albums=get_user_album_data(uid), tags=get_user_tags(uid),
											 friendrecs=friendrecs, maylikemessage="Add tags to your photos so we can recommend photos based off your most popular tags.")
		else:

			pid = usetags[0]
			print("The photo id is " + str(pid))
			#may_like = get_picture_data(pid)
			#print(may_like)
			return render_template("hello.html", name=flask_login.current_user.id, message="Here's your profile",
											 	photos=getUsersPhotos(uid), base64=base64, user=get_user_data(uid), 
											 	friends=friends, albums=get_user_album_data(uid), tags=get_user_tags(uid),
											 	friendrecs=friendrecs, maylike=get_picture_data(pid))

def getfriendrecs(friends, uid):
	friend_user_ids = []
	friend_recs = []
	for i in friends:
		friend_user_ids.append(i[1])
	for i in range(len(friend_user_ids)):
		next_recs = get_user_friends(friend_user_ids[i])
		for i in next_recs:
			if(i[1] != uid):
				friend_recs.append(i)
		if len(friend_recs) >= 5:
			break
	return friend_recs
	
def you_may_also_like(uid):
	cursor = conn.cursor()
	cursor.execute('''SELECT t.descript, COUNT(t.tag_id)
					  FROM Tagged ta, Tags t, Pictures p
					  WHERE ta.photo_id = p.photo_id AND ta.tags_id = t.tag_id AND p.u_id = %s
					  GROUP BY t.descript
					  ORDER BY COUNT(t.tag_id) DESC''', uid)
	UserTags = cursor.fetchall()
	print(UserTags)
	NumTags = len(UserTags)
	print(NumTags)
	TagList = [None] * NumTags
	i = 0
	for tagtuple in UserTags:
		TagList[i] = tagtuple[0]
		i += 1

	FirstTag = ""
	SecondTag = ""
	ThirdTag = ""
	if NumTags >= 1:
		FirstTag = TagList[0]
	if NumTags >= 2:
		SecondTag = TagList[1]
	if NumTags >= 3:
		ThirdTag = TagList[2]

	# For Console Testing
	print(FirstTag)
	print(SecondTag)
	print(ThirdTag)		

	# Three tags, query all three
	if FirstTag != "" and SecondTag != "" and ThirdTag != "":
		result = three_tag_match_query(FirstTag, SecondTag, ThirdTag, uid)
		if result != None:
			return result
	elif FirstTag != "" and SecondTag != "" and ThirdTag == "":
		result = two_tag_match_query(FirstTag, SecondTag, uid)
		if result != None:
			return result
	elif FirstTag != "" and SecondTag == "" and ThirdTag == "":
		result = one_tag_match_query(FirstTag, uid)
		if result != None:
			return result
	else:
		return None

def three_tag_match_query(FirstTag, SecondTag, ThirdTag, uid):
	cursor = conn.cursor()
	cursor.execute('''SELECT tone.photo_id, tone.tag_id, tone.descript
	                  FROM (
						SELECT ttwo.photo_id, ttwo.tag_id, ttwo.descript
						FROM (
							SELECT ta.photo_id, t.tag_id, t.descript, p.u_id
							FROM Tagged ta, Tags t, Pictures p
							WHERE t.tag_id = ta.tags_id AND ta.photo_id = p.photo_id AND p.u_id <> %s AND t.descript = %s
						) AS ttwo
						WHERE ttwo.descript = %s
					  ) AS tone
					  WHERE tone.descript = %s''', (uid, FirstTag, SecondTag, ThirdTag))				  
	result = cursor.fetchone()
	if result == None:
		return two_tag_match_query(FirstTag, SecondTag, uid)
	else:
		return result
		

def two_tag_match_query(FirstTag, SecondTag, uid):
	cursor.execute('''SELECT tone.photo_id, tone.tag_id, tone.descript
	                  FROM (
						SELECT ta.photo_id, t.tag_id, t.descript, p.u_id
						FROM Tagged ta, Tags t, Pictures p
						WHERE t.tag_id = ta.tags_id AND ta.photo_id = p.photo_id AND p.u_id <> %s AND t.descript = %s
					  ) AS tone
					  WHERE tone.descript = %s''', (uid, FirstTag, SecondTag))
	result = cursor.fetchone()
	if result == None:
		return one_tag_match_query(FirstTag, uid)
	else: 
		return result

def one_tag_match_query(FirstTag, uid):
	cursor.execute('''SELECT ta.photo_id, t.tag_id, t.descript, p.u_id
					  FROM Tagged ta, Tags t, Pictures p
					  WHERE t.tag_id = ta.tags_id AND ta.photo_id = p.photo_id AND p.u_id <> %s AND t.descript = %s''', (uid, FirstTag))
	result = cursor.fetchone()
	print(result)
	return result



#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def handle_tags(tags_to_insert, photo_id):
	for i in tags_to_insert:
		cursor.execute('''SELECT T.tag_id FROM Tags T WHERE T.descript = %s''',(i))
		tags_found = cursor.fetchall()
		print(len(tags_found))
		if len(tags_found) > 0:
			tag_id = tags_found[0]
			cursor.execute("INSERT INTO Tagged (photo_id, tags_id) VALUES (%s,%s)",(photo_id,tag_id))
			conn.commit()
		else:
			cursor.execute("INSERT INTO Tags (descript) VALUES (%s)", (i))
			conn.commit()
			tag_inserted = cursor.lastrowid
			cursor.execute("INSERT INTO Tagged (photo_id,tags_id) VALUES (%s,%s)", (photo_id,tag_inserted))
			conn.commit()


@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		photo_data =imgfile.read()
		oldaid = request.form.get('oldalbum')
		new_album = request.form.get('newa')
		cursor = conn.cursor()
		if (oldaid == '0' and new_album == "") or (oldaid != '0' and new_album != ""):
			return display_album_form_list_error()
		if new_album != "":
			cursor.execute('''INSERT INTO Albums (album_name, userid) VALUES (%s, %s)''', (new_album, uid))
			conn.commit()
			cursor.execute('''SELECT a.a_id	
							  FROM Albums a
							  WHERE a.album_name = %s AND a.userid = %s''', (new_album, uid))
			oldaid = cursor.fetchone()

		cursor.execute('''INSERT INTO Pictures (p_data, u_id, caption, a_id) VALUES (%s, %s, %s, %s )''', (photo_data, uid, caption, oldaid))
		conn.commit()

		photo_inserted_id = cursor.lastrowid
	
		tags = request.form.get('tags')

		if tags != "":
			tags = tags.lower()
			tags_to_insert = tags.split()

			handle_tags(tags_to_insert, photo_inserted_id)

		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return display_album_form_list(uid)

def display_album_form_list(uid):
	cursor = conn.cursor()
	cursor.execute('''SELECT a.a_id, a.album_name
					  FROM  Albums a
					  WHERE a.userid = %s''', uid)
	OldAlbums = cursor.fetchall()
	return render_template('upload.html', oldalbums=OldAlbums)

def display_album_form_list_error():
	cursor = conn.cursor()
	cursor.execute('''SELECT a.a_id, a.album_name
						  FROM  Albums a''')
	OldAlbums = cursor.fetchall()
	return render_template('upload.html', oldalbums=OldAlbums, message="Error Uploading. Must Choose Existing Album or Create New Album.")

def create_new_album_from_form():
	return render_template('upload.html', newalbum="True")

#end photo uploading code

def doUserSearch(user):
	cursor = conn.cursor()
	query = "SELECT u.u_id, u.email, u.f_name, u.l_name, u.dob FROM Users u WHERE u.email = %s"
	userFound = cursor.execute(query,(user))
	userFound = cursor.fetchall()
	return userFound

def doTagSearch(tag):
	tagList = tag.split(" ")
	cursor = conn.cursor()
	if len(tagList) > 1:
		tagTup = tuple(tagList)
		query = '''SELECT P.photo_id, P.caption, P.p_data 
		FROM Pictures P JOIN Tagged T ON P.photo_id = T.photo_id JOIN Tags Ta ON T.tags_id = Ta.tag_id
		WHERE Ta.descript IN {0} 
		GROUP BY P.photo_id
		HAVING COUNT(DISTINCT Ta.tag_id) = {1}'''.format(tagTup, len(tagList))
		cursor.execute(query)
		photosToReturn = cursor.fetchall()
	else:
		query = '''SELECT P.photo_id, P.caption, P.p_data 
		FROM Pictures P, Tagged T, Tags Ta 
		WHERE P.photo_id = T.photo_id AND T.tags_id = Ta.tag_id AND Ta.descript = %s'''
		cursor.execute(query, (tagList[0]))
		photosToReturn = cursor.fetchall()
	
	return photosToReturn

def doCommentSearch(comment):
	cursor = conn.cursor()
	commentFound = cursor.execute('''SELECT u.u_id, u.email, u.f_name, u.l_name, u.dob 
	                                 FROM Users u 
									 WHERE u.u_id IN 
									      (SELECT DISTINCT C.c_owner 
										  FROM Comments C 
										  WHERE C.contents = %s 
										  GROUP BY C.c_owner
										  ORDER BY COUNT(C.c_owner) DESC)''',(comment))
	commentFound = cursor.fetchall()
	return commentFound

@app.route("/search", methods=['GET', 'POST'])
def search():
	if request.method == 'POST':
		userSearchResult, tagSearchResult, commentSearchResult = "", "", ""
		userSearch = request.form.get('username')
		tagSearch = request.form.get('tags')
		commentSearch = request.form.get('comment')
		if userSearch != "":
			userSearchResult = doUserSearch(userSearch)
		if tagSearch != "":
			tagSearchResult = doTagSearch(tagSearch)
		if commentSearch != "":
			commentSearchResult = doCommentSearch(commentSearch)
		return search_result(userSearchResult, tagSearchResult, commentSearchResult)
	else:
		return render_template('search.html', form = search)

@app.route("/search_result", methods=['GET'])
def search_result(users, tags, comments):
	return render_template('search_result.html', users = users, tags = tags, base64=base64, comments = comments)


@app.route("/user/<int:uid>", methods=['GET','POST'])
def display_user_info(uid):
	if request.method == 'GET':
		return render_template('user.html', user=get_user_data(uid), albums=get_user_album_data(uid),
	 						friends=get_user_friends(uid), tags=get_user_tags(uid),uid=uid)
	else:
		return add_friend(uid)

@flask_login.login_required
def add_friend(uid):
	this_user = getUserIdFromEmail(flask_login.current_user.id)
	if this_user == uid:
		return render_template('user.html', user=get_user_data(uid), albums=get_user_album_data(uid),
	 					friends=get_user_friends(uid), tags=get_user_tags(uid), uid=uid,message="ERROR: You cannot friend yourself.")
	else:
		cursor = conn.cursor()
		cursor.execute('''SELECT f.b_uid
						  FROM Friends f
						  WHERE f.a_uid = %s AND f.b_uid = %s''', (this_user, uid))
		already_friends = cursor.fetchone()

		if already_friends != None:
			return render_template('user.html', user=get_user_data(uid), albums=get_user_album_data(uid),
	 					friends=get_user_friends(uid), tags=get_user_tags(uid),uid=uid, 
						message="You are already friends with this user.")

		cursor.execute('''INSERT INTO Friends (a_uid, b_uid) VALUES (%s,%s)''',(this_user, uid))
		conn.commit()
		cursor.execute('''INSERT INTO Friends (a_uid, b_uid) VALUES (%s,%s)''',(uid,this_user))
		conn.commit()
		return render_template('user.html', user=get_user_data(uid), albums=get_user_album_data(uid),
	 					friends=get_user_friends(uid), tags=get_user_tags(uid),uid=uid)


def get_user_data(uid):
	cursor = conn.cursor()
	cursor.execute('''SELECT u.f_name, u.l_name, u.email, u.hometown
					  FROM Users u
					  WHERE u.u_id = %s''', uid)
	return cursor.fetchall()

def get_user_album_data(uid):
	cursor = conn.cursor()
	cursor.execute('''SELECT a.a_id, a.date_created, a.album_name
					  FROM Albums a
					  WHERE a.userid = %s''', uid)
	return cursor.fetchall()

def get_user_tags(uid):
	cursor = conn.cursor()
	cursor.execute('''SELECT *
					  FROM Tags
					  WHERE Tags.tag_id IN
					  (SELECT T.tags_id 
					  FROM Tagged T, Pictures P
					  WHERE P.u_id = %s AND T.photo_id = P.photo_id)''', (uid))
	return cursor.fetchall()

def get_user_friends(uid):
	cursor = conn.cursor()
	cursor.execute('''SELECT f.a_uid, f.b_uid, u.f_name, u.l_name, u.email
					  FROM Users u, Friends f
					  WHERE f.b_uid = u.u_id AND f.a_uid = %s''', uid)
	return cursor.fetchall()

@app.route("/album/<int:aid>", methods=['GET','POST'])
def display_album_info(aid):
	cursor = conn.cursor()
	if request.method == 'GET':
		cursor.execute('''SELECT p.photo_id, p.caption, p.p_data, p.a_id, p.u_id, a.a_id, a.date_created, 
					  a.album_name, a.userid
					  FROM Pictures p, Albums a
					  WHERE p.a_id = a.a_id AND a.a_id = %s''', (aid))
		photodata = cursor.fetchall()
		cursor.execute('''SELECT u.email
					  FROM Users u, Albums a
					  WHERE u.u_id = a.userid and a.a_id = %s''', (aid))
		albumowner = cursor.fetchone()
		return render_template('album.html', photos=photodata, base64=base64, albumowner=albumowner)
	else:
		current_user = getUserIdFromEmail(flask_login.current_user.id)
		cursor.execute("SELECT userid FROM Albums WHERE a_id = %s", (aid))
		albumowner = cursor.fetchone()
		if current_user == albumowner[0]:
			cursor.execute("DELETE FROM Albums WHERE a_id = %s", (aid))
			conn.commit()
			return protected()
		else:
			cursor.execute('''SELECT p.photo_id, p.caption, p.p_data, p.a_id, p.u_id, a.a_id, a.date_created, 
					  a.album_name, a.userid
					  FROM Pictures p, Albums a
					  WHERE p.a_id = a.a_id AND a.a_id = %s''', (aid))
			photodata = cursor.fetchall()
			cursor.execute('''SELECT u.email
					  FROM Users u, Albums a
					  WHERE u.u_id = a.userid and a.a_id = %s''', (aid))
			return render_template('album.html', photos=photodata, base64=base64, albumowner=albumowner, message="ERROR: You can only delete your own albums")

@app.route("/tag/<int:tag_id>", methods=['GET'])
def display_all_tag_pics(tag_id):
	cursor = conn.cursor()
	cursor.execute('''SELECT P.photo_id, P.caption, P.p_data 
	                 FROM Pictures P, Tagged T
					WHERE T.tags_id = %s AND P.photo_id = T.photo_id''', (tag_id))
	photodata = cursor.fetchall()
	cursor.execute("SELECT T.descript FROM Tags T WHERE T.tag_id = %s",(tag_id))
	descript = cursor.fetchall()
	return render_template('tag.html', descript=descript, photos=photodata, base64 = base64, tag_id=tag_id)

@app.route("/my-tag/<int:tag_id>", methods=['GET'])
@flask_login.login_required
def display_my_tag_pics(tag_id):
	cursor = conn.cursor()
	user = getUserIdFromEmail(flask_login.current_user.id)
	cursor.execute('''SELECT P.photo_id, P.caption, P.p_data 
	                 FROM Pictures P, Tagged T
					WHERE T.tags_id = %s AND P.u_id = %s AND T.photo_id = P.photo_id''', (tag_id, user))
	results = cursor.fetchall()
	cursor.execute("SELECT T.descript FROM Tags T WHERE T.tag_id = %s",(tag_id))
	descript = cursor.fetchall()
	return render_template('my-tag.html', descript=descript, photos=results,base64=base64)

@app.route("/photo/<int:pid>", methods=['GET', 'POST'])
def display_photo_info(pid):
	if request.method == 'POST':
		return update_likes_and_comments(pid)	
	else:
		photodata = get_picture_data(pid)
		commentdata = get_comment_data(pid)
		likes = get_who_liked(pid)
		numlikes = len(likes)
		tags = get_picture_tags(pid)
		print(tags)
		return render_template('photo.html', photos=photodata, base64=base64, comments=commentdata, 
											 numlikes=numlikes, likes=likes, tags=tags)

@flask_login.login_required
def update_likes_and_comments(pid):
		uid = getUserIdFromEmail(flask_login.current_user.id)
		commentcontents = request.form.get('comment')
		likes = get_who_liked(pid)
		numlikes = len(likes)
		cursor = conn.cursor()

		if commentcontents != None:
			cursor.execute('''SELECT p.photo_id, p.u_id 
							FROM Pictures p
							WHERE p.photo_id = %s''', (pid))
			photoowner = cursor.fetchall()

			if photoowner[0][1] == uid:
				return render_template('photo.html', photos=get_picture_data(pid),
										base64=base64, comments=get_comment_data(pid),
										numlikes=numlikes, likes=likes, tags=get_picture_tags(pid),
										errormessage="ERROR: User cannot comment on own photo.")
			else:
				cursor.execute('''INSERT INTO Comments (c_owner, contents, photo_id) VALUES (%s, %s, %s)''', (uid, commentcontents, photoowner[0][0]))
				conn.commit()
				return render_template('photo.html', photos=get_picture_data(pid),
										numlikes=numlikes, likes=likes,
										base64=base64, comments=get_comment_data(pid), tags=get_picture_tags(pid))		
		else:
			if 'deletebutton' in request.form:
				current_user = getUserIdFromEmail(flask_login.current_user.id)
				cursor.execute("SELECT u_id FROM Pictures WHERE photo_id = %s", (pid))
				photoowner = cursor.fetchone()
				if current_user == photoowner[0]:
					cursor.execute("DELETE FROM Pictures WHERE photo_id = %s", (pid))
					conn.commit()
					return protected()
				else:
					photodata = get_picture_data(pid)
					commentdata = get_comment_data(pid)
					likes = get_who_liked(pid)
					numlikes = len(likes)
					tags = get_picture_tags(pid)
					return render_template('photo.html', photos=photodata, base64=base64, comments=commentdata, 
											 numlikes=numlikes, likes=likes, tags=tags, errormessage="ERROR: You can only delete your own photos")

			else:
				cursor.execute('''SELECT l.u_id 
								  FROM Likes l
								  WHERE l.photo_id = %s AND l.u_id = %s''', (pid, uid))
				already_liked = cursor.fetchone()
				
				if already_liked == None:
					cursor.execute('''INSERT INTO Likes (photo_id, u_id) VALUES (%s, %s)''', (pid, uid))
					conn.commit()
					likes = get_who_liked(pid)
					numlikes = len(likes)
					return render_template('photo.html', photos=get_picture_data(pid),
											numlikes=numlikes, likes=likes,
											base64=base64, comments=get_comment_data(pid), tags=get_picture_tags(pid))
				else:
					return render_template('photo.html', photos=get_picture_data(pid),
											numlikes=numlikes, likes=likes,
											base64=base64, comments=get_comment_data(pid), tags=get_picture_tags(pid),
											errormessage='You already liked this photo.')	


def get_picture_data(pid):
	cursor = conn.cursor()
	cursor.execute('''SELECT p.p_data, p.photo_id, p.caption
					  FROM Pictures p 
					  WHERE p.photo_id = %s''', pid)
	return cursor.fetchall()

def get_comment_data(pid):
	cursor = conn.cursor()
	cursor.execute('''SELECT c.c_id, c.c_owner, c.date, c.contents, c.photo_id, u.email
					  FROM Comments c, Users u
					  WHERE u.u_id = c.c_owner AND c.photo_id = %s''', (pid))
	return cursor.fetchall()

def get_who_liked(pid):
	cursor = conn.cursor()
	cursor.execute('''SELECT l.photo_id, l.u_id, u.email
					  FROM Likes l, Users u
					  WHERE l.u_id = u.u_id AND l.photo_id = %s''', (pid))
	return cursor.fetchall()

def get_picture_tags(pid):
	cursor = conn.cursor()
	cursor.execute('''SELECT * FROM Tags T WHERE T.tag_id IN (SELECT Ta.tags_id FROM Tagged Ta, Pictures P WHERE (Ta.photo_id = P.photo_id AND Ta.photo_id = %s))''',(pid))
	return cursor.fetchall()


@app.route("/test", methods=['GET'])
def testusers():
	cursor = conn.cursor()
	cursor.execute('''SELECT u.u_id, u.email, u.f_name, u.l_name, u.dob
			          FROM Users u ''')
	UserList = cursor.fetchall()

	cursor.execute('''SELECT a.a_id, a.album_name
						  FROM  Albums a''')
	OldAlbums = cursor.fetchall()
	return render_template('test.html', users=UserList, albums=OldAlbums)

@app.route("/", methods=['GET'])
def mainpage():
	cursor = conn.cursor()
	cursor.execute('''SELECT u.u_id, u.email, u.f_name, u.l_name, u.dob, COUNT(*) as contributions
		FROM Users u, Comments C, Pictures P
		WHERE (u.u_id = C.c_owner OR u.u_id = P.u_id)
		GROUP BY u.u_id
		ORDER BY contributions DESC 
		LIMIT 3''')
	topUsers = cursor.fetchall()
	print(topUsers)
	cursor.execute('''SELECT T.tag_id, T.descript, COUNT(*) as num_tagged
	FROM Tags T, Tagged Ta
	WHERE T.tag_id = Ta.tags_id
	GROUP BY T.tag_id
	ORDER BY num_tagged DESC
	LIMIT 3''')
	topTags = cursor.fetchall()

	return render_template('index.html', message='Welcome to Photoshare', users=topUsers, tags=topTags)

if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
