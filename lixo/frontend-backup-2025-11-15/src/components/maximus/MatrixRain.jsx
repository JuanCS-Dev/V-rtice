/**
 * Matrix Rain Effect - Bem sutil (azul → roxo)
 * Códigos binários caindo suavemente no background
 */

import React, { useEffect, useRef } from "react";

export const MatrixRain = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    // Set canvas size
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    // Characters for matrix effect (binary + hex)
    const chars = "01";
    const fontSize = 14;
    const _columns = canvas.width / fontSize;

    // Cores do gradiente: azul → roxo (BEM sutis)
    const colors = [
      "rgba(6, 182, 212, 0.15)", // Cyan bem leve
      "rgba(59, 130, 246, 0.12)", // Blue suave
      "rgba(99, 102, 241, 0.10)", // Indigo discreto
      "rgba(139, 92, 246, 0.08)", // Violet bem sutil
      "rgba(168, 85, 247, 0.06)", // Purple quase invisível
    ];

    let drops = [];
    for (let i = 0; i < canvas.width / fontSize; i++) {
      drops[i] = Math.random() * -100;
    }

    const render = () => {
      ctx.fillStyle = "rgba(10, 14, 39, 0.05)";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      ctx.font = fontSize + "px monospace";

      for (let i = 0; i < drops.length; i++) {
        const text = chars[Math.floor(Math.random() * chars.length)];
        const colorIndex =
          Math.floor(((drops[i] * fontSize) / canvas.height) * colors.length) %
          colors.length;
        ctx.fillStyle = colors[colorIndex];
        ctx.fillText(text, i * fontSize, drops[i] * fontSize);

        if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
          drops[i] = 0;
        }
        drops[i]++;
      }
    };

    const interval = setInterval(render, 50);
    return () => clearInterval(interval);
  }, []);

  return <canvas ref={canvasRef} className="matrix-rain" />;
};

export default MatrixRain;
