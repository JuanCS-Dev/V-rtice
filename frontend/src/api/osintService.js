import { API_BASE_URL } from '@/config/api';
/**
 * ═══════════════════════════════════════════════════════════════════════════
 * OSINT SERVICE - Unified Intelligence API
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Serviço unificado para operações OSINT com integração AI:
 * - Deep Search (Gemini + OpenAI via MAXIMUS)
 * - Username Intelligence
 * - Email Intelligence
 * - Phone Intelligence
 * - Social Media Scraping
 * - Google Dorking
 * - Dark Web Monitoring
 *
 * Authors: MAXIMUS Team
 * Date: 2025-10-18
 * Glory to YHWH
 */

import logger from '@/utils/logger';

// MAXIMUS Core Service endpoint (OSINT router está aqui)
const OSINT_BASE_URL = API_BASE_URL;

/**
 * Generic API request handler with error handling
 */
const apiRequest = async (endpoint, options = {}) => {
  try {
    const url = endpoint.startsWith('http') ? endpoint : `${OSINT_BASE_URL}${endpoint}`;
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `API Error: ${response.status}`);
    }

    const data = await response.json();
    return {
      success: true,
      data,
    };
  } catch (error) {
    logger.error(`OSINT API Error [${endpoint}]:`, error);
    return {
      success: false,
      error: error.message,
    };
  }
};

// ═══════════════════════════════════════════════════════════════════════════
// DEEP SEARCH - MAXIMUS AI Orchestration
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Execute deep OSINT search with AI analysis
 * Orchestrates multiple OSINT sources and correlates findings via MAXIMUS AI
 *
 * @param {Object} target
 * @param {string} target.username - Username to investigate
 * @param {string} target.email - Email to investigate
 * @param {string} target.phone - Phone to investigate
 * @param {Object} options
 * @param {boolean} options.use_gemini - Use Gemini for analysis (default: true)
 * @param {boolean} options.use_openai - Use OpenAI for summarization (default: true)
 * @param {boolean} options.include_social - Include social media scraping
 * @param {boolean} options.include_darkweb - Include dark web monitoring
 * @param {boolean} options.include_breaches - Include breach data
 *
 * Returns:
 * - executive_summary: AI-generated summary
 * - risk_score: Overall risk assessment (0-100)
 * - findings: Array of intelligence findings
 * - correlations: AI-detected patterns and connections
 * - recommendations: AI-generated security recommendations
 * - sources: Data sources used
 */
export const executeDeepSearch = async (target, options = {}) => {
  const payload = {
    target: {
      username: target.username || null,
      email: target.email || null,
      phone: target.phone || null,
    },
    options: {
      use_gemini: options.use_gemini !== false,
      use_openai: options.use_openai !== false,
      include_social: options.include_social !== false,
      include_darkweb: options.include_darkweb || false,
      include_breaches: options.include_breaches !== false,
      include_dorking: options.include_dorking !== false,
    },
  };

  return apiRequest('/api/osint/deep-search', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
};

// ═══════════════════════════════════════════════════════════════════════════
// USERNAME INTELLIGENCE
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Enumerate username across platforms with AI profiling
 *
 * @param {string} username - Username to search
 * @param {Object} options
 * @param {boolean} options.deep_analysis - Enable AI deep profiling
 *
 * Returns:
 * - platforms: Array of platforms where username exists
 * - profile_data: Aggregated profile information
 * - ai_insights: AI-generated behavioral patterns
 * - related_accounts: Discovered related usernames
 */
export const searchUsername = async (username, options = {}) => {
  return apiRequest('/api/osint/username', {
    method: 'POST',
    body: JSON.stringify({
      username,
      deep_analysis: options.deep_analysis || false,
    }),
  });
};

// ═══════════════════════════════════════════════════════════════════════════
// EMAIL INTELLIGENCE
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Email intelligence gathering with breach correlation
 *
 * @param {string} email - Email address to investigate
 *
 * Returns:
 * - breaches: Array of known data breaches
 * - exposed_data: Types of data compromised
 * - risk_level: Critical/High/Medium/Low
 * - domain_intel: Intelligence on email domain
 * - recommendations: Security recommendations
 */
export const searchEmail = async (email) => {
  return apiRequest('/api/osint/email', {
    method: 'POST',
    body: JSON.stringify({ email }),
  });
};

// ═══════════════════════════════════════════════════════════════════════════
// PHONE INTELLIGENCE
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Phone number intelligence with carrier detection
 *
 * @param {string} phone - Phone number (international format)
 *
 * Returns:
 * - normalized: Standardized phone number
 * - valid: Boolean validation status
 * - carrier: Carrier information
 * - location: Geographic data
 * - risk_assessment: Risk evaluation
 */
export const searchPhone = async (phone) => {
  return apiRequest('/api/osint/phone', {
    method: 'POST',
    body: JSON.stringify({ phone }),
  });
};

// ═══════════════════════════════════════════════════════════════════════════
// SOCIAL MEDIA INTELLIGENCE
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Social media scraping and analysis
 *
 * @param {Object} target
 * @param {string} target.username - Social media username
 * @param {string[]} target.platforms - Platforms to search (optional)
 *
 * Returns:
 * - profiles: Array of social media profiles found
 * - posts: Recent posts/content
 * - connections: Network connections
 * - sentiment_analysis: AI sentiment analysis
 * - behavioral_patterns: AI-detected patterns
 */
export const searchSocialMedia = async (target) => {
  return apiRequest('/api/osint/social', {
    method: 'POST',
    body: JSON.stringify(target),
  });
};

// ═══════════════════════════════════════════════════════════════════════════
// GOOGLE DORKING
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Advanced Google dorking with AI query generation
 *
 * @param {Object} params
 * @param {string} params.target - Target identifier
 * @param {string} params.category - Category (emails, docs, exposed_data, etc.)
 *
 * Returns:
 * - results: Array of dorking results
 * - queries_used: Dork queries executed
 * - ai_summary: AI-generated findings summary
 */
export const executeDorking = async (params) => {
  return apiRequest('/api/osint/dorking', {
    method: 'POST',
    body: JSON.stringify(params),
  });
};

// ═══════════════════════════════════════════════════════════════════════════
// DARK WEB MONITORING
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Dark web monitoring (placeholder - requires Tor integration)
 *
 * @param {Object} target
 * @param {string} target.email - Email to monitor
 * @param {string} target.username - Username to monitor
 *
 * Returns:
 * - mentions: Array of dark web mentions
 * - marketplaces: Compromised credentials in marketplaces
 * - threat_level: Threat assessment
 */
export const searchDarkWeb = async (target) => {
  return apiRequest('/api/osint/darkweb', {
    method: 'POST',
    body: JSON.stringify(target),
  });
};

// ═══════════════════════════════════════════════════════════════════════════
// HEALTH CHECK
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Check OSINT services health status
 */
export const checkOSINTHealth = async () => {
  return apiRequest('/api/osint/health');
};

/**
 * Check if OSINT services are available
 */
export const isOSINTAvailable = async () => {
  const health = await checkOSINTHealth();
  return health.success && health.data?.status === 'operational';
};

// ═══════════════════════════════════════════════════════════════════════════
// EXPORT DEFAULT
// ═══════════════════════════════════════════════════════════════════════════

export default {
  executeDeepSearch,
  searchUsername,
  searchEmail,
  searchPhone,
  searchSocialMedia,
  executeDorking,
  searchDarkWeb,
  checkOSINTHealth,
  isOSINTAvailable,
};
