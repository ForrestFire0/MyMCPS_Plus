from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, ValidationError
from wtforms.validators import Length
from gradedisplay.models import User

# Create a new object that inherits the flaskform properties, we want to add
# our additional attributes that this object should have
class LoginForm(FlaskForm):  
    # We want a uername feild, we restrict the length and put in a placeholder
    username = StringField('School ID', render_kw={"placeholder": "Enter your ID"})
    # Same as the username feild, we want a passord feild in which we restrict
    # the length and add a placeholder
    password = PasswordField('Password', validators=[Length(min=6, max=8)], render_kw={"placeholder": "Enter your password"})
    # Add a submit feild
    submit = SubmitField('Login')
    
    #def validate_username(self, username): #see if our user has signed up.
    #    if not len(str(username.data)) == 6:
    #        print("Error: not six digits.")
    #        raise ValidationError("Enter your six digit numerical ID");
    #    else: 
    #        print("was six digits")
    #        user = User.query.filter_by(schoolID=username.data).first()
    #        if not user: #this user does not exist in our database
    #            print("not in database")
    #            raise ValidationError("This ID has not signed up.")



class SignupForm(FlaskForm):
    schoolID = StringField("schoolID", validators=[Length(min=6, max=6)], render_kw={"placeholder": "Enter Your School Issued ID"})
    submit = SubmitField("Sign Up")

    #def validate_schoolID(self, schoolID):
    #    user = User.query.filter_by(schoolID=schoolID.data).first()
    #    if user:
    #        raise ValidationError("This ID has already signed up. Please Sign In.")
        
