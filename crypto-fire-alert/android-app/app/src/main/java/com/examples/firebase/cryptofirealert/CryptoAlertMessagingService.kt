package com.examples.firebase.cryptofirealert

import android.os.Handler
import android.util.Log
import android.widget.Toast
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage

class CryptoAlertMessagingService: FirebaseMessagingService() {

    override fun onMessageReceived(message: RemoteMessage?) {
        message?.notification?.let {
            Log.d(TAG, "Message Notification Body: ${it.body}")
            val mainHandler = Handler(mainLooper)
            mainHandler.post {
                Toast.makeText(applicationContext, "${it.body}", Toast.LENGTH_SHORT).show()
            }

        }

    }

    companion object {
        private const val TAG = "MessagingService"
    }
}