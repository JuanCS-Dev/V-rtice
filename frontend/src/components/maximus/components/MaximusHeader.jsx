/**
 * MaximusHeader - Redesigned Command Center Header
 *
 * Two-tier design:
 * - Top Bar: Logo, Status, Clock, Actions
 * - Nav Bar: Panel Navigation
 *
 * Cyberpunk aesthetic with military precision
 */

import React from 'react';
import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';
import { CompactEffectSelector } from './CompactEffectSelector';
import { CompactLanguageSelector } from './CompactLanguageSelector';

export const MaximusHeader = ({
  aiStatus,
  currentTime,
  activePanel,
  panels,
  setActivePanel,
  setCurrentView,
  getItemProps,
  backgroundEffect,
  onEffectChange
}) => {
  const { t } = useTranslation();

  // Format time
  const timeString = currentTime.toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
  const dateString = currentTime.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });

  return (
    <header style={{
      position: 'relative',
      zIndex: 10,
      background: 'linear-gradient(180deg, rgba(15, 23, 42, 0.98) 0%, rgba(15, 23, 42, 0.95) 100%)',
      borderBottom: '2px solid rgba(139, 92, 246, 0.4)',
      backdropFilter: 'blur(10px)',
      boxShadow: '0 4px 24px rgba(0, 0, 0, 0.5)'
    }}>
      {/* TOP BAR - Command Center */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'auto 1fr auto',
        alignItems: 'center',
        padding: '1rem 2rem',
        gap: '2rem',
        borderBottom: '1px solid rgba(139, 92, 246, 0.2)'
      }}>
        {/* LEFT - Logo & Branding */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            width: '50px',
            height: '50px',
            background: 'linear-gradient(135deg, #8B5CF6 0%, #06B6D4 100%)',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.75rem',
            position: 'relative',
            boxShadow: '0 4px 16px rgba(139, 92, 246, 0.4)'
          }}>
            🧠
            <div style={{
              position: 'absolute',
              width: '100%',
              height: '100%',
              borderRadius: '10px',
              border: '2px solid #8B5CF6',
              animation: 'pulse 2s ease-out infinite'
            }}></div>
          </div>
          <div>
            <h1 style={{
              margin: 0,
              fontSize: '1.5rem',
              fontWeight: 'bold',
              background: 'linear-gradient(135deg, #8B5CF6, #06B6D4, #10B981)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              letterSpacing: '2px',
              fontFamily: 'monospace'
            }}>
              MAXIMUS AI
            </h1>
            <p style={{
              margin: '0.25rem 0 0',
              fontSize: '0.7rem',
              color: '#94A3B8',
              letterSpacing: '1px',
              fontFamily: 'monospace'
            }}>
              Autonomous Intelligence Platform
            </p>
          </div>
        </div>

        {/* CENTER - Status Indicators */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          gap: '1rem'
        }}>
          {/* CORE */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.75rem 1rem',
            background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(6, 182, 212, 0.15))',
            border: '1px solid rgba(139, 92, 246, 0.3)',
            borderRadius: '8px',
            minWidth: '80px',
            position: 'relative',
            overflow: 'hidden'
          }}>
            <div style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '2px',
              background: aiStatus.core.status === 'online' ? '#10B981' :
                         aiStatus.core.status === 'offline' ? '#EF4444' : '#F59E0B',
              boxShadow: `0 0 10px ${aiStatus.core.status === 'online' ? '#10B981' : '#EF4444'}`
            }}></div>
            <span style={{
              fontSize: '0.55rem',
              color: '#94A3B8',
              fontWeight: '600',
              textTransform: 'uppercase',
              letterSpacing: '1px',
              fontFamily: 'monospace'
            }}>CORE</span>
            <span style={{
              fontSize: '0.8rem',
              fontWeight: 'bold',
              color: aiStatus.core.status === 'online' ? '#10B981' :
                     aiStatus.core.status === 'offline' ? '#EF4444' : '#F59E0B',
              textTransform: 'uppercase',
              fontFamily: 'monospace'
            }}>
              {aiStatus.core.status === 'online' ? 'ONLINE' :
               aiStatus.core.status === 'offline' ? 'OFFLINE' : 'IDLE'}
            </span>
          </div>

          {/* ORACLE */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.75rem 1rem',
            background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(6, 182, 212, 0.15))',
            border: '1px solid rgba(139, 92, 246, 0.3)',
            borderRadius: '8px',
            minWidth: '80px',
            position: 'relative',
            overflow: 'hidden'
          }}>
            <div style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '2px',
              background: aiStatus.oraculo.status === 'online' ? '#10B981' :
                         aiStatus.oraculo.status === 'offline' ? '#EF4444' : '#F59E0B',
              boxShadow: `0 0 10px ${aiStatus.oraculo.status === 'online' ? '#10B981' : '#EF4444'}`
            }}></div>
            <span style={{
              fontSize: '0.55rem',
              color: '#94A3B8',
              fontWeight: '600',
              textTransform: 'uppercase',
              letterSpacing: '1px',
              fontFamily: 'monospace'
            }}>ORACLE</span>
            <span style={{
              fontSize: '0.8rem',
              fontWeight: 'bold',
              color: aiStatus.oraculo.status === 'online' ? '#10B981' :
                     aiStatus.oraculo.status === 'offline' ? '#EF4444' : '#F59E0B',
              textTransform: 'uppercase',
              fontFamily: 'monospace'
            }}>
              {aiStatus.oraculo.status === 'online' ? 'IDLE' :
               aiStatus.oraculo.status === 'offline' ? 'OFFLINE' : 'IDLE'}
            </span>
          </div>

          {/* EUREKA */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.75rem 1rem',
            background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(6, 182, 212, 0.15))',
            border: '1px solid rgba(139, 92, 246, 0.3)',
            borderRadius: '8px',
            minWidth: '80px',
            position: 'relative',
            overflow: 'hidden'
          }}>
            <div style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '2px',
              background: aiStatus.eureka.status === 'online' ? '#10B981' :
                         aiStatus.eureka.status === 'offline' ? '#EF4444' : '#F59E0B',
              boxShadow: `0 0 10px ${aiStatus.eureka.status === 'online' ? '#10B981' : '#EF4444'}`
            }}></div>
            <span style={{
              fontSize: '0.55rem',
              color: '#94A3B8',
              fontWeight: '600',
              textTransform: 'uppercase',
              letterSpacing: '1px',
              fontFamily: 'monospace'
            }}>EUREKA</span>
            <span style={{
              fontSize: '0.8rem',
              fontWeight: 'bold',
              color: aiStatus.eureka.status === 'online' ? '#10B981' :
                     aiStatus.eureka.status === 'offline' ? '#EF4444' : '#F59E0B',
              textTransform: 'uppercase',
              fontFamily: 'monospace'
            }}>
              {aiStatus.eureka.status === 'online' ? 'IDLE' :
               aiStatus.eureka.status === 'offline' ? 'OFFLINE' : 'IDLE'}
            </span>
          </div>
        </div>

        {/* RIGHT - Time, Effects, Back */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '1rem'
        }}>
          {/* Clock */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'flex-end',
            padding: '0.5rem 1rem',
            background: 'rgba(6, 182, 212, 0.1)',
            border: '1px solid rgba(6, 182, 212, 0.3)',
            borderRadius: '8px'
          }}>
            <span style={{
              fontSize: '1.1rem',
              fontWeight: 'bold',
              color: '#06B6D4',
              fontFamily: 'monospace',
              letterSpacing: '1px'
            }}>
              {timeString}
            </span>
            <span style={{
              fontSize: '0.65rem',
              color: '#94A3B8',
              fontFamily: 'monospace'
            }}>
              {dateString}
            </span>
          </div>

          {/* Language Selector */}
          <CompactLanguageSelector />

          {/* Effect Selector */}
          <CompactEffectSelector
            currentEffect={backgroundEffect}
            onEffectChange={onEffectChange}
          />

          {/* Back Button */}
          <button
            onClick={() => setCurrentView('main')}
            style={{
              padding: '0.75rem 1.5rem',
              background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
              border: 'none',
              borderRadius: '8px',
              color: '#000',
              fontWeight: 'bold',
              fontSize: '0.8rem',
              cursor: 'pointer',
              letterSpacing: '1px',
              fontFamily: 'monospace',
              boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)',
              transition: 'all 0.3s ease'
            }}
            onMouseEnter={(e) => {
              e.target.style.transform = 'translateY(-2px)';
              e.target.style.boxShadow = '0 6px 20px rgba(16, 185, 129, 0.5)';
            }}
            onMouseLeave={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = '0 4px 12px rgba(16, 185, 129, 0.3)';
            }}
          >
            ← BACK
          </button>
        </div>
      </div>

      {/* NAVIGATION BAR - Panel Selection */}
      <div style={{
        display: 'flex',
        padding: '0.75rem 2rem',
        gap: '0.75rem',
        overflowX: 'auto',
        background: 'rgba(30, 27, 75, 0.3)'
      }}>
        {panels.map((panel, index) => {
          const isActive = activePanel === panel.id;
          const itemProps = getItemProps ? getItemProps(index) : {};

          return (
            <button
              key={panel.id}
              onClick={() => setActivePanel(panel.id)}
              {...itemProps}
              style={{
                flex: '1 1 auto',
                minWidth: '120px',
                padding: '0.75rem 1rem',
                background: isActive
                  ? 'linear-gradient(135deg, rgba(139, 92, 246, 0.3) 0%, rgba(6, 182, 212, 0.3) 100%)'
                  : 'rgba(15, 23, 42, 0.6)',
                border: isActive
                  ? '1px solid #8B5CF6'
                  : '1px solid rgba(139, 92, 246, 0.2)',
                borderRadius: '6px',
                color: isActive ? '#E2E8F0' : '#94A3B8',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem',
                fontSize: '0.85rem',
                fontWeight: isActive ? 'bold' : 'normal',
                fontFamily: 'monospace',
                letterSpacing: '0.5px',
                boxShadow: isActive ? '0 4px 12px rgba(139, 92, 246, 0.3)' : 'none',
                position: 'relative',
                overflow: 'hidden'
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.target.style.background = 'rgba(139, 92, 246, 0.15)';
                  e.target.style.borderColor = '#8B5CF6';
                  e.target.style.color = '#E2E8F0';
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.target.style.background = 'rgba(15, 23, 42, 0.6)';
                  e.target.style.borderColor = 'rgba(139, 92, 246, 0.2)';
                  e.target.style.color = '#94A3B8';
                }
              }}
            >
              {isActive && (
                <div style={{
                  position: 'absolute',
                  bottom: 0,
                  left: 0,
                  width: '100%',
                  height: '2px',
                  background: 'linear-gradient(90deg, #8B5CF6, #06B6D4)',
                  boxShadow: '0 0 8px rgba(139, 92, 246, 0.6)'
                }}></div>
              )}
              <span style={{ fontSize: '1.25rem' }}>{panel.icon}</span>
              <span>{panel.name}</span>
            </button>
          );
        })}
      </div>
    </header>
  );
};

MaximusHeader.propTypes = {
  aiStatus: PropTypes.object.isRequired,
  currentTime: PropTypes.instanceOf(Date).isRequired,
  activePanel: PropTypes.string.isRequired,
  panels: PropTypes.array.isRequired,
  setActivePanel: PropTypes.func.isRequired,
  setCurrentView: PropTypes.func.isRequired,
  getItemProps: PropTypes.func.isRequired,
  getStatusColor: PropTypes.func.isRequired,
  backgroundEffect: PropTypes.string,
  onEffectChange: PropTypes.func
};

export default MaximusHeader;
