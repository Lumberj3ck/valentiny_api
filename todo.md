Can I make json key as a integer?
Deployments potential problems:
Path for .env.api file inside of dependencies.py
Db not created
Change url path for database inside of db.py

- [] Set a unique key pair in db for name and user inside of section 
Because it is imposible for one user to have two the same sections
- [] Set a unique name per request for update and create; Name should be unique
for every section inside the list


Create endpoint for getting user sections by user id 


Use integer keys as string on front

Realy hash passwords!

- [ ] Change save json api endpoint now instead of list of sections dict of sections: list


When user and sections just created then we need to either make second 
api call to fetch id of instance so then if user makes additional sections
changes we can send update api call


But we api after post can just send data without additional cal



User registration 
Send post request to /users/create_user/
If success than change page to login page
So when user sends username and password
we trying authenticate user if we get right user then we can send for user 
jwt token with username 
on frontend we save given token 
then whenever we need to access /sections/user
we need to send jwt token if there is no token (api will decrypt username from
jwt and then return the user and accessed information)
; give login page 

FOR BACKEND 
whenever we want to restrict access to the endpoint we must add auth dependence which
will seek for bearer jwt token in headers


Whenever user logins frontend should send a request to a api user sections 
