'use strict';


console.log('Hello');

let client, iotTopic;

window.addEventListener('load', function () {
  console.log('All assets are loaded');

  let awsAccessKeyId = localStorage.getItem('awsAccessKeyId');
  let awsSecretAccessKey = localStorage.getItem('awsSecretAccessKey');

  if (awsAccessKeyId === null) {
    document.getElementById('awsKeys').style.display = 'block';
    document.getElementById("submitBtn").addEventListener("click", function () {
      let awsAccessKeyId = document.getElementById('awsAccessKeyId').value;
      let awsSecretAccessKey = document.getElementById('awsSecretAccessKey').value;

      localStorage.setItem('awsAccessKeyId', awsAccessKeyId);
      localStorage.setItem('awsSecretAccessKey', awsSecretAccessKey);

      document.getElementById('awsKeys').style.display = 'none';
    });
  }

  var AWS = require('aws-sdk');
  AWS.config.update({region: 'us-east-1'});
  AWS.config.credentials = new AWS.Credentials(awsAccessKeyId, awsSecretAccessKey);

  var AWSIoTData = require('aws-iot-device-sdk');
  var iot = new AWS.Iot();

  iot.describeEndpoint({
    endpointType: 'iot:Data-ATS'
  }, function (err, data) {
    if (err) {
      console.log(err, err.stack); // an error occurred
    }
    else {
      console.log(data); // successful response
      client = AWSIoTData.device({
        region: AWS.config.region,
        protocol: 'wss',
        accessKeyId: awsAccessKeyId,
        secretKey: awsSecretAccessKey,
        // sessionToken: 'something',
        // port: 8000,
        host: data.endpointAddress
      });


      client.on('connect', onConnect);
      client.on('message', onMessage);
      client.on('error', onError);
      client.on('reconnect', onReconnect);
      client.on('offline', onOffline);
      client.on('close', onClose);
    }
  });

});


const onConnect = () => {
  console.log('Connected');
  client.subscribe('talko/job_status')
};

const onMessage = (topic, message) => {
  console.log('Message');
  message = JSON.parse(new TextDecoder("utf-8").decode(message));
  console.log(message);
  let status = message.Status;
  console.log(status);
  if (status === 'Transcribing') {
    resetColumns();
    let row = addRow(message.JobId);
    console.log(row)

    let elem = document.getElementById("transcribing");
    activateColumn(elem);
  } else if (status === 'Translating') {
    let elem = document.getElementById("translating");
    activateColumn(elem);
  } else if (status === 'Pollying') {
    let elem = document.getElementById("pollying");
    activateColumn(elem);
  } else if (status === 'Publishing') {
    let elem = document.getElementById("publishing");
    activateColumn(elem);
  }
};

const onError = () => {
  console.log('onError');
};
const onReconnect = () => {
  console.log('onReconnect');
};
const onOffline = () => {
  console.log('onOffline');
};

const onClose = () => {
  console.log('onClose');
};

const getAllColumnElems = () => {
  return [
    document.getElementById("transcribing"),
    document.getElementById("translating"),
    document.getElementById("pollying"),
    document.getElementById("publishing"),
  ]
};

const resetColumns = () => {
  let elems = getAllColumnElems();
  elems.map((elem) => {
    elem.classList.remove("colored");
    removeProgressBarStripes(elem);
  });
};

const removeProgressBarStripes = (elem) => {
  elem.classList.remove("progress-bar-striped");
  elem.classList.remove("progress-bar-animated");
};

const addProgressBarStripes = (elem) => {
  elem.classList.add("progress-bar-striped");
  elem.classList.add("progress-bar-animated");
};

const activateColumn = (elem) => {
  let elems = getAllColumnElems();
  elems.map((elem) => {
    removeProgressBarStripes(elem);
  });

  elem.classList.add("colored");
  addProgressBarStripes(elem);
};

// <div class="row">
//   <div id="transcribing" class="transcribing col progress-bar">
//   Transcribing
//   </div>
//   <div id="translating" class="col progress-bar">
//   Translating
//   </div>
//   <div id="pollying" class="col progress-bar">
//   Pollying
//   </div>
//   <div id="publishing" class="col progress-bar">
//   Publishing
//   </div>
//   </div>

const addRow = (rowId) => {
  let div = document.createElement('div');
  div.classList.add('row');
  div.id = rowId;
  div.innerHTML = '  <div class="transcribing col progress-bar">\n' +
    '  Transcribing\n' +
    '  </div>\n' +
    '  <div class="translating col progress-bar">\n' +
    '  Translating\n' +
    '  </div>\n' +
    '  <div class="pollying col progress-bar">\n' +
    '  Pollying\n' +
    '  </div>\n' +
    '  <div class="publishing col progress-bar">\n' +
    '  Publishing\n' +
    '  </div>';

  document.getElementById('mainContainer').appendChild(div);

  return div;
};

const getRow = (rowId) => {
  return document.getElementById(rowId);
};


