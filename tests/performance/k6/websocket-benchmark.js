import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Counter, Trend } from 'k6/metrics';

const messagesSent = new Counter('ws_messages_sent_total');
const messagesReceived = new Counter('ws_messages_received_total');
const latency = new Trend('ws_message_latency', true);

export const options = {
  vus: Number(__ENV.K6_VUS || 20),
  duration: __ENV.K6_DURATION || '5m',
  thresholds: {
    ws_message_latency: ['p(95)<500'],
    ws_messages_received_total: ['count>0'],
  },
};

const TARGET_URL = __ENV.BENCH_TARGET_WS_URL || 'ws://localhost:8001/stream/consciousness/ws';
const MESSAGE_INTERVAL = Number(__ENV.MESSAGE_INTERVAL_MS || 1000);

export default function () {
  const res = ws.connect(TARGET_URL, {}, function (socket) {
    const start = Date.now();
    socket.on('open', function () {
      socket.setInterval(function () {
        const sent = Date.now();
        socket.send(JSON.stringify({ type: 'ping', timestamp: sent }));
        messagesSent.add(1);
      }, MESSAGE_INTERVAL);
    });

    socket.on('message', function (data) {
      messagesReceived.add(1);
      try {
        const payload = JSON.parse(data);
        if (payload.timestamp) {
          latency.add(Date.now() - payload.timestamp);
        }
      } catch (_e) {
        // ignore parse errors
      }
    });

    socket.on('close', function () {
      const duration = Date.now() - start;
      console.log(`WS closed after ${duration}ms`);
    });

    socket.on('error', function (e) {
      console.error('WS error: ', e.error());
    });

    sleep(1);
  });

  check(res, { 'status is 101': (r) => r && r.status === 101 });
}
