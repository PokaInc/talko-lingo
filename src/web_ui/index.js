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
  if (status === 'SpeechToText') {
    let row = getOrCreateRow(message.JobId);
    activateColumn(row, 'speech-to-text');
  } else if (status === 'Translating') {
    let row = getOrCreateRow(message.JobId);
    activateColumn(row, 'translating', "\"" + message.Data.Text + "\"");
  } else if (status === 'TextToSpeech') {
    let row = getOrCreateRow(message.JobId);
    activateColumn(row, 'text-to-speech', "\"" + message.Data.Text + "\"");
  } else if (status === 'Publishing') {
    let row = getOrCreateRow(message.JobId);
    activateColumn(row, 'publishing');
    window.setTimeout(() => {
      removeRow(row);
    }, 10000);
  } else if (status === 'Error') {
    let row = getOrCreateRow(message.JobId);
    markRowAsError(row);
    window.setTimeout(() => {
      removeRow(row);
    }, 10000);
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

const getRowColumns = (row) => {
  return Array.from(row.getElementsByClassName("col"));
};

const removeProgressBarStripes = (elem) => {
  elem.classList.remove("progress-bar-striped");
  elem.classList.remove("progress-bar-animated");
};

const addProgressBarStripes = (elem) => {
  elem.classList.add("progress-bar-striped");
  elem.classList.add("progress-bar-animated");
};

const activateColumn = (row, columnName, data) => {
  let columns = getRowColumns(row);
  columns.map((elem) => {
    removeProgressBarStripes(elem);
  });

  let elem = row.getElementsByClassName(columnName)[0];

  if (data !== undefined) {
    let dataElem = document.createElement('div');
    dataElem.innerText = data;
    elem.appendChild(dataElem);
  }

  let columnIndex = columns.indexOf(elem);
  for (let i = 0; i <= columnIndex; i++) {
    let column = columns[i];
    column.classList.add("colored");
  }

  addProgressBarStripes(elem);
};

const addRow = (rowId) => {
  let div = document.createElement('div');
  div.classList.add('row');
  div.id = rowId;
  div.innerHTML = '  <div class="speech-to-text col progress-bar">\n' +
    '  Speech to Text\n' +
    '  </div>\n' +
    '  <div class="translating col progress-bar">\n' +
    '  Translating\n' +
    '  </div>\n' +
    '  <div class="text-to-speech col progress-bar">\n' +
    '  Text to Speech\n' +
    '  </div>\n' +
    '  <div class="publishing col progress-bar">\n' +
    '  Publishing\n' +
    '  </div>';

  document.getElementById('mainContainer').appendChild(div);

  adjustRowHeights();

  return div;
};

const removeRow = (row) => {
  row.remove();
  adjustRowHeights();
};

const adjustRowHeights = () => {
  let parent = document.getElementById('mainContainer');

  let childCount = parent.childNodes.length;
  let childHeight = 100 / childCount;

  Array.from(parent.childNodes).map((node) => {
    node.style.height = childHeight + '%';
  });
};

const getOrCreateRow = (rowId) => {
  let row = document.getElementById(rowId);
  if( row === null) {
    row = addRow(rowId);
  }

  return row;
};

const markRowAsError = (row) => {
  row.classList.add('error');
};


