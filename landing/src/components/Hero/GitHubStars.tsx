/**
 * ═══════════════════════════════════════════════════════════════════════════
 * GITHUB STARS COMPONENT - React Island
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Componente React que busca REAL GitHub stars count via API.
 * Renderiza no cliente (client:load) para evitar rate limits durante build.
 *
 * Features:
 * - Fetch real da API do GitHub
 * - Loading state
 * - Error handling gracioso
 * - Fallback para valor hardcoded se API falhar
 * - Cache no localStorage (opcional)
 *
 * Zero mocks. Zero placeholders. Production-ready.
 */

import { useState, useEffect } from 'react';

interface GitHubStarsProps {
  repo?: string;
  fallbackCount?: number;
}

export default function GitHubStars({
  repo = 'JuanCS-Dev/V-rtice',
  fallbackCount = 0
}: GitHubStarsProps) {
  const [stars, setStars] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const fetchStars = async () => {
      try {
        // Check localStorage cache first (24h TTL)
        const cacheKey = `gh-stars-${repo}`;
        const cached = localStorage.getItem(cacheKey);

        if (cached) {
          const { stars: cachedStars, timestamp } = JSON.parse(cached);
          const isExpired = Date.now() - timestamp > 24 * 60 * 60 * 1000; // 24h

          if (!isExpired) {
            setStars(cachedStars);
            setLoading(false);
            return;
          }
        }

        // Fetch from GitHub API
        const response = await fetch(`https://api.github.com/repos/${repo}`, {
          headers: {
            'Accept': 'application/vnd.github.v3+json',
          },
        });

        if (!response.ok) {
          throw new Error(`GitHub API error: ${response.status}`);
        }

        const data = await response.json();
        const starCount = data.stargazers_count;

        // Save to cache
        localStorage.setItem(cacheKey, JSON.stringify({
          stars: starCount,
          timestamp: Date.now(),
        }));

        setStars(starCount);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching GitHub stars:', err);
        setError(true);
        setLoading(false);

        // Fallback to hardcoded value
        if (fallbackCount > 0) {
          setStars(fallbackCount);
        }
      }
    };

    fetchStars();
  }, [repo, fallbackCount]);

  // Format number with K suffix for thousands
  const formatStars = (count: number): string => {
    if (count >= 1000) {
      return `${(count / 1000).toFixed(1)}k`;
    }
    return count.toString();
  };

  if (loading) {
    return (
      <span className="gh-stars-loading">
        <span className="gh-stars-skeleton"></span>
      </span>
    );
  }

  if (error && !stars) {
    return (
      <span className="gh-stars-text">
        GitHub
      </span>
    );
  }

  return (
    <span className="gh-stars-wrapper">
      <span className="gh-stars-icon">⭐</span>
      <span className="gh-stars-count">{stars !== null ? formatStars(stars) : fallbackCount}</span>
    </span>
  );
}
