/**
import logger from '@/utils/logger';
 * ═══════════════════════════════════════════════════════════════════════════
 * BACKGROUND EFFECTS - Sistema Escalável de Efeitos Visuais
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Sistema modular para adicionar/trocar efeitos de background do dashboard.
 * Ideal para ensinar AI a criar novos efeitos visuais!
 *
 * Como adicionar novo efeito:
 * 1. Criar função como export const NomeEffect = () => { ... }
 * 2. Adicionar ao array AVAILABLE_EFFECTS
 * 3. Pronto! Aparece no seletor automaticamente
 */

import React, { useEffect, useRef } from 'react';

// ═══════════════════════════════════════════════════════════════════════════
// EFEITO 1: SCANLINE (Original - linha que desce)
// ═══════════════════════════════════════════════════════════════════════════
export const ScanlineEffect = () => {
  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100%',
      height: '2px',
      background: 'linear-gradient(90deg, transparent, #8B5CF6, transparent)',
      zIndex: 1,
      animation: 'scanlineMove 3s linear infinite',
      pointerEvents: 'none'
    }} />
  );
};

// ═══════════════════════════════════════════════════════════════════════════
// EFEITO 2: MATRIX RAIN (Códigos caindo tipo Matrix)
// ═══════════════════════════════════════════════════════════════════════════
export const MatrixRainEffect = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) {
      logger.debug('⚠️ MatrixRain: Canvas ref não disponível');
      return;
    }

    logger.debug('✅ MatrixRain: Iniciando efeito...', canvas.width, canvas.height);

    const ctx = canvas.getContext('2d');
    if (!ctx) {
      logger.debug('⚠️ MatrixRain: Context 2D não disponível');
      return;
    }

    // Configuração do canvas
    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      logger.debug('📐 MatrixRain: Canvas redimensionado:', canvas.width, 'x', canvas.height);
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Configuração do Matrix
    const chars = '01MAXIMUS'; // Binary + MAXIMUS
    const fontSize = 14;
    const columns = Math.floor(canvas.width / fontSize);
    const drops = [];

    // Randomize início das colunas
    for (let i = 0; i < columns; i++) {
      drops[i] = Math.floor(Math.random() * -100);
    }

    logger.debug('🔢 MatrixRain: Configurado com', columns, 'colunas');

    // Função de desenho
    const draw = () => {
      // Fade effect - deixa rastro visível mas sutil
      ctx.fillStyle = 'rgba(15, 23, 42, 0.08)'; // Fade leve = efeito mais persistente
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Desenhar caracteres
      for (let i = 0; i < drops.length; i++) {
        // Caracter aleatório
        const char = chars[Math.floor(Math.random() * chars.length)];

        // Calcular posição Y
        const y = drops[i] * fontSize;

        // Gradiente azul → roxo VISÍVEL (cyberpunk aesthetic)
        const gradient = ctx.createLinearGradient(0, y - 150, 0, y);
        gradient.addColorStop(0, 'rgba(139, 92, 246, 0.5)'); // Roxo no topo (visível)
        gradient.addColorStop(0.3, 'rgba(6, 182, 212, 0.3)'); // Cyan (visível)
        gradient.addColorStop(0.7, 'rgba(139, 92, 246, 0.15)'); // Roxo esmaecendo
        gradient.addColorStop(1, 'rgba(139, 92, 246, 0)'); // Invisível no final

        ctx.fillStyle = gradient;
        ctx.font = `${fontSize}px monospace`;
        ctx.fillText(char, i * fontSize, y);

        // Reset aleatório (cria efeito de chuva espaçada)
        if (y > canvas.height && Math.random() > 0.975) {
          drops[i] = 0;
        }

        drops[i]++;
      }
    };

    // Animation loop (60 FPS)
    let frameCount = 0;
    const interval = setInterval(() => {
      draw();
      frameCount++;
      if (frameCount === 1) {
        logger.debug('🎬 MatrixRain: Primeira animação renderizada');
      }
    }, 50);

    logger.debug('🔄 MatrixRain: Loop de animação iniciado');

    return () => {
      logger.debug('🛑 MatrixRain: Cleanup - parando animação');
      clearInterval(interval);
      window.removeEventListener('resize', resizeCanvas);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: 1,
        pointerEvents: 'none',
        opacity: 0.6 // Visível - estética cyberpunk com efeito Matrix perceptível
      }}
    />
  );
};

// ═══════════════════════════════════════════════════════════════════════════
// EFEITO 3: PARTICLES (Partículas flutuantes - exemplo para expandir)
// ═══════════════════════════════════════════════════════════════════════════
export const ParticlesEffect = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Criar partículas
    const particles = [];
    const particleCount = 50;

    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        radius: Math.random() * 2 + 1
      });
    }

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particles.forEach((p, i) => {
        // Atualizar posição
        p.x += p.vx;
        p.y += p.vy;

        // Bounce nas bordas
        if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1;

        // Desenhar partícula
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(139, 92, 246, 0.3)`;
        ctx.fill();

        // Conectar partículas próximas
        particles.slice(i + 1).forEach(p2 => {
          const dx = p.x - p2.x;
          const dy = p.y - p2.y;
          const distance = Math.sqrt(dx * dx + dy * dy);

          if (distance < 100) {
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle = `rgba(6, 182, 212, ${0.2 * (1 - distance / 100)})`;
            ctx.lineWidth = 1;
            ctx.stroke();
          }
        });
      });
    };

    const interval = setInterval(draw, 1000 / 60);

    return () => {
      clearInterval(interval);
      window.removeEventListener('resize', resizeCanvas);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: 1,
        pointerEvents: 'none'
      }}
    />
  );
};

// ═══════════════════════════════════════════════════════════════════════════
// EFEITO 4: NONE (Sem efeito)
// ═══════════════════════════════════════════════════════════════════════════
export const NoneEffect = () => null;

// ═══════════════════════════════════════════════════════════════════════════
// REGISTRO DE EFEITOS DISPONÍVEIS
// ═══════════════════════════════════════════════════════════════════════════
export const AVAILABLE_EFFECTS = [
  {
    id: 'scanline',
    name: 'Scanline',
    description: 'Linha horizontal descendo (clássico)',
    icon: '━',
    component: ScanlineEffect
  },
  {
    id: 'matrix',
    name: 'Matrix Rain',
    description: 'Códigos binários caindo (azul→roxo sutil)',
    icon: '⋮',
    component: MatrixRainEffect
  },
  {
    id: 'particles',
    name: 'Particles',
    description: 'Partículas conectadas flutuantes',
    icon: '∴',
    component: ParticlesEffect
  },
  {
    id: 'none',
    name: 'Nenhum',
    description: 'Desabilitar efeitos de background',
    icon: '○',
    component: NoneEffect
  }
];

// ═══════════════════════════════════════════════════════════════════════════
// COMPONENTE SELETOR DE EFEITOS
// ═══════════════════════════════════════════════════════════════════════════
export const EffectSelector = ({ currentEffect, onEffectChange }) => {
  logger.debug('🎨 EffectSelector renderizando:', currentEffect);

  return (
    <div style={{
      position: 'fixed',
      bottom: '7rem',
      right: '2rem',
      zIndex: 9999,
      background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(30, 27, 75, 0.98))',
      border: '1px solid rgba(139, 92, 246, 0.4)',
      borderRadius: '12px',
      padding: '0.75rem',
      backdropFilter: 'blur(15px)',
      boxShadow: '0 8px 32px rgba(139, 92, 246, 0.2), 0 0 0 1px rgba(139, 92, 246, 0.1)',
      transition: 'all 0.3s ease'
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.6rem',
        marginBottom: '0.6rem'
      }}>
        <div style={{
          width: '3px',
          height: '16px',
          background: 'linear-gradient(180deg, #8B5CF6, #06B6D4)',
          borderRadius: '2px'
        }}></div>
        <div style={{
          color: '#E2E8F0',
          fontSize: '0.65rem',
          fontWeight: '600',
          textTransform: 'uppercase',
          letterSpacing: '1.2px',
          fontFamily: 'monospace'
        }}>
          🎨 Visual Effect
        </div>
      </div>

      <div style={{
        display: 'flex',
        gap: '0.4rem',
        flexWrap: 'wrap'
      }}>
        {AVAILABLE_EFFECTS.map(effect => (
          <button
            key={effect.id}
            onClick={() => onEffectChange(effect.id)}
            title={effect.description}
            style={{
              width: '34px',
              height: '34px',
              background: currentEffect === effect.id
                ? 'linear-gradient(135deg, #8B5CF6, #06B6D4)'
                : 'rgba(15, 23, 42, 0.6)',
              border: currentEffect === effect.id
                ? '2px solid #8B5CF6'
                : '1px solid rgba(139, 92, 246, 0.2)',
              borderRadius: '8px',
              color: currentEffect === effect.id ? '#FFFFFF' : '#94A3B8',
              fontSize: '1rem',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontFamily: 'monospace',
              position: 'relative',
              overflow: 'hidden',
              boxShadow: currentEffect === effect.id
                ? '0 4px 12px rgba(139, 92, 246, 0.4)'
                : 'none'
            }}
            onMouseEnter={(e) => {
              if (currentEffect !== effect.id) {
                e.target.style.background = 'rgba(139, 92, 246, 0.15)';
                e.target.style.borderColor = '#8B5CF6';
                e.target.style.color = '#E2E8F0';
                e.target.style.transform = 'translateY(-2px)';
              }
            }}
            onMouseLeave={(e) => {
              if (currentEffect !== effect.id) {
                e.target.style.background = 'rgba(15, 23, 42, 0.6)';
                e.target.style.borderColor = 'rgba(139, 92, 246, 0.2)';
                e.target.style.color = '#94A3B8';
                e.target.style.transform = 'translateY(0)';
              }
            }}
          >
            {effect.icon}
          </button>
        ))}
      </div>

      {/* Tooltip com nome do efeito atual */}
      <div style={{
        marginTop: '0.75rem',
        paddingTop: '0.75rem',
        borderTop: '1px solid rgba(139, 92, 246, 0.2)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '0.5rem'
      }}>
        <div style={{
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          background: 'linear-gradient(135deg, #8B5CF6, #06B6D4)',
          boxShadow: '0 0 8px rgba(139, 92, 246, 0.6)',
          animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite'
        }}></div>
        <div style={{
          fontSize: '0.65rem',
          color: '#8B5CF6',
          fontWeight: '600',
          fontFamily: 'monospace',
          letterSpacing: '0.5px'
        }}>
          {AVAILABLE_EFFECTS.find(e => e.id === currentEffect)?.name || 'None'}
        </div>
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL - Renderiza o efeito selecionado
// ═══════════════════════════════════════════════════════════════════════════
export const BackgroundEffect = ({ effectId }) => {
  const effect = AVAILABLE_EFFECTS.find(e => e.id === effectId);
  if (!effect) return null;

  const EffectComponent = effect.component;
  return <EffectComponent />;
};

// ═══════════════════════════════════════════════════════════════════════════
// EXPORT DEFAULT
// ═══════════════════════════════════════════════════════════════════════════
export default {
  BackgroundEffect,
  AVAILABLE_EFFECTS,
  // Individual effects
  ScanlineEffect,
  MatrixRainEffect,
  ParticlesEffect,
  NoneEffect
};
