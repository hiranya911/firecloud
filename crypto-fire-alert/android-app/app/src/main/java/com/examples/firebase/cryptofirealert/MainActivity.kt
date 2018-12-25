package com.examples.firebase.cryptofirealert

import android.support.v7.app.AppCompatActivity
import android.os.Bundle
import android.support.v7.app.AlertDialog
import android.util.Log
import android.view.LayoutInflater
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import com.google.firebase.firestore.EventListener
import com.google.firebase.firestore.FirebaseFirestore
import com.google.firebase.firestore.QuerySnapshot
import com.google.firebase.firestore.SetOptions
import com.google.firebase.iid.FirebaseInstanceId
import kotlinx.android.synthetic.main.activity_main.*
import kotlinx.coroutines.experimental.android.UI
import kotlinx.coroutines.experimental.launch
import java.lang.Exception

class MainActivity : AppCompatActivity() {

    companion object {
        private const val TAG = "MainActivity"
    }

    private val db = FirebaseFirestore.getInstance()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        setupPriceListeners()
        setupClickListeners()
    }

    private fun setupPriceListeners() {
        db.collection("prices")
            .addSnapshotListener(EventListener<QuerySnapshot> { value, e ->
                if (e != null) {
                    Log.w(TAG, "Listen failed.", e)
                    return@EventListener
                }
                for (doc in value!!) {
                    val id = resources.getIdentifier(doc.id, "id", packageName)
                    if (id != 0) {
                        val text = "1 ${doc.getString("name")} = ${doc.getDouble("value")} USD"
                        findViewById<TextView>(id).text = text
                    }
                }
            })
    }

    private fun setupClickListeners() {
        this.btc.setOnClickListener {
            createDialog("btc")
        }
        this.eth.setOnClickListener {
            createDialog("eth")
        }
    }

    private fun createDialog(currency: String){
        val view = LayoutInflater.from(this).inflate(R.layout.alert_layout,null)
        val dialog = AlertDialog.Builder(this)
            .setTitle(R.string.set_limits)
            .setMessage(R.string.set_limits_intro)
            .setView(view)
            .create()
        val minEditText = view.findViewById<EditText>(R.id.minimumValue)
        val maxEditText = view.findViewById<EditText>(R.id.maximumValue)

        launch {
            val instanceId = FirebaseInstanceId.getInstance().instanceId.await()
            try {
                val snapshot = db.collection("prefs")
                    .document(instanceId.id).get().await()
                if (snapshot.exists()) {
                    launch (UI) {
                        snapshot.getDouble("${currency}_min")?.let {
                            minEditText.setText(it.toString())
                        }
                        snapshot.getDouble("${currency}_max")?.let {
                            maxEditText.setText(it.toString())
                        }
                    }
                }
            } catch (ex: Exception) {
                Log.w(TAG, "Error while loading existing preferences", ex)
            }
        }

        view.findViewById<Button>(R.id.save).setOnClickListener {
            val min = minEditText.text.toString().toDoubleOrNull()
            val max = maxEditText.text.toString().toDoubleOrNull()
            val error = when {
                min == null -> "Invalid min value"
                max == null -> "Invalid max value"
                min < 0 -> "Min must not be negative"
                min >= max -> "Max must be greater than min"
                else -> null
            }
            if (error != null) {
                Toast.makeText(dialog.context, error, Toast.LENGTH_SHORT).show()
            } else {
                launch {
                    try {
                        savePref(currency, min!!, max!!)
                        launch(UI) {
                            Toast.makeText(
                                this@MainActivity, "$currency preferences saved",
                                Toast.LENGTH_SHORT
                            ).show()
                        }
                    } catch (ex: Exception) {
                        Log.w(TAG, "Error saving preferences", ex)
                    }
                }
                dialog.dismiss()
            }
        }
        dialog.show()
    }

    private suspend fun savePref(currency: String, min: Double, max: Double) {
        val instanceId = FirebaseInstanceId.getInstance().instanceId.await()
        val data = mapOf(
            "${currency}_min" to min,
            "${currency}_max" to max,
            "token" to instanceId.token
        )
        db.collection("prefs").document(instanceId.id)
            .set(data, SetOptions.merge()).await()
    }
}
