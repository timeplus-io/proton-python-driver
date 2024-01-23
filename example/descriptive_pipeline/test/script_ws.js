import ws from 'k6/ws';
import { check } from 'k6';

export const options = {
    vus: 1,
    duration: '30s',
};

export default function () {
  const url = 'ws://localhost:5001/queries/pipeline1';

  const res = ws.connect(url, {}, function (socket) {
    socket.on('open', () => console.log('connected'));
    socket.on('close', () => console.log('disconnected'));

    socket.setTimeout(function () {
        console.log('2 seconds passed, closing the socket');
        socket.close();
      }, 1000 * 30);
  });

  check(res, { 'status is 101': (r) => r && r.status === 101 });
}