# Cryptocurrency Price Monitor

This is a sample Firebase app with both client-side and server-side components.
It allows users to keep track of the market prices of Bitcoin and Ethereum via
an Android app. Users can configure min and max price thresholds for each of
the above cryptocurrencies, and they will be notified whenever the price of a
currency drops below the min threshold, or exceeds the max threshold.

The app is comprised of three components.

1. [Android client app](./android-app)
2. [Price monitoring service](./cryptocron)
3. [Price notification sender](./notification-sender)

The objective of this app is to demonstrate how to access Firebase data and
services from several client and server platforms.

## Firebase and GCP services used

* Google Cloud Firestore
* Firebase Cloud Messaging
* Google App Engine
* Google Cloud Functions

## Requirements

You will need a Firebase project. Use the
[Firebase console](https://console.firebase.google.com/) to create one if you
haven't already. Enable Firestore for the project by following the
instructions in the [quickstart](https://firebase.google.com/docs/firestore/quickstart)
guide. Additionally, you will need the following software installed in your
development environment.

* Android app
  - Android Studio (tested with v3.2)
  - Gradle (tested with v4.6)
  - An Android virtual device (tested with a virtual Pixel 2 device running API
    28, Android 9.0)
* App Engine
  - golang v1.11
  - Google Cloud SDK v228.0.0 or higher (`gcloud` command-line utility)
* Cloud Functions
  - Node.js v8.x
  - Firebase CLI v6.2.2 or higher (`firebase` command-line utility)

## Running the app

**To run the Android app:**

* Register the app in your Firebase project with `com.examples.firebase.cryptofirealert`
  as the package name.
* Download the `google-services.json` file from the Firebase project, and copy
  it to the `app/` directory of the Android project.

**To run the server-side components:**

* Download a service account JSON file from your Firebase project.
* Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to point to it.
