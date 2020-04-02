const admin = require('firebase-admin');

const app = admin.initializeApp();

const email = 'hkj@google.com';
admin.auth().getUserByEmail(email)
  .then((user) => {
    console.log(`Granting moderator role to ${user.email} (${user.uid})`);
    return admin.auth().setCustomUserClaims(user.uid, {role: 'moderator'});
  })
  .then(() => {
    app.delete();
  })
  .catch((err) => {
    console.log(err);
  });
