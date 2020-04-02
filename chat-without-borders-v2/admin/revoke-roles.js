const admin = require('firebase-admin');

const app = admin.initializeApp();
const email = 'hkj@google.com';

admin.auth().getUserByEmail(email)
  .then((user) => {
    console.log(`Revoking roles from ${user.email} (${user.uid})`);
    return admin.auth().setCustomUserClaims(user.uid, {});
  })
  .then(() => {
    app.delete();
  })
  .catch((err) => {
    console.log(err);
  });