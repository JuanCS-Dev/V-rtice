/**
 * ═══════════════════════════════════════════════════════════════════════════
 * DASHBOARD CAROUSEL - Vertical Perspective Carousel
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Carrossel vertical com efeito de perspectiva 3D:
 * - Imagem ativa no centro (escala 1.0, opacity 1.0, z-index alto)
 * - Imagem anterior acima (escala 0.85, opacity 0.5, metade visível)
 * - Imagem posterior abaixo (escala 0.85, opacity 0.5, metade visível)
 * - Autoplay a cada 4 segundos
 * - Navegação manual com setas
 * - Smooth transitions
 */

import { useState, useEffect } from 'react';

const dashboards = [
  {
    src: '/dashboard-0.png',
    alt: 'MAXIMUS AI - Neural Architecture Dashboard',
    title: 'Neural Architecture'
  },
  {
    src: '/dashboard-1.png',
    alt: 'MAXIMUS AI - Consciousness Metrics Dashboard',
    title: 'Consciousness Metrics'
  },
  {
    src: '/dashboard-2.png',
    alt: 'MAXIMUS AI - Offensive Operations Dashboard',
    title: 'Offensive Operations'
  },
  {
    src: '/dashboard-3.png',
    alt: 'MAXIMUS AI - Defensive Operations Dashboard',
    title: 'Defensive Operations'
  }
];

export default function DashboardCarousel() {
  const [activeIndex, setActiveIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);

  // Autoplay
  useEffect(() => {
    if (isPaused) return;

    const interval = setInterval(() => {
      setActiveIndex((current) => (current + 1) % dashboards.length);
    }, 4000);

    return () => clearInterval(interval);
  }, [isPaused]);

  const goToPrevious = () => {
    setActiveIndex((current) =>
      current === 0 ? dashboards.length - 1 : current - 1
    );
  };

  const goToNext = () => {
    setActiveIndex((current) => (current + 1) % dashboards.length);
  };

  const getImageStyle = (index: number) => {
    const diff = index - activeIndex;
    const absPos = Math.abs(diff);

    // Imagem ativa (centro)
    if (diff === 0) {
      return {
        transform: 'translateY(0%) scale(1) translateZ(0px)',
        opacity: 1,
        zIndex: 30,
        pointerEvents: 'auto' as const,
        filter: 'brightness(1)'
      };
    }

    // Imagem anterior (acima)
    if (diff === -1 || (diff === dashboards.length - 1)) {
      return {
        transform: 'translateY(-55%) scale(0.85) translateZ(-100px)',
        opacity: 0.4,
        zIndex: 10,
        pointerEvents: 'none' as const,
        filter: 'brightness(0.7)'
      };
    }

    // Imagem posterior (abaixo)
    if (diff === 1 || (diff === -(dashboards.length - 1))) {
      return {
        transform: 'translateY(55%) scale(0.85) translateZ(-100px)',
        opacity: 0.4,
        zIndex: 10,
        pointerEvents: 'none' as const,
        filter: 'brightness(0.7)'
      };
    }

    // Outras imagens (ocultas)
    return {
      transform: 'translateY(0%) scale(0.7) translateZ(-200px)',
      opacity: 0,
      zIndex: 0,
      pointerEvents: 'none' as const,
      filter: 'brightness(0.5)'
    };
  };

  return (
    <div
      className="carousel-container"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      <div className="carousel-viewport">
        {dashboards.map((dashboard, index) => (
          <div
            key={dashboard.src}
            className="carousel-slide"
            style={getImageStyle(index)}
          >
            <img
              src={dashboard.src}
              alt={dashboard.alt}
              loading={index === 0 ? 'eager' : 'lazy'}
              width="1200"
              height="800"
            />
            {index === activeIndex && (
              <div className="carousel-caption">
                {dashboard.title}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Navigation Controls */}
      <button
        className="carousel-button carousel-button-prev"
        onClick={goToPrevious}
        aria-label="Previous dashboard"
      >
        <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
          <path d="m18 15-6-6-6 6"/>
        </svg>
      </button>

      <button
        className="carousel-button carousel-button-next"
        onClick={goToNext}
        aria-label="Next dashboard"
      >
        <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24">
          <path d="m6 9 6 6 6-6"/>
        </svg>
      </button>

      {/* Indicators */}
      <div className="carousel-indicators">
        {dashboards.map((_, index) => (
          <button
            key={index}
            className={`carousel-indicator ${index === activeIndex ? 'active' : ''}`}
            onClick={() => setActiveIndex(index)}
            aria-label={`Go to dashboard ${index + 1}`}
          />
        ))}
      </div>
    </div>
  );
}
