/**
 * Metrics Parser Utility
 *
 * Parses Prometheus-format metrics from API Gateway.
 * Extracts:
 * - Total requests
 * - Error rate
 * - Average latency
 */

export const parseMetrics = (text) => {
  let totalRequests = 0;
  let errorRequests = 0;
  let totalLatencySum = 0;
  let totalLatencyCount = 0;

  const lines = text.split('\n');
  const requestRegex = /api_requests_total{.*status_code="(\d{3})".*} (\d+\.?\d*)/;

  lines.forEach(line => {
    if (line.startsWith('#') || line.trim() === '') return;

    const requestMatch = line.match(requestRegex);
    if (requestMatch) {
      const statusCode = parseInt(requestMatch[1], 10);
      const value = parseFloat(requestMatch[2]);

      totalRequests += value;
      if (statusCode < 200 || statusCode >= 300) {
        errorRequests += value;
      }
    } else if (line.startsWith('api_response_time_seconds_sum')) {
      totalLatencySum += parseFloat(line.split(' ')[1]);
    } else if (line.startsWith('api_response_time_seconds_count')) {
      totalLatencyCount += parseFloat(line.split(' ')[1]);
    }
  });

  const averageLatency = totalLatencyCount > 0 ? (totalLatencySum / totalLatencyCount) * 1000 : 0;
  const errorRate = totalRequests > 0 ? (errorRequests / totalRequests) * 100 : 0;

  return {
    totalRequests,
    averageLatency: Math.round(averageLatency),
    errorRate: errorRate.toFixed(2)
  };
};

export default parseMetrics;
