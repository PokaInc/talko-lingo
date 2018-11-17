'use strict';


console.log('Hello');

let client, iotTopic;

window.addEventListener('load', function () {
  console.log('All assets are loaded')
  var AWS = require('aws-sdk');
  AWS.config.update({region: 'us-east-1'});
  AWS.config.credentials = new AWS.Credentials("", "");

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
        accessKeyId: "",
        secretKey: "",
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
  var decoded = new TextDecoder("utf-8").decode(message);
  console.log(decoded);
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


