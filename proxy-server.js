const express = require('express');
const request = require('request');
const path = require('path');
const cors = require('cors');  

const app = express();
const PORT = 8000;


app.use(cors());


app.use(express.static(path.join(__dirname, 'public')));

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});


app.post('/payment/poscloud/nexo/payment', (req, res) => {
  const url = 'https://uscst-pos.gsc.vficloud.net/oidc/poscloud/nexo/payment';
  const headers = {
   'Authorization': "Basic MGY2ZDI4ZmYtZWJmMi00ZjRlLWEzZTItZjk0ZTJmMmMxMmM3OmZjRGJYUFJSRVdwZFJ4c2pwcFFydk1RaHdhc3lKdXhYTUJtbw==",

    'x-site-entity-id':'4c6664c7-733e-4d12-a75c-9796a59c9fd8',
    'Content-Type': 'application/json'
  };

  req.pipe(
    request.post({
      uri: url,
      json: true,
      headers: headers,
      body: req.body
    })
  ).pipe(res);
});

app.post('/payment/reversal', (req, res) => {
  const url = 'https://uscst-pos.gsc.vficloud.net/oidc/poscloud/nexo/v2/reversal';
  const headers = {
    'Authorization': "Basic MGY2ZDI4ZmYtZWJmMi00ZjRlLWEzZTItZjk0ZTJmMmMxMmM3OmZjRGJYUFJSRVdwZFJ4c2pwcFFydk1RaHdhc3lKdXhYTUJtbw==",
    'x-site-entity-id': '4c6664c7-733e-4d12-a75c-9796a59c9fd8',
    'Content-Type': 'application/json'
  };

  req.pipe(
    request.post({
      uri: url,
      json: true,
      headers: headers,
      body: req.body
    })
  ).pipe(res);
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
