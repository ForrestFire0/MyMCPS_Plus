import requests
import webbrowser

s = requests.session()

clientID = ""
clientSecret = ""
redirect_uri = 'https://qwertyuiopa.com/oauth_complete'

#Step 1: Redirect users to request Canvas access
#1A Generate a variable for state.
state = "123456789"
#1B Generate the link with the client ID
link = 'https://mcpsmd.instructure.com/login/oauth2/auth?client_id=' + clientID + '&response_type=code&redirect_uri=' + redirectURI + '&state=' + state

webbrowser.open_new_tab(link)

#Step 2: Redirect back to the request_uri, or out-of-band redirect
code = input("Enter the code from the URL")
print("Sending post request...")

data = {
    'grant_type': 'authorization_code',
    'client_id': clientID,
    'client_secret': clientSecret,
    'redirect_uri': redirect_uri,
    'code': code,
    }

link = 'https://mcpsmd.instructure.com/login/oauth2/token'

response = s.post(link, data = data)
print(response.text)

json = response.json()

refreshToken = json['refresh_token']
accessToken = json['access_token']
print("Access Token: " + accessToken)
print("Refresh Token: " + refreshToken)