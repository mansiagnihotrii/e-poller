# e-poller
## This online voting application (E-POLLER) runs using flask primarily. It uses Heroku Postgres Database.

If you are not familiar with heroku , follow these steps:

## SET UP HEROKU POSTGRES DATABASE
1. Navigate to "signup.heroku.com" and create an account. Login after you created the account.
2. Create new app. The app name can be of your choice.
3. Navigate to "Resources" tab in the header of heroku dashboard. Then type Heroku Postgres into the Add-ons search field. Select Heroku Postgres from the dropdown.
4. Select "Hobby Dev-Free" plan and click "Provision".
****Your free postgreSQL Database is created****
5. Navigate to "Heroku Postgres"-->"Settings"-->"View Credentials" to see your credentials


## SET UP ENVIRONMENT VARIABLES

****DATABASE_URL****
:  Set DATABASE_URL environment variable to the value of URI in your Heroku Credentials.

****FLASK_APP****
:  Set FLASK_APP environment variable to value "application.py"


## RUN THE APPLICATION
1. Open cmd and navigate to your repository location.
2. Type following command to install all the requirements. (Make sure you have python 3.0+ version installed)
			>> "pip install -r requirements.txt"	
3. Type following command to create tables in your database. (Make sure to set environment variables)
			>> "python import.py"
4. Lastly, type following command to run your application.
			>> "flask run"
Navigate to your localhost address in your browser to see the application in action !!!!

