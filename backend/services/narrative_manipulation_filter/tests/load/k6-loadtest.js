/**
 * ============================================================================
 * K6 Load Testing Script - Cognitive Defense System
 * ============================================================================
 *
 * Run with:
 *   k6 run k6-loadtest.js
 *
 * With options:
 *   k6 run --vus 100 --duration 5m k6-loadtest.js
 *
 * Cloud execution:
 *   k6 cloud k6-loadtest.js
 */

import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import { randomItem, randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// ============================================================================
// CONFIGURATION
// ============================================================================

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8013';

// Test stages - gradual ramp-up and ramp-down
export const options = {
  stages: [
    { duration: '2m', target: 10 },   // Warm-up: ramp to 10 users
    { duration: '3m', target: 50 },   // Ramp-up: increase to 50 users
    { duration: '5m', target: 100 },  // Peak: maintain 100 users
    { duration: '3m', target: 200 },  // Stress: push to 200 users
    { duration: '2m', target: 0 },    // Ramp-down: cool down
  ],

  // Thresholds - SLA requirements
  thresholds: {
    // HTTP errors should be less than 1%
    'http_req_failed': ['rate<0.01'],

    // 95% of requests should be below 500ms (Tier 1)
    'http_req_duration': ['p(95)<500'],

    // 99% of requests should be below 2000ms (Standard)
    'http_req_duration{mode:standard}': ['p(99)<2000'],

    // 99% of deep analysis should be below 5000ms
    'http_req_duration{mode:deep}': ['p(99)<5000'],

    // Custom metrics
    'analysis_success_rate': ['rate>0.95'],
    'manipulation_detection_rate': ['rate>0.30'],  // At least 30% should detect manipulation
  },

  // Browser-like user behavior
  userAgent: 'K6 Load Test / Cognitive Defense System',

  // Connection settings
  insecureSkipTLSVerify: true,  // For self-signed certs in dev
  noConnectionReuse: false,
  noVUConnectionReuse: false,
};

// ============================================================================
// CUSTOM METRICS
// ============================================================================

const analysisSuccessRate = new Rate('analysis_success_rate');
const manipulationDetectionRate = new Rate('manipulation_detection_rate');
const avgManipulationScore = new Trend('avg_manipulation_score');
const analysisErrors = new Counter('analysis_errors');

// ============================================================================
// TEST DATA
// ============================================================================

const FAKE_NEWS_SAMPLES = [
  "Governo anuncia que vai distribuir R$ 10.000 para todos os brasileiros na próxima semana!",
  "Cientistas descobrem que vacinas causam autismo, estudo comprova teoria!",
  "Político corrupto confessa desvio de bilhões em vídeo vazado!",
  "Novo tratamento milagroso cura câncer em 24 horas, médicos confirmam!",
  "País vai adotar moeda digital e acabar com o Real a partir de amanhã!",
];

const REAL_NEWS_SAMPLES = [
  "Ministério da Saúde divulga novo boletim epidemiológico com dados atualizados.",
  "Congresso aprova projeto de lei após amplo debate parlamentar.",
  "Pesquisa do IBGE mostra crescimento da economia no último trimestre.",
  "Universidade publica estudo sobre mudanças climáticas no Brasil.",
  "Banco Central mantém taxa de juros em 10,5% ao ano.",
];

const PROPAGANDA_SAMPLES = [
  "Vote no candidato X! Ele é o ÚNICO que pode salvar o Brasil da destruição total!",
  "Nossos adversários querem destruir tudo que é sagrado! Não deixe isso acontecer!",
  "A oposição é composta INTEIRAMENTE por comunistas e criminosos!",
  "Se você não votar em mim, o país vai virar uma Venezuela! É agora ou nunca!",
];

const SOURCE_DOMAINS = [
  "nytimes.com",
  "bbc.com",
  "folha.uol.com.br",
  "estadao.com.br",
  "g1.globo.com",
  "unknown-blog.com",
  "fake-news-site.net",
  "suspicious-news.org",
];

const ALL_CONTENT = [...FAKE_NEWS_SAMPLES, ...REAL_NEWS_SAMPLES, ...PROPAGANDA_SAMPLES];

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

function getRandomContent() {
  return randomItem(ALL_CONTENT);
}

function getRandomSource() {
  return randomItem(SOURCE_DOMAINS);
}

function buildAnalysisPayload(mode = 'STANDARD') {
  return {
    content: getRandomContent(),
    source_info: {
      domain: getRandomSource(),
      url: `https://${getRandomSource()}/article/${randomIntBetween(1, 999999)}`,
      timestamp: new Date().toISOString(),
    },
    mode: mode,
  };
}

// ============================================================================
// SETUP & TEARDOWN
// ============================================================================

export function setup() {
  console.log('🚀 Starting Cognitive Defense Load Test');
  console.log(`📍 Target: ${BASE_URL}`);

  // Verify service is up
  const healthCheck = http.get(`${BASE_URL}/health`);

  if (healthCheck.status !== 200) {
    throw new Error(`Service not healthy: ${healthCheck.status}`);
  }

  console.log('✅ Service is healthy, starting test...\n');

  return {
    startTime: new Date(),
  };
}

export function teardown(data) {
  const duration = (new Date() - data.startTime) / 1000;
  console.log(`\n✅ Test completed in ${duration.toFixed(2)} seconds`);
}

// ============================================================================
// MAIN TEST SCENARIO
// ============================================================================

export default function () {
  // Simulate different user behaviors with weighted probabilities

  const scenario = Math.random();

  if (scenario < 0.5) {
    // 50% - Fast analysis (Tier 1 only)
    analyzeFastTrack();
  } else if (scenario < 0.8) {
    // 30% - Standard analysis (Tier 1 + Tier 2)
    analyzeStandard();
  } else if (scenario < 0.9) {
    // 10% - Deep analysis (Full KG verification)
    analyzeDeep();
  } else {
    // 10% - Other endpoints (history, metrics, etc.)
    otherEndpoints();
  }

  // Think time (simulate user reading results)
  sleep(randomIntBetween(1, 3));
}

// ============================================================================
// TEST SCENARIOS
// ============================================================================

function analyzeFastTrack() {
  group('Fast Track Analysis', function () {
    const payload = buildAnalysisPayload('FAST_TRACK');

    const response = http.post(
      `${BASE_URL}/api/v2/analyze`,
      JSON.stringify(payload),
      {
        headers: { 'Content-Type': 'application/json' },
        tags: { mode: 'fast' },
      }
    );

    // Assertions
    const success = check(response, {
      'status is 200': (r) => r.status === 200,
      'response time < 500ms': (r) => r.timings.duration < 500,
      'has manipulation_score': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.hasOwnProperty('manipulation_score');
        } catch (e) {
          return false;
        }
      },
      'has threat_level': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.hasOwnProperty('threat_level');
        } catch (e) {
          return false;
        }
      },
    });

    // Custom metrics
    analysisSuccessRate.add(success);

    if (success) {
      try {
        const result = JSON.parse(response.body);
        avgManipulationScore.add(result.manipulation_score);

        if (result.manipulation_score > 0.5) {
          manipulationDetectionRate.add(1);
        } else {
          manipulationDetectionRate.add(0);
        }
      } catch (e) {
        analysisErrors.add(1);
      }
    } else {
      analysisErrors.add(1);
    }
  });
}

function analyzeStandard() {
  group('Standard Analysis', function () {
    const payload = buildAnalysisPayload('STANDARD');

    const response = http.post(
      `${BASE_URL}/api/v2/analyze`,
      JSON.stringify(payload),
      {
        headers: { 'Content-Type': 'application/json' },
        tags: { mode: 'standard' },
      }
    );

    const success = check(response, {
      'status is 200': (r) => r.status === 200,
      'response time < 2000ms': (r) => r.timings.duration < 2000,
      'has full analysis': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.credibility_score !== undefined &&
                 body.emotional_score !== undefined &&
                 body.fallacy_count !== undefined;
        } catch (e) {
          return false;
        }
      },
    });

    analysisSuccessRate.add(success);

    if (!success) {
      analysisErrors.add(1);
    }
  });
}

function analyzeDeep() {
  group('Deep Analysis', function () {
    const payload = buildAnalysisPayload('DEEP_ANALYSIS');

    const response = http.post(
      `${BASE_URL}/api/v2/analyze`,
      JSON.stringify(payload),
      {
        headers: { 'Content-Type': 'application/json' },
        tags: { mode: 'deep' },
        timeout: '10s',  // Longer timeout for deep analysis
      }
    );

    const success = check(response, {
      'status is 200': (r) => r.status === 200,
      'response time < 5000ms': (r) => r.timings.duration < 5000,
      'has verified claims': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.verified_claims !== undefined;
        } catch (e) {
          return false;
        }
      },
    });

    analysisSuccessRate.add(success);

    if (!success) {
      analysisErrors.add(1);
    }
  });
}

function otherEndpoints() {
  group('Other Endpoints', function () {
    // History endpoint
    const historyResponse = http.get(`${BASE_URL}/api/v2/history?limit=10`);
    check(historyResponse, {
      'history status is 200': (r) => r.status === 200,
    });

    // Health check
    const healthResponse = http.get(`${BASE_URL}/health`);
    check(healthResponse, {
      'health status is 200': (r) => r.status === 200,
      'service is healthy': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.status === 'healthy';
        } catch (e) {
          return false;
        }
      },
    });

    // Metrics endpoint
    const metricsResponse = http.get(`${BASE_URL}/metrics`);
    check(metricsResponse, {
      'metrics status is 200': (r) => r.status === 200,
    });
  });
}

// ============================================================================
// ADVANCED SCENARIOS (Optional)
// ============================================================================

// Spike test - sudden traffic spike
export const spikeTest = {
  executor: 'ramping-arrival-rate',
  startRate: 10,
  timeUnit: '1s',
  preAllocatedVUs: 50,
  maxVUs: 500,
  stages: [
    { duration: '2m', target: 10 },   // Normal load
    { duration: '30s', target: 500 }, // Spike!
    { duration: '2m', target: 10 },   // Back to normal
  ],
};

// Soak test - prolonged steady load
export const soakTest = {
  executor: 'constant-vus',
  vus: 50,
  duration: '30m',
};

// Stress test - find breaking point
export const stressTest = {
  executor: 'ramping-vus',
  startVUs: 0,
  stages: [
    { duration: '2m', target: 100 },
    { duration: '5m', target: 200 },
    { duration: '5m', target: 300 },
    { duration: '5m', target: 400 },
    { duration: '2m', target: 0 },
  ],
};

// ============================================================================
// USAGE EXAMPLES
// ============================================================================
/*
# Basic test
k6 run k6-loadtest.js

# With custom VUs and duration
k6 run --vus 100 --duration 5m k6-loadtest.js

# With environment variable
k6 run --env BASE_URL=https://api.vertice.dev k6-loadtest.js

# Output results to JSON
k6 run --out json=results.json k6-loadtest.js

# Cloud execution
k6 cloud k6-loadtest.js

# InfluxDB + Grafana
k6 run --out influxdb=http://localhost:8086/k6 k6-loadtest.js
*/
