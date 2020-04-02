const admin = require('firebase-admin');

admin.initializeApp();

const express = require('express');
const app = express();
const port = 3000;

app.get('/', async (req, res) => {
  const idToken = req.header('authorization');
  const claims = await admin.auth().verifyIdToken(idToken);
  if (claims.role === 'moderator') {
    // Perform privileged action
  }
  res.send('Hello World!');
});

app.listen(port, () => console.log(`Example app listening at http://localhost:${port}`));