# GVE_DevNet_Meraki_Downtime_Reporting
Logging and report generation for downtime of Meraki devices

![Downtime Web App](IMAGES/highlevel.png)

## Contacts
* Josh Ingeniero

## Solution Components
* Meraki
* MongoDB
* Python
* Flask

## Installation:
You must have the [collector](collector) folder on your intended server to collect downtime
data, and your [web-app](web-app) folder on your web-app server to view data.

#### Clone the repo
```console
git clone https://github.com/gve-sw/gve_devnet_meraki_downtime_reporting
```
#### Set up a Python venv
First make sure that you have Python 3 installed on your machine. We will then be using venv to create
an isolated environment with only the necessary packages.

##### Install virtualenv via pip
```
$ pip install virtualenv
```

##### Create a new venv
```
Change to your project folder
$ cd GVE_DevNet_Meraki_Downtime_Reporting

Create the venv
$ virtualenv venv

Activate your venv
$ source venv/bin/activate
```

#### Install dependencies
```
$ pip install -r requirements.txt
```

## Setup

#### Meraki details:
You can deploy this prototype in a lab environment or on your own Meraki dashboard online
[here](https://account.meraki.com/secure/login/dashboard_login).

To generate an API KEY, refer to the documentation [here](https://documentation.meraki.com/zGeneral_Administration/Other_Topics/The_Cisco_Meraki_Dashboard_API#Enable_API_access).
You will use this for getting an ORGANIZATION ID, and using this application.

You must select an organization to manage and use its ORGANIZATION ID. You may do so by using Meraki's Postman collection
[here](https://documenter.getpostman.com/view/7928889/SVmsVg6K#18e62fd9-402a-4768-ab5e-f11a44651cfe) and GET the list of organizations,
or use Meraki's API Docs to generate a request [here](https://developer.cisco.com/meraki/api-v1/#!get-organizations).


Fill in the details of your Meraki deployment in the [DETAILS.py](web-app/DETAILS.py) file in the web-app folder
and [main.py](collector/main.py) in the collector folder.
```python
# Meraki Details
API_KEY = "API KEY"
ORG_ID = 999999
```

#### MongoDB details:
You would need to use a MongoDB server for this prototype. You may use MongoDB Atlas, which
you can try for free [here](https://www.mongodb.com/cloud/atlas).

Fill in the details of your MongoDB deployment in the [DETAILS.py](web-app/DETAILS.py) file in the web-app folder
and [main.py](collector/main.py) in the collector folder. You may either use variables for the connection string
or copy it as per instructions [here](https://docs.atlas.mongodb.com/driver-connection/).

```python
# MongoDB Details
DBNAME = "database name"
PASSWORD = "database password"
CONNECTION_STRING = f"mongodb+srv://username:{PASSWORD}@cluster_url/{DBNAME}?retryWrites=true&w=majority"
```


## Usage:
These require the appropriate venv to be activated.

### Collector Server
Run the collector app to collect downtime data
```
$ cd collector
$ python main.py
```

### Web App
Run the flask app to view downtime data
```
$ cd web-app
$ flask run
```
### Database Schema
![img.png](IMAGES/db.png)

# Screenshots

### Downtime Web App
![Downtime Web App](IMAGES/web-app.png)

![IMAGES/0image.png](IMAGES/0image.png)

### LICENSE

Provided under Cisco Sample Code License, for details see [LICENSE](LICENSE.md)

### CODE OF CONDUCT

Our code of conduct is available [here](CODE_OF_CONDUCT.md)

### CONTRIBUTING

See our contributing guidelines [here](CONTRIBUTING.md)

#### DISCLAIMER:
**Please note:** This script is meant for demo purposes only. All tools/ scripts in this repo are released for use "AS IS" without any warranties of any kind, including, but not limited to their installation, use, or performance. Any use of these scripts and tools is at your own risk. There is no guarantee that they have been through thorough testing in a comparable environment and we are not responsible for any damage or data loss incurred with their use.
You are responsible for reviewing and testing any scripts you run thoroughly before use in any non-testing environment.