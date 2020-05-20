from flask import render_template, url_for, request, flash, redirect, make_response, session # Import some built in functions of flask
from gradedisplay import app, db # Import the app from our package, for decorators.  Import Database.
from gradedisplay.form import LoginForm, SignupForm #Form imports
from gradedisplay.models import User, Assignment, Period #models imports
from gradedisplay.data import getDBAssignments, getDBPeriods
from datetime import datetime
from time import time

# Import sessions
from flask_session import Session
# Import other useful stuff
import requests
import lxml.html
import json
import os
import time
import smtplib
# Env vars
from dotenv import load_dotenv
load_dotenv()


# Create an instance of a request object
s = requests.session()
# Use a get request to the portal login page, then we get the hidden feilds in
# the form that we will need to copy and post back to the server
# This code was borrowed from Stephen Brennan at
# https://brennan.io/2016/03/02/logging-in-with-requests/
login = s.get('https://portal.mcpsmd.org/public/')
login_html = lxml.html.fromstring(login.text)
hidden_inputs = login_html.xpath(r'//form//input[@type="hidden"]')
form = {x.attrib["name"]: x.attrib["value"] for x in hidden_inputs}

# Create a session object and initilize it
sess = Session()
sess.init_app(app)

# I could probably do this in a differnt way where I figure out if its summer
# based on the result from the sever, but I think that this is probably
# simpler, its just that I will have to manually edit it (only once a year tho)
summer_break = eval(os.getenv('sb'))
# Same with this, I think that I could figure out how to automate this, but im
# fine with having to manually edit it each quarter
marking_period = os.getenv('mp')

# This function takes the username and password and returns the users info.
def load_data(form):
    '''This function handles the data loading of the program, the input "form" is what the user entered on the login form. All the data is loaded as soon as the user enters vaild credentials'''
    # Try to post the data, which is a collection of what we get with the get
    # request at the top of the page and the users credentials
    # Sometimes the portal page glitches out, you enter in valid credentials
    # and nothing happens, you may have experienced this yourself, so I created
    # a loop to conteract this
    # However, we don't want the loop to interate too much because if the user
    # entered invalid credentials, it could end up locking their account as
    # that is how MCPS deals with brute force attacks
    for i in range(3):
        # Keep posting
        response = s.post('https://portal.mcpsmd.org/guardian/home.html', data=form)
        # Check if it is valid by tring to find something that is there when
        # the user enters valid credentials
        if response.text.find('root.schoolId') != -1:
            # Exit this loop if it is proved that the user entered valid
            # credentials
            break
    # If even after the 3 attempts, it is found the credentials are invalid,
    # exit this function (return None)
    if response.text.find('root.schoolId') == -1:
        return
    # However, if it is found that the user entered valid data, we need to get
    # that data and format in a way that suits us
    else:
        # We first get the school id and the guardian id which are needed
        # later, also initilize a variable called specialData which we will
        # only use in specific cases
        gradeInfo, specialData = [[response.text[response.text.find('root.schoolId') + 26:response.text.find('root.schoolId') + 29],response.text[response.text.find('root.guardianId') + 19: response.text.find('root.guardianId') + 24]]],[]
        # Here we use the guardian id as well as the school id to get data of
        # all the classes that the student has taken in the school year and we
        # store it in loginData
        # This data includes the course and teacher name, the marking period,
        # the overall grade, the class period and more
        loginData = s.get('https://portal.mcpsmd.org/guardian/prefs/gradeByCourseSecondary.json?schoolid=' + gradeInfo[0][0] + '&student_number=' + form['account'] + '&studentId=' + gradeInfo[0][1]).json()

        # Now we need to keep only the data that we want, so we will loop
        # through the loginData that we just got
        for quarter in range(len(loginData) - 1):
            # Here we filter the login data to match only the marking period
            # that we want to show
            if loginData[quarter]['termid'] == marking_period:
                # Now we are looping through each class, we get the more
                # specific information here such as the percent that the user
                # has in the class, and storing it so that we can filter it
                # later
                basicInfo = s.get('https://portal.mcpsmd.org/guardian/prefs/assignmentGrade_CourseDetail.json?secid=' + loginData[quarter]['sectionid'] + '&student_number=' + form['account'] + '&schoolid=' + gradeInfo[0][0] + '&termid=' + marking_period)
                basicInfo = basicInfo.json()
                # Now with that information that we received, we want to only
                # store the following - the name of the course, the overall
                # grade, the percent the user has in the class, etc
                gradeInfo.append([basicInfo['courseName'], basicInfo['overallgrade'], float(basicInfo['percent']),basicInfo['teacher'],basicInfo['email_addr'], basicInfo['sectionid'], basicInfo['period']])
                # Now that we have added that info to grade data, we also want
                # to add the actual grades such as the grade categories (for
                # example the formative category with a weight of 40) and the
                # percent that the user has in each category
                # We also get the individual grades, for example a 30/40 on a
                # formative project or 10/10 on a homework, we save these both
                # in our gradeInfo variable
                gradeInfo.append([s.get('https://portal.mcpsmd.org/guardian/prefs/assignmentGrade_CategoryDetail.json?secid=' + basicInfo['sectionid'] + '&student_number=' + form['account'] + '&schoolid=' + gradeInfo[0][0] + '&termid=' + marking_period).json(),s.get('https://portal.mcpsmd.org/guardian/prefs/assignmentGrade_AssignmentDetail.json?secid=' + basicInfo['sectionid'] + '&student_number=' + form['account'] + '&schoolid=' + gradeInfo[0][0] + '&termid=' + marking_period).json()])
            # However, we also want to keep track of unlisted marking periods
            # because due to how MyMCPS works, if a grade isnt entered for a
            # class, there will be no marking period assigned to that class
            # If the class isnt included, it will cause our program to crash
            # later, therefore it is necesary that we add the classes without
            # grades, also we need to check that these aren't "fake classes"
            # like counselor
            elif loginData[quarter]['termid'] == '' and loginData[quarter]['courseName'] not in ['HOMEROOM', 'COUNSELOR', 'MYP RESEARCH SEM']:
                # Add the course name, and everthing else, this is the same
                # thing we did with the other data
                specialData.append([loginData[quarter]['courseName'], '', '', loginData[quarter]['teacher'],loginData[quarter]['email_addr'], loginData[quarter]['sectionid'],loginData[quarter]['period']])
        # If we found special data, this is only run when you have a class that
        # doesn't have grades entered, because MCPS won't assign a marking
        # period to them when sending the json over
        if specialData:
            # Here we look at all the users classes again, and we sort them
            # I fixed this so this shouldn't be able to crash
            # Get the higest period we have of the special data
            lastSpecialData = int(specialData[-1][6]) if len(specialData) > 0 and isinstance(specialData[-1][6], str) and specialData[-1][6].isdigit() else 0
            # Get the highest period we have of the actual grade data
            lastGradeData = int(gradeInfo[-2][6]) if len(gradeInfo) >= 2 and isinstance(gradeInfo[-2][6], str) and gradeInfo[-2][6].isdigit() else 0
            # Get the max of these, and run through the range to make sure we
            # have all the periods in between
            for period in range(max(lastSpecialData,lastGradeData,1)):
                # Due to how I stored the data, I know how to perform
                # calculations on it to check for certian things, the first
                # clause checks to see that the period isnt outside of the
                # amount of classes stored in gradeInfo, if it is,
                # then that class might need to be added, also I check to see
                # if the class in gradeInfo isnt matching up with the period,
                # for example, if the period I'm looking for is 1 (meaning
                # period is 0 since I am interating through
                # a list that starts from 0 and goes to the last period), then
                # I check to see if the period at the index that should
                # correspond to 1 is in fact 1, and if it is not, then we need
                # to proceed
                if (period) * 2 + 1 > len(gradeInfo) - 2 or gradeInfo[(period) * 2 + 1][6] != "0" + str(period + 1):
                    # Keep a boolean to see if we have found something to fill
                    # that periods location
                    classFound = False
                    # Enumerate through all the special data
                    for data in range(len(specialData)):
                        # If the data is the one that we are looking for (we
                        # got this from the if loop) then we will proceed
                        if specialData[data][6] == "0" + str(period + 1):
                            # Change bool
                            classFound = True
                            # We want to then insert that data at the specific
                            # location, this is the class data, as I said
                            # before this includes things such as the course
                            # name, and everthing else
                            gradeInfo.insert(period * 2 + 1, specialData[data]) 
                            # Since there are no grades, just put in a list
                            # with blank dictionaries to server sort of as a
                            # place holder
                            gradeInfo.insert(period * 2 + 2, [{},{}])
                    # Apparently there can be classes that just don't exist on
                    # portal as well
                    if not classFound:
                        # Fill in class data with "missing"
                        gradeInfo.insert(period * 2 + 1, ['CLASS DATA MISSING','', '','UNKOWN TEACHER','UNKNOWN EMAIL','00000000','0' + str(period + 1)])
                        # Put in empty grade data
                        gradeInfo.insert(period * 2 + 2, [{},{}])
        # After everything, return the grade data
        return gradeInfo
        # We now have all the grade data that we will need for the entire
        # program, the format is as such:
        '''
        [[schoolId, gardianId], [class1Attr1, class1Attr2, *this is filled with class attributes that include the teachers name, period number, grade in the class, etc*], [{class1GradeHeader1, class1GradeHeader2, *this is filled with the class grade headers*},{class1Grade1, class1Grade2, *this is filled with the individual grades*}], *and here we would place our second class followed by its grades*]
        '''
        # So as you can see, we have a large list which begins with a small
        # list containing the school and guardian id (which are actually
        # useless after we have gathered the data but I'm to remove them
        # because I would have to change the rest of the program and I'm too
        # lazy to change everything, maybe I will later)
        # After that list, we have a class which is a list that has some
        # attributes of the class, with another list is followed by another
        # list which has two dictionaries containing grade data
        # Then we would have more classes following that class, meaning two
        # lists (per class), the first with class attributes the second with
        # dictionaries with grade data
        # Thats it for the data gathering/formatting part which I think was one
        # of the hardest parts of this program , honestly I think by organizing
        # the data this way I made it harder for myself

# Decorator before_request, makes the following function run when they are
# fetching the website
# Function that delete old session information so that the server won't run out
# of memory with useless session info
@app.before_request
def cleanSessionData():
    '''clean the old session data on the server'''
    # Im using an exception just in case I'm not able to find the data or
    # something weird happens so that it doesn't crash
    try:
        # Here we search through all the files in the current directory under
        # the file flask session which is where flask sessions are stored
        for filename in os.listdir(os.getcwd() + '//flask_session'):
            # If the current time minus the time the file was made, which is
            # how long the file was "alive", exceeds 900 seconds, which is 15
            # minutes, proceed
            if time.time() - os.path.getmtime(os.getcwd() + '//flask_session//' + filename) > 900:
                # Delete this file, 15 minutes seems like a long enough time to
                # check grades, we don't want it to be too long
                os.remove(os.getcwd() + '//flask_session//' + filename)
    # If an error occurs when trying to get rid of files store it in e
    except Exception as e:
        # Display an error message to the user, the developer actually wont be
        # notified, but if there was a recurring problem, I would already know
        # about it
        flash('An error occured: ' + str(e) + '. The developer will be notified', 'danger')

#this functions returns the signup page.
@app.route("/signup", methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit(): #The user successfully signed up.

        idnumber = int(form.schoolID.data)
        user = User(schoolID=idnumber, signupDate=datetime.now(), lastUpdateDate=datetime.min, sortingMethod="p")
        db.session.add(user)
        db.session.commit()
        print("New User Registered. ID Number:" + form.schoolID.data)
        return redirect(url_for('tutorial')) 
    return render_template("signup.html", form=form)

#This returns the page after the user has signed up.  Soon this will be a
#message about what the thing does and how it works, black theme.  It has a
#sucess message about the sign up.
@app.route("/tutorial")
def tutorial():
    return render_template("tutorial.html")

@app.route('/', methods=['GET', 'POST'])
def getInfo():
    return redirect(url_for('login'))

# Decorator which makes the following function run when the user goes to the
# default page, hence the "/", also allow both get and post requests since we
# have a form
@app.route("/login", methods=['GET', 'POST'])
# The actual function that handles what to do when the user gets on the website
def login():
    '''login page for the website'''
    # Before doing anything, we check to see if there is already current
    # session data, we check to see if the user has already logged in
    #if session.get('login', False):
        # Tell the user that they have already logged in
     #   flash('You are already logged in!', 'success')
        # Redirect the user to the grade page
      #  return redirect(url_for('assignments'))
    # Check if its summer break
    if summer_break:
        return redirect(url_for('summer'))
    # Create an instance of the class login form and feed it the login form on
    # the page
    login = LoginForm()
    
    # If they credentials that they entered into the form are valid then we can
    # do stuff with them
    if login.validate_on_submit():
        # Fill in some of the form fields of the form that we created at the
        # beginning of the program, so that the form is complete when we post
        # the data to MyMCPS
        form['account'], form['ldappassword'], form['pw'] = request.form['username'], request.form['password'], '0'
        session['login'] = True
        studentID = request.form['username']
        session['studentID'] = studentID
        print("User " + str(studentID) + ' is signing in.')

        return redirect(url_for('assignments'))

    # This section here tells the app to send the user the home page when they
    # connect to our website
    return render_template('home.html', title = 'Login', form=login)


#handle checking the box
@app.route('/set/<assignmentID>/<state>')
def set(assignmentID, state):
    if assignmentID == "sortingMethod":
        user=User.query.filter_by(schoolID=session.get('studentID')).first()
        user.sortingMethod = state
        db.session.commit()
    else:
        a = Assignment.query.get(assignmentID)
        a.completed = state == '1'
        db.session.commit()
        print("Set assignment " + str(assignmentID) + " to " + str(state))
    return ("Succsesssss")

@app.route('/assignments')
def assignments():
    
    #load some numbers from the signin page.

    if not session.get('login', False):
        return redirect(url_for('login'))

    studentID = session.get('studentID')
    user = User.query.filter_by(schoolID=studentID).first()
    
    sortingMethod = user.sortingMethod

    #Here we need to load all the data, but only if we are more that 24 hours from the last time we loaded it.

    if (datetime.now() - user.lastUpdateDate).days >= 1: #
        print("Loading data")
        user.lastUpdateDate = datetime.now();
        db.session.commit()
        #First, MCPS data.
        mcps_data = load_data(form)
        if mcps_data:
            #Note: 'getDBAssignments' gets assignments as an array of 'Assignment' models, not a python key thingamabob.
            myMCPS_Classes = getDBPeriods(mcps_data, user.id)
            addPeriods(myMCPS_Classes, user.id)
        
            myMCPS_Assignments = getDBAssignments(mcps_data, user.id)
            addAssignments(myMCPS_Assignments, user.id)

        else:
            flash("There is a very big problem. We couldent collect your MCPS data!", 'danger')
            return redirect(url_for('login'))
    
        #googleClassroomAssignmens = getGoogleClassroomAssignments()
        #canvasAssignmens = getCanvasAssignments()
    else:
        print("Skipping Load. Last Load Date: " + str(user.lastUpdateDate))
    A = user.classes

    assignments = []
    if sortingMethod == "m": #missing
        missingAssignments = Assignment.query.filter_by(userDBI=user.id, missing=True).all()
        assignments = Assignment.query.filter_by(userDBI=user.id, missing=False).all()
        assignments = [assignments, missingAssignments]
    elif sortingMethod == "d":
        assignments = Assignment.query.filter_by(userDBI=user.id).order_by(Assignment.duedate.asc()).all()
    else:
        assignments = Assignment.query.filter_by(userDBI=user.id).all()

    return render_template('assignments.html', classes1=A[:len(A)//2], classes2=A[len(A)//2:], sortingMethod=sortingMethod, assignments=assignments)

#updates the users master list of assignments with the new data we find.
def addAssignments(assignments, userID):
    studentID = session.get('studentID')

    print('Adding assignments for SID ' + str(studentID) + '. and DBI ' + str(userID))

    for ass in assignments:

        corDBAssignment = Assignment.query.filter_by(userDBI=userID, name=ass.name).first()
        exists = not corDBAssignment is None
        mcpsDone = ass.completed

        if exists: #we have a record
            if mcpsDone: #mcps says its done. Remove it from the list.
                db.session.delete(corDBAssignment)
            if not corDBAssignment.completed: 
                #if the user did not mark it as completed, we will update the assignment.
                db.session.delete(corDBAssignment)
                db.session.add(ass)
        else: # no record in DB.
            if not mcpsDone:
                print('New assignment found: ' + ass.name + ' done: ' + str(ass.completed))
                db.session.add(ass)

    db.session.commit()

#this does the same thing for assignments as it does for classes.
def addPeriods(classes, userID):
    studentID = session.get('studentID')

    print('Adding periodes for SID ' + str(studentID) + '. and DBI ' + str(userID))

    for cl in classes:

        dbc = Period.query.filter_by(userDBI=userID, name=cl.name).first()
        exists = not dbc is None

        if exists: #we have a record
            pass # we already have the class, dont mess with it.
        else: # no record in DB.
            print('New class found: ' + cl.name + ' Teacher: ' + str(cl.teacher))
            db.session.add(cl)

    db.session.commit()

# Decorator that makes the following function handle the about page on the
# website
@app.route('/about')
def about():
    # Since this page is quite simple, all we have to do is return the html
    # template
    return render_template('about.html', title = 'About Page')

# Decorator that makes the following function handle the /logout "page" on the
# website, not really a page, but...
@app.route('/logout')
def logout():
    # Set the session value of the login to be false
    session['login'] = False
    # Tell the user they have been logged out
    flash('You have been logged out!', 'info')
    # Finally, redirect them to the login page
    return redirect(url_for('getInfo'))

# Decorator that is supposed to handle the error 404 which is for pages that do
# not exist, so for instance if the user typed some thing random after our
# domain name (like mymcpsplusplus.herokuapp.com/blahblahblah), this would handle
# the error that would occur
@app.errorhandler(404)
def pageNotFound(e):
    print(e)
    # Tell the user they tried to go to a non existent page
    flash('You have entered a url that does not exist! You have been redirected.', 'warning')
    # Redirect them to the login page
    return redirect(url_for('login'))

# Decorator that handles the error 500 which is an internal server error, which
# is a pretty general error where something goes wrong, but the website doesn't
# really know what caused the crash
@app.errorhandler(500)
def crash(e):
    # Store the crash message in the session
    session['crash'] = str(e)
    # Return to the page with a crash message
    return redirect(url_for('getInfo'))

# Decorator that deals with the error 410, this is used for data that goes
# missing on the server for various reasons, I put this in just in case, but I
# don't think it will ever trigger
@app.errorhandler(410)
def deletedInfo():
    # Tell the user that a problem has occurred
    flash('It seems that the data you are trying to access has been mysteriously deleted or changed! If this problem persists, contact the creator of this website.', 'danger')
    # Redirect them to the homepage
    return redirect(url_for('getInfo'))