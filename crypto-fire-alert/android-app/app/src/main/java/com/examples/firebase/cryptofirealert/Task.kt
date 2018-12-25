package com.examples.firebase.cryptofirealert

import com.google.android.gms.tasks.Task
import kotlinx.coroutines.experimental.suspendCancellableCoroutine

suspend fun <T> Task<T>.await() =
    suspendCancellableCoroutine<T> {
        this.addOnSuccessListener(it::resume)
        this.addOnFailureListener(it::resumeWithException)
        this.addOnCanceledListener { it.cancel() }
    }