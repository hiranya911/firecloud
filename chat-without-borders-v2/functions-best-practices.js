const functions = require('firebase-functions');
const admin = require('firebase-admin');

// Idempotency
// ===========

functions.auth.user().onCreate(async (user) => {
  await admin.firestore().collection('users').add({
    uid: user.uid,
  });
});



// Promise chains
// ==============

functions.firestore.document('reviews/{reviewId}').onWrite((change, context) => {
  const data = change.after.data();
  admin.firestore().collection('users').doc(data.uid).update({
    reviews: admin.firestore.FieldValue.increment(1),
  });
});



// Global scope and lazy load
// ===========================

functions.firestore.document('reviews/{reviewId}').onWrite((change, context) => {
  const value = expensiveInitialization();
  return admin.firestore().collection('users').doc(data.uid).update({
    reviews: admin.firestore.FieldValue.increment(value.delta),
  });
});

functions.auth.user().onCreate(async (user) => {
  await admin.firestore().collection('users').add({
    uid: user.uid,
  });
});

function expensiveInitialization() {
  // Some time-consuming work.
}