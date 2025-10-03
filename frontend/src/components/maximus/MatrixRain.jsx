/**
 * Matrix Rain Effect - Bem sutil (azul → roxo)
 * Códigos binários caindo suavemente no background
 */

import React, { useEffect, useRef } from 'react';

export const MatrixRain = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // Set canvas size
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    // Characters for matrix effect (binary + hex)
    const chars = '01';
    const fontSize = 14;
    const columns = canvas.width / fontSize;

    // Array para track posição de cada coluna
    const drops = Array(Math.floor(columns)).fill(0);

    // Cores do gradiente: azul → roxo (BEM sutis)
    const colors = [
      'rgba(6, 182, 212, 0.15)',    // Cyan bem leve
      'rgba(59