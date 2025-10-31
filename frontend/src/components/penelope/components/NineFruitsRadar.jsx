/**
 * NineFruitsRadar - Radar Chart dos 9 Frutos do Espírito
 * =======================================================
 *
 * Visualização em radar chart dos scores (0-100) de cada fruto.
 * Usa Recharts para renderização.
 *
 * Frutos (Gálatas 5:22-23):
 * - Agape (Amor), Chara (Alegria), Eirene (Paz)
 * - Enkrateia (Domínio Próprio), Pistis (Fidelidade), Praotes (Mansidão)
 * - Tapeinophrosyne (Humildade), Aletheia (Verdade), Sophia (Sabedoria)
 */

import React from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';

export const NineFruitsRadar = ({ fruits }) => {
  // Transform fruits data to Recharts format
  const data = fruits
    ? [
        { fruit: 'Amor', fullMark: 100, score: fruits.agape?.score || 0, greek: 'ἀγάπη' },
        { fruit: 'Alegria', fullMark: 100, score: fruits.chara?.score || 0, greek: 'χαρά' },
        { fruit: 'Paz', fullMark: 100, score: fruits.eirene?.score || 0, greek: 'εἰρήνη' },
        { fruit: 'D.Próprio', fullMark: 100, score: fruits.enkrateia?.score || 0, greek: 'ἐγκράτεια' },
        { fruit: 'Fidelidade', fullMark: 100, score: fruits.pistis?.score || 0, greek: 'πίστις' },
        { fruit: 'Mansidão', fullMark: 100, score: fruits.praotes?.score || 0, greek: 'πραότης' },
        { fruit: 'Humildade', fullMark: 100, score: fruits.tapeinophrosyne?.score || 0, greek: 'ταπεινοφροσύνη' },
        { fruit: 'Verdade', fullMark: 100, score: fruits.aletheia?.score || 0, greek: 'ἀλήθεια' },
        { fruit: 'Sabedoria', fullMark: 100, score: fruits.sophia?.score || 0, greek: 'σοφία' },
      ]
    : [];

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div
          style={{
            background: 'rgba(0, 0, 0, 0.9)',
            border: '1px solid #00ff88',
            borderRadius: '8px',
            padding: '12px',
            color: '#fff',
          }}
        >
          <p style={{ margin: 0, fontWeight: 'bold', color: '#00ff88' }}>{data.fruit}</p>
          <p style={{ margin: '4px 0 0', fontSize: '0.9rem', opacity: 0.7 }}>{data.greek}</p>
          <p style={{ margin: '8px 0 0', fontSize: '1.5rem', fontWeight: 'bold' }}>
            {data.score}/100
          </p>
        </div>
      );
    }
    return null;
  };

  if (!fruits) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '400px' }}>
        <p style={{ opacity: 0.6 }}>Carregando dados dos frutos...</p>
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={400}>
      <RadarChart data={data}>
        <PolarGrid stroke="rgba(0, 255, 136, 0.2)" />
        <PolarAngleAxis
          dataKey="fruit"
          tick={{ fill: '#fff', fontSize: 12 }}
          stroke="rgba(0, 255, 136, 0.3)"
        />
        <PolarRadiusAxis
          angle={90}
          domain={[0, 100]}
          tick={{ fill: '#fff', fontSize: 10 }}
          stroke="rgba(0, 255, 136, 0.3)"
        />
        <Radar
          name="Frutos"
          dataKey="score"
          stroke="#00ff88"
          fill="#00ff88"
          fillOpacity={0.6}
          strokeWidth={2}
        />
        <Tooltip content={<CustomTooltip />} />
      </RadarChart>
    </ResponsiveContainer>
  );
};

export default NineFruitsRadar;
