import * as functions from 'firebase-functions';
import * as admin from 'firebase-admin';

admin.initializeApp();

export const trackActivity = functions.firestore
  .document(`restaurants/{restaurantId}/ratings/{ratingId}`)
  .onCreate(async (snapshot, context) => {
    const data: {userId: string} = snapshot.data() as any;
    const uid = data.userId;
    const doc = admin.firestore().collection('activities').doc(uid);
    await admin.firestore().runTransaction(async (txn) => {
      const snap = await txn.get(doc);
      const activityData = snap.data() || {};
      const count = activityData.count || 0;
      txn.set(doc, {count: count + 1}, {merge: true});
    });

    return true;
  });
