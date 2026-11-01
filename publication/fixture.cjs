// Synthetic WiNet and minimal MQTT broker. Runs only on an internal Docker network.
const http = require('node:http');
const net = require('node:net');
const {WebSocketServer} = require('/usr/src/app/node_modules/ws');
const proof = {language_requests: 0, logins: 0, mqtt_connections: 0, discovery: false, availability: false, reading: false};
http.createServer((req, res) => {
  if (req.url === '/proof') { res.writeHead(200, {'Content-Type': 'application/json'}); return res.end(JSON.stringify(proof)); }
  if (req.url.startsWith('/i18n/')) { proof.language_requests++; res.writeHead(200); return res.end('I18N_COMMON_TOTAL_ACTIVE_POWER=Total active power\n'); }
  res.writeHead(404); res.end();
}).listen(80, '0.0.0.0');
const wss = new WebSocketServer({port: 8082, host: '0.0.0.0'});
wss.on('connection', ws => ws.on('message', raw => {
  const m = JSON.parse(raw);
  const send = data => ws.send(JSON.stringify({result_code: 1, result_msg: 'success', result_data: {service: m.service, ...data}}));
  switch (m.service) {
    case 'connect': return send({token: 'fixture-token', uid: 1, ip: '127.0.0.1', forceModifyPasswd: 0});
    case 'login': proof.logins++; return send({token: 'fixture-token', uid: 1, role: 2});
    case 'devicelist': return send({count: 1, list: [{id: 1, dev_id: 1, dev_code: 3344, dev_type: 0, dev_procotol: 1, inv_type: 0, dev_sn: 'FIXTURE12345', dev_name: 'SG5.0RS', dev_model: 'SG5.0RS', port_name: 'COM1', phys_addr: '1', logc_addr: '1', link_status: 1, init_status: 1, dev_special: '0'}]});
    case 'real': return send({count: 1, list: [{data_name: 'I18N_COMMON_TOTAL_ACTIVE_POWER', data_value: '1.5', data_unit: 'kW'}]});
    case 'direct': return send({count: 0, list: []});
    default: return send({});
  }
}));
net.createServer(socket => {
  let buffer = Buffer.alloc(0);
  socket.on('error', () => {});
  socket.on('data', data => {
    buffer = Buffer.concat([buffer, data]);
    while (buffer.length >= 2) {
      let length = 0, multiplier = 1, n = 1, digit;
      do { if (n >= buffer.length) return; digit = buffer[n++]; length += (digit & 127) * multiplier; multiplier *= 128; } while (digit & 128);
      if (buffer.length < n + length) return;
      const flags = buffer[0], body = buffer.subarray(n, n + length); buffer = buffer.subarray(n + length);
      switch (flags >> 4) {
        case 1: proof.mqtt_connections++; socket.write(Buffer.from([0x20, 2, 0, 0])); break;
        case 3: {
          const topicLength = body.readUInt16BE(0), topic = body.toString('utf8', 2, 2 + topicLength);
          const qos = (flags >> 1) & 3, offset = 2 + topicLength + (qos ? 2 : 0), payload = body.toString('utf8', offset);
          if (qos === 1) socket.write(Buffer.from([0x40, 2, body[2 + topicLength], body[3 + topicLength]]));
          if (topic.endsWith('/status') && payload === 'online') proof.availability = true;
          if (topic.endsWith('/config') && payload) {
            const config = JSON.parse(payload); if (config.state_topic && config.unique_id) proof.discovery = true;
          }
          if (topic.endsWith('/state') && payload) {
            const state = JSON.parse(payload); if (state.value === 1.5 && state.unit_of_measurement === 'kW') proof.reading = true;
          }
          break;
        }
        case 8: socket.write(Buffer.from([0x90, 3, body[0], body[1], 0])); break;
        case 12: socket.write(Buffer.from([0xd0, 0])); break;
        case 14: socket.end(); break;
      }
    }
  });
}).listen(1883, '0.0.0.0');
console.log('fixture-ready');
