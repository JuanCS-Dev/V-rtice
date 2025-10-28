/**
 * ═══════════════════════════════════════════════════════════════════════════
 * useGSAPTimeline Hook - Immune Cascade Animation
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * GSAP timeline orchestrating the biological immune response cascade.
 * Animates from milliseconds (reflex) to hours (memory formation).
 */

import { useRef, useEffect } from 'react';
import { gsap } from 'gsap';
import { useGSAP } from '@gsap/react';
import type { AnimationPhase } from './types';

interface UseGSAPTimelineProps {
  phases: AnimationPhase[];
  containerRef: React.RefObject<SVGSVGElement | null>;
  isLayoutStable: boolean;
  speed?: number;
}

interface UseGSAPTimelineReturn {
  timeline: gsap.core.Timeline | null;
  play: () => void;
  pause: () => void;
  restart: () => void;
  setSpeed: (speed: number) => void;
  currentPhase: number;
}

export function useGSAPTimeline({
  phases,
  containerRef,
  isLayoutStable,
  speed = 1
}: UseGSAPTimelineProps): UseGSAPTimelineReturn {
  const timelineRef = useRef<gsap.core.Timeline | null>(null);
  const currentPhaseRef = useRef(0);

  useGSAP(() => {
    if (!containerRef.current || !isLayoutStable) return;

    // Create master timeline
    const tl = gsap.timeline({
      paused: true,
      defaults: { ease: 'power2.inOut' },
      onUpdate: () => {
        // Track current phase based on timeline progress
        const progress = tl.progress();
        const totalDuration = tl.duration();
        const currentTime = progress * totalDuration;

        for (let i = 0; i < phases.length; i++) {
          const phase = phases[i];
          if (currentTime >= phase.startTime && currentTime < phase.startTime + phase.duration) {
            currentPhaseRef.current = i;
            break;
          }
        }
      }
    });

    // ═══════════════════════════════════════════════════════════════════════
    // PHASE 1: FIREWALL DETECTION (0-300ms)
    // ═══════════════════════════════════════════════════════════════════════

    // Atacantes aparecem no topo
    tl.fromTo('.attacker-group',
      {
        opacity: 0,
        scale: 0.5,
        y: -50
      },
      {
        opacity: 1,
        scale: 1,
        y: 0,
        duration: 0.3,
        ease: 'back.out(1.7)'
      }, 0)
    // Atacantes se movem em direção ao firewall
    .to('.attacker-group', {
      y: 100,
      duration: 0.5,
      ease: 'power2.in'
    }, 0.2)
    // Firewall detecta
    .to('.node[data-system="firewall"]', {
      scale: 1.3,
      fill: '#f97316',
      opacity: 1,
      duration: 0.2,
      stagger: 0.05,
      ease: 'back.out(1.7)'
    }, 0.3)
    .to('.node[data-system="firewall"]', {
      boxShadow: '0 0 30px rgba(249, 115, 22, 0.8)',
      duration: 0.1,
      yoyo: true,
      repeat: 1
    }, 0.4);

    // ═══════════════════════════════════════════════════════════════════════
    // PHASE 2: AUTONOMIC REFLEX (300-500ms)
    // ═══════════════════════════════════════════════════════════════════════
    tl.to('.node[data-system="autonomic"]', {
      scale: 1.4,
      fill: '#ef4444',
      opacity: 1,
      duration: 0.1,
      stagger: 0.02,
      ease: 'power4.out'
    }, 0.3)
    .to('.link[data-target*="reflex"]', {
      strokeWidth: 4,
      stroke: '#ef4444',
      opacity: 1,
      duration: 0.1
    }, 0.3);

    // Particle flow along link (Kafka event)
    tl.to('.particle-reflex', {
      motionPath: {
        path: '.link[data-target*="reflex"]',
        align: '.link[data-target*="reflex"]',
        autoRotate: true,
        alignOrigin: [0.5, 0.5]
      },
      duration: 0.2,
      ease: 'none'
    }, 0.3);

    // ═══════════════════════════════════════════════════════════════════════
    // PHASE 3: NEUTROPHIL RESPONSE (500ms-2.5s)
    // ═══════════════════════════════════════════════════════════════════════

    // Atacantes penetram mais fundo
    tl.to('.attacker-group', {
      y: 250,
      duration: 0.5,
      ease: 'power1.in'
    }, 0.5)
    // Neutrófilos respondem
    .to('.node[data-id="neutrophil"]', {
      scale: 1.5,
      fill: '#10b981',
      opacity: 1,
      x: '+=50',
      y: '-=30',
      duration: 1,
      ease: 'power2.out'
    }, 0.5)
    .to('.node[data-id="nk_cell"]', {
      scale: 1.3,
      fill: '#10b981',
      opacity: 0.9,
      x: '+=30',
      y: '+=20',
      duration: 1,
      ease: 'power2.out'
    }, 0.7)
    // Escudo aparece
    .to('.shield-effect', {
      opacity: 1,
      scale: 1.2,
      duration: 0.2,
      ease: 'back.out(2)'
    }, 1.3)
    // Primeiro ataque: alguns atacantes são destruídos
    .to('.attacker-virus-1', {
      scale: 0,
      rotation: 360,
      opacity: 0,
      duration: 0.3,
      ease: 'back.in(2)'
    }, 1.5)
    // Explosão 1
    .to('.explosion-1', {
      opacity: 1,
      scale: 1.5,
      duration: 0.2,
      ease: 'power2.out'
    }, 1.5)
    .to('.explosion-1', {
      opacity: 0,
      scale: 2,
      duration: 0.3
    }, 1.7)
    // Malware destruído
    .to('.attacker-malware-1', {
      scale: 0,
      rotation: -360,
      opacity: 0,
      duration: 0.3,
      ease: 'back.in(2)'
    }, 1.7)
    // Explosão 2
    .to('.explosion-2', {
      opacity: 1,
      scale: 1.5,
      duration: 0.2,
      ease: 'power2.out'
    }, 1.7)
    .to('.explosion-2', {
      opacity: 0,
      scale: 2,
      duration: 0.3
    }, 1.9)
    // Escudo desaparece
    .to('.shield-effect', {
      opacity: 0,
      duration: 0.3
    }, 2);

    // ═══════════════════════════════════════════════════════════════════════
    // PHASE 4: MACROPHAGE PHAGOCYTOSIS (2.5s-4.5s)
    // ═══════════════════════════════════════════════════════════════════════

    // Atacantes restantes avançam mais
    tl.to('.attacker-ransomware', {
      y: 300,
      rotation: 360,
      duration: 0.5,
      ease: 'power1.in'
    }, 2.5)
    .to('.attacker-trojan', {
      y: 300,
      rotation: -360,
      duration: 0.5,
      ease: 'power1.in'
    }, 2.5)
    // Macrófago ativa
    .to('.node[data-id="macrophage"]', {
      scale: 1.8,
      rotation: 360,
      fill: '#14b8a6',
      opacity: 1,
      duration: 1.5,
      ease: 'back.inOut(1.2)'
    }, 2.5)
    // "Engulfing" animation (pulsing) - fagocitose
    .to('.node[data-id="macrophage"]', {
      scale: 2,
      opacity: 0.7,
      duration: 0.3,
      yoyo: true,
      repeat: 3,
      ease: 'power1.inOut'
    }, 3)
    // Ransomware é engolido
    .to('.attacker-ransomware', {
      scale: 0,
      opacity: 0,
      duration: 0.5,
      ease: 'power3.in'
    }, 3.5)
    // Explosão 3
    .to('.explosion-3', {
      opacity: 1,
      scale: 1.5,
      duration: 0.2
    }, 3.5)
    .to('.explosion-3', {
      opacity: 0,
      scale: 2,
      duration: 0.3
    }, 3.7)
    // Trojan é engolido
    .to('.attacker-trojan', {
      scale: 0,
      opacity: 0,
      duration: 0.5,
      ease: 'power3.in'
    }, 3.9)
    // Explosão 4
    .to('.explosion-4', {
      opacity: 1,
      scale: 1.5,
      duration: 0.2
    }, 3.9)
    .to('.explosion-4', {
      opacity: 0,
      scale: 2,
      duration: 0.3
    }, 4.1);

    // Particle flow to macrophage
    tl.to('.particle-macrophage', {
      motionPath: {
        path: '.link[data-target="macrophage"]',
        align: '.link[data-target="macrophage"]',
        autoRotate: true
      },
      duration: 1,
      stagger: 0.1,
      ease: 'none'
    }, 2.5);

    // ═══════════════════════════════════════════════════════════════════════
    // PHASE 5: DENDRITIC CELL CORRELATION (4.5s-5.5s)
    // ═══════════════════════════════════════════════════════════════════════
    tl.to('.node[data-id="dendritic"]', {
      scale: 1.6,
      fill: '#8b5cf6',
      opacity: 1,
      duration: 0.5,
      ease: 'elastic.out(1, 0.5)'
    }, 4.5)
    // Qdrant vector search visualization (radiating lines)
    .to('.dendritic-rays', {
      scale: 2,
      opacity: [0, 0.6, 0],
      duration: 0.5,
      stagger: 0.05
    }, 4.7);

    // ═══════════════════════════════════════════════════════════════════════
    // PHASE 6: HELPER T-CELL ORCHESTRATION (5.5s-6.5s)
    // ═══════════════════════════════════════════════════════════════════════
    tl.to('.node[data-id="helper_t"]', {
      scale: 1.7,
      fill: '#a855f7',
      opacity: 1,
      duration: 0.5,
      ease: 'back.out(2)'
    }, 5.5)
    // Th1/Th2 decision (branching paths)
    .to('.link[data-source="helper_t"]', {
      strokeWidth: 3,
      stroke: '#a855f7',
      opacity: 1,
      duration: 0.3,
      stagger: 0.1
    }, 5.7);

    // ═══════════════════════════════════════════════════════════════════════
    // PHASE 7: ADAPTIVE RESPONSE (6.5s-9.5s)
    // ═══════════════════════════════════════════════════════════════════════
    // B-Cells generate antibodies
    tl.to('.node[data-id="bcell"]', {
      scale: 1.5,
      fill: '#c084fc',
      opacity: 1,
      duration: 1,
      ease: 'power2.out'
    }, 6.5)
    // "Antibody" particles emanating
    .to('.antibody-particle', {
      scale: [0, 1.2, 0],
      opacity: [0, 1, 0],
      x: '+=random(-50, 50)',
      y: '+=random(-50, 50)',
      duration: 1.5,
      stagger: 0.1,
      ease: 'none'
    }, 6.8);

    // Último atacante (worm) tenta penetrar mais fundo
    tl.to('.attacker-worm', {
      y: 450,
      rotation: 720,
      duration: 1,
      ease: 'power2.in'
    }, 7)
    // Cytotoxic T-Cells attack - ataque direto
    .to('.node[data-id="cytotoxic_t"]', {
      scale: 1.6,
      fill: '#dc2626',
      opacity: 1,
      x: '+=80',
      duration: 1.5,
      ease: 'power3.out'
    }, 7.5)
    // Attack animation (rapid strikes) - ataques rápidos
    .to('.node[data-id="cytotoxic_t"]', {
      x: '+=10',
      duration: 0.1,
      yoyo: true,
      repeat: 5,
      ease: 'none'
    }, 8)
    // Worm é destruído pelo ataque
    .to('.attacker-worm', {
      scale: 0,
      rotation: 1080,
      opacity: 0,
      duration: 0.4,
      ease: 'back.in(3)'
    }, 8.5)
    // Explosão final - múltiplas explosões
    .to(['.explosion-1', '.explosion-2', '.explosion-3', '.explosion-4'], {
      opacity: 1,
      scale: 2,
      duration: 0.3,
      stagger: 0.1,
      ease: 'power2.out'
    }, 8.5)
    .to(['.explosion-1', '.explosion-2', '.explosion-3', '.explosion-4'], {
      opacity: 0,
      scale: 3,
      duration: 0.5,
      stagger: 0.1
    }, 8.8)
    // Mensagem de vitória
    .to('.shield-effect', {
      opacity: 1,
      scale: 1.5,
      rotation: 360,
      duration: 0.5,
      ease: 'back.out(2)'
    }, 9.3);

    // Regulatory T-Cells suppress
    tl.to('.node[data-id="treg"]', {
      scale: 1.3,
      fill: '#6366f1',
      opacity: 0.8,
      duration: 1,
      ease: 'sine.inOut'
    }, 8.5);

    // ═══════════════════════════════════════════════════════════════════════
    // PHASE 8: MEMORY FORMATION (9.5s-11.5s)
    // ═══════════════════════════════════════════════════════════════════════
    tl.to('.node[data-id="oraculo"]', {
      scale: 1.4,
      fill: '#7c3aed',
      opacity: 1,
      duration: 1,
      ease: 'power2.out'
    }, 9.5)
    .to('.node[data-id="eureka"]', {
      scale: 1.4,
      fill: '#6d28d9',
      opacity: 1,
      duration: 1,
      ease: 'power2.out'
    }, 10);

    // Memory "writing" effect (glowing)
    tl.to(['.node[data-id="oraculo"]', '.node[data-id="eureka"]'], {
      filter: 'brightness(1.5) drop-shadow(0 0 20px rgba(124, 58, 237, 0.8))',
      duration: 0.5,
      yoyo: true,
      repeat: 1
    }, 10.5);

    // ═══════════════════════════════════════════════════════════════════════
    // PHASE 9: CONSCIOUSNESS UPDATE (11.5s-13s)
    // ═══════════════════════════════════════════════════════════════════════
    tl.to('.node[data-id="maximus_core"]', {
      scale: 2,
      fill: '#fbbf24',
      opacity: 1,
      filter: 'brightness(1.3) drop-shadow(0 0 40px rgba(251, 191, 36, 0.9))',
      duration: 1,
      ease: 'power3.out'
    }, 11.5)
    // Consciousness "pulse" (all systems update)
    .to('.node', {
      opacity: 0.5,
      scale: 0.9,
      duration: 0.3,
      stagger: { amount: 0.5, from: 'center', grid: 'auto' }
    }, 12)
    .to('.node', {
      opacity: 1,
      scale: 1,
      duration: 0.5,
      stagger: { amount: 0.5, from: 'center', grid: 'auto' }
    }, 12.3);

    // Final fade out
    tl.to('.node, .link', {
      opacity: 0.6,
      duration: 0.5
    }, 12.8);

    timelineRef.current = tl;
    tl.timeScale(speed);

  }, { scope: containerRef, dependencies: [isLayoutStable, phases, speed] });

  const play = () => {
    timelineRef.current?.play();
  };

  const pause = () => {
    timelineRef.current?.pause();
  };

  const restart = () => {
    timelineRef.current?.restart();
  };

  const setSpeed = (newSpeed: number) => {
    timelineRef.current?.timeScale(newSpeed);
  };

  return {
    timeline: timelineRef.current,
    play,
    pause,
    restart,
    setSpeed,
    currentPhase: currentPhaseRef.current
  };
}
