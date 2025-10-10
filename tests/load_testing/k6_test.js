// K6 Load Test Script para MAXIMUS AI
// Execute: k6 run k6_test.js

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Métricas customizadas
const errorRate = new Rate('errors');

// Configuração do teste
export const options = {
  stages: [
    { duration: '2m', target: 10 },   // Ramp-up para 10 users
    { duration: '5m', target: 10 },   // Stay at 10 users
    { duration: '2m', target: 50 },   // Ramp-up para 50 users
    { duration: '5m', target: 50 },   // Stay at 50 users
    { duration: '2m', target: 100 },  // Ramp-up para 100 users
    { duration: '5m', target: 100 },  // Stay at 100 users
    { duration: '3m', target: 0 },    // Ramp-down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'], // 95% < 500ms, 99% < 1s
    http_req_failed: ['rate<0.05'],  // Error rate < 5%
    errors: ['rate<0.1'],            // Custom error rate < 10%
  },
};

const BASE_URL = 'http://localhost:8000';

export default function () {
  // Test 1: Health Check
  let healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, {
    'health status 200': (r) => r.status === 200,
    'health response time < 200ms': (r) => r.timings.duration < 200,
  }) || errorRate.add(1);

  sleep(1);

  // Test 2: Consciousness Query
  const consciousnessPayload = JSON.stringify({
    query: 'What is your current state?',
    context: { user_id: 'k6_test_user' }
  });
  
  let consciousnessRes = http.post(
    `${BASE_URL}/api/v1/consciousness/query`,
    consciousnessPayload,
    { headers: { 'Content-Type': 'application/json' } }
  );
  
  check(consciousnessRes, {
    'consciousness status 200': (r) => r.status === 200,
    'consciousness response time < 1s': (r) => r.timings.duration < 1000,
  }) || errorRate.add(1);

  sleep(1);

  // Test 3: Memory Operations
  const memoryPayload = JSON.stringify({
    timestamp: new Date().toISOString(),
    event_type: 'k6_test_event',
    data: { test: true },
    importance: 0.8
  });
  
  let memoryRes = http.post(
    `${BASE_URL}/api/v1/memory/episodic`,
    memoryPayload,
    { headers: { 'Content-Type': 'application/json' } }
  );
  
  check(memoryRes, {
    'memory store status 200/201': (r) => r.status === 200 || r.status === 201,
    'memory response time < 500ms': (r) => r.timings.duration < 500,
  }) || errorRate.add(1);

  sleep(2);
}

// Função executada no final do teste
export function handleSummary(data) {
  return {
    'load_test_summary.json': JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}
