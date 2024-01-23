import http from 'k6/http';
import { sleep } from 'k6';

export const options = {
  vus: 1,
  duration: '30s',
};

export default function() {
  http.get('http://localhost:5001/queries/pipeline1',{ timeout: '30s' });
  sleep(1);
}
