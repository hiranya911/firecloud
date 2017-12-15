# Flask on Google Compute Engine

This is a simple Python web service based on [Flask](http://flask.pocoo.org/docs/0.12/quickstart/).
It can be deployed on any environment that
supports Python, including Google Compute Engine. The web service uses 
[Firebase Admin SDK](https://firebase.google.com/docs/admin/setup) to
interact with the Firebase Realtime Database.

## Requirements

* Python 2.7
* `virtualenv` is recommended for local testing
* `gcloud` command line utilities
* `curl` command lint tool

## Local Setup

* Start a new virtualenv environment.

```
virtualenv env
source env/bin/activate
```

* Download a service account credential from your Firebase project.
* Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to point to the downloaded service
  account credential.

```
export GOOGLE_APPLICATION_CREDENTIALS=path/to/serviceAccount.json
```

* Install the dependencies (Flask and firebase-admin modules).

```
pip install -r requirements.txt
```

* Update the `<DB_NAME>` field in `super_heroes.py`. This should point to the Realtime Database of
  your Firebase project.
* Launch the web service.

```
export FLASK_APP=super_heroes.py
flask run
```

* If all went well your web service should be now running locally. By default Flask listens for
  incoming requests on port 5000.

## Sending Requests

* Create a new entry by sending a POST request. This responds with an HTTP `201 Created` response,
  and a unique ID string. When completed, the entry should be saved to the Firebase Realtime
  Database at `/super_heroes/<ID>`. 

```
$ curl -v -X POST -d @spiderman.json -H "Content-type: application/json" http://localhost:5000/heroes
< HTTP/1.0 201 CREATED
< Content-Type: application/json
< Content-Length: 35
< Server: Werkzeug/0.13 Python/2.7.6
< Date: Fri, 15 Dec 2017 22:16:39 GMT
< 
{
  "id": "-L0RF2E2upW9jhCjmi6R"
}
```

* You can use the returned ID to retrieve the entry.

```
$ curl -v http://localhost:5000/heroes/-L0RF2E2upW9jhCjmi6R
< HTTP/1.0 200 OK
< Content-Type: application/json
< Content-Length: 197
< Server: Werkzeug/0.13 Python/2.7.6
< Date: Fri, 15 Dec 2017 22:18:11 GMT
< 
{
  "name": "Spider-Man", 
  "powers": [
    "wall crawling", 
    "web shooters", 
    "spider senses", 
    "super human stregth & agility"
  ], 
  "realName": "Peter Parker", 
  "since": 1962
}
```

* An invalid ID will return a `404 NOT FOUND` response.

```
$ curl -v http://localhost:5000/heroes/invalid_id
< HTTP/1.0 404 NOT FOUND
< Content-Type: text/html
< Content-Length: 233
< Server: Werkzeug/0.13 Python/2.7.6
< Date: Fri, 15 Dec 2017 22:18:16 GMT
< 
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<title>404 Not Found</title>
<h1>Not Found</h1>
...
```

* Similarly you can experiment with PUT and DELETE requests to update and delete entries from the
  database.

## Deploying to Google Compute Engine

* You will use the `gcloud` command line tools to start and manage Compute Engine virtual machine
  (VM) instances. All the `gcloud` commands listed in this section should be run in your local
  workstation.
* Since we are using Google application default credentials, we must create our VM instance in the
  Google Cloud Platform (GCP) project that is associated with our Firebase project.

```
gcloud config set project <Firebase/GCP project name>
```

* Create a new VM instance with the required OAuth2 scopes.

```
export SCOPES=https://www.googleapis.com/auth/firebase.database,https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/cloud-platform
gcloud compute instances create flask-demo --scopes $SCOPES
```

* The `cloud-platform` scope is not required for this example. But it is required if you ever
  access Google Cloud Storage or Cloud Firestore from the Admin SDK.
* Start the VM instance.

```
gcloud compute instances start flask-demo
```

* SSH into the instance.

```
gcloud compute ssh flask-demo
```

* Copy `super_heroes.py` into the file system of the instance. You can either scp the file over,
  or just copy-and-paste the content manually since the file is very small. Make sure the
  database URL is correct in the deployed file.
* Install the necessary tools and dependencies.

```
sudo apt-get install -y python-pip
pip install --user firebase-admin google-auth-oauthlib
```

* `google-auth-oauthlib` installed above is not really required for this example. But without it,
  you're likely to encounter an
  [issue](https://github.com/GoogleCloudPlatform/google-auth-library-python/issues/229)
  loading some crypto modules. It will get fixed in the near future.
* Install Flask globally, so you can access the `flask` command line utility.

```
sudo pip install flask
```

* Launch the application as usual.

```
export FLASK_APP=super_heroes.py
flask run
```

* Run some curl commands from the VM instance to make sure everything is working as expected.
* To send requests to the service remotely, you need to:
  - Bind the Flask server to the public facing network interface.
  - Open up Flask port (5000) in the GCP Firewall.

```
# On VM instance
flask run --host=0.0.0.0
```

```
# On local workstation
gcloud compute firewall-rules create open-flask --allow tcp:5000 --source-tags=flask-demo --source-ranges=0.0.0.0/0
```
