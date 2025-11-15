# 🎨 MAXIMUS Background Effects - Guia de Criação

## 📋 Visão Geral

Sistema escalável e modular para criar efeitos visuais de background no MAXIMUS AI Dashboard.

**Ideal para**: Ensinar AI a criar novos efeitos visuais personalizados!

---

## ✨ Efeitos Disponíveis

### 1. **Scanline** (━)

Linha horizontal descendo pela tela (clássico).

- **Tecnologia**: CSS puro com animation
- **Performance**: Excelente (GPU accelerated)
- **Complexidade**: ⭐

### 2. **Matrix Rain** (⋮) - PADRÃO

Códigos binários caindo estilo Matrix.

- **Tecnologia**: HTML5 Canvas + JavaScript
- **Performance**: Boa (60 FPS)
- **Complexidade**: ⭐⭐⭐
- **Cores**: Gradiente azul (#06B6D4) → roxo (#8B5CF6)
- **Características**:
  - Códigos esmaecendo de cima para baixo
  - BEM sutil (quase invisível)
  - Texto: `01MAXIMUS` (binary + nome)

### 3. **Particles** (∴)

Partículas flutuantes conectadas.

- **Tecnologia**: HTML5 Canvas
- **Performance**: Boa
- **Complexidade**: ⭐⭐
- **Características**:
  - 50 partículas com movimento suave
  - Linhas conectando partículas próximas
  - Bounce nas bordas

### 4. **None** (○)

Desabilita efeitos de background.

---

## 🚀 Como Adicionar um Novo Efeito

### Passo 1: Criar o Componente

Abra `/frontend/src/components/maximus/BackgroundEffects.jsx` e adicione:

```jsx
// ═══════════════════════════════════════════════════════════════════════════
// EFEITO 5: WAVE (Exemplo - ondas animadas)
// ═══════════════════════════════════════════════════════════════════════════
export const WaveEffect = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    // Configuração
    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);

    // Variáveis da onda
    let offset = 0;

    // Função de desenho
    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Desenhar onda
      ctx.beginPath();
      ctx.moveTo(0, canvas.height / 2);

      for (let x = 0; x < canvas.width; x++) {
        const y = canvas.height / 2 + Math.sin((x + offset) * 0.01) * 50;
        ctx.lineTo(x, y);
      }

      ctx.strokeStyle = "rgba(139, 92, 246, 0.3)";
      ctx.lineWidth = 2;
      ctx.stroke();

      offset += 2;
    };

    // Animation loop
    const interval = setInterval(draw, 1000 / 60);

    return () => {
      clearInterval(interval);
      window.removeEventListener("resize", resizeCanvas);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        zIndex: 1,
        pointerEvents: "none",
      }}
    />
  );
};
```

### Passo 2: Registrar no Array

No mesmo arquivo, adicione ao array `AVAILABLE_EFFECTS`:

```jsx
export const AVAILABLE_EFFECTS = [
  // ... efeitos existentes ...
  {
    id: "wave",
    name: "Wave",
    description: "Ondas animadas atravessando a tela",
    icon: "〜",
    component: WaveEffect,
  },
];
```

### Passo 3: Pronto!

O efeito aparece automaticamente no seletor. Não precisa modificar mais nada!

---

## 🎨 Guia de Estilo para Efeitos

### Cores Recomendadas

Use sempre tons da paleta MAXIMUS para manter consistência:

```jsx
// Primary (Roxo)
"rgba(139, 92, 246, 0.X)"; // #8B5CF6

// Secondary (Cyan)
"rgba(6, 182, 212, 0.X)"; // #06B6D4

// Success (Verde)
"rgba(16, 185, 129, 0.X)"; // #10B981

// Danger (Vermelho)
"rgba(239, 68, 68, 0.X)"; // #EF4444

// Warning (Laranja)
"rgba(245, 158, 11, 0.X)"; // #F59E0B
```

**Opacidade**: Sempre BEM sutil! Use valores entre `0.05` e `0.4`.

### Performance Guidelines

1. **Usar `requestAnimationFrame` quando possível** (melhor que `setInterval`)
2. **Canvas clearing strategy**:
   - Para rastros: `fillRect` com alpha baixo
   - Sem rastros: `clearRect`
3. **FPS Target**: 60 FPS (16.6ms por frame)
4. **Cleanup**: Sempre limpar timers/listeners no `return`

### Template Básico (Canvas)

```jsx
export const MeuEfeito = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    // Setup
    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);

    // State do efeito
    let animationState = {};

    // Draw function
    const draw = () => {
      // Limpar ou deixar rastro
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      // ou
      // ctx.fillStyle = 'rgba(15, 23, 42, 0.1)';
      // ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Desenhar efeito
      // ...

      // Atualizar state
      // ...
    };

    // Animation loop
    const interval = setInterval(draw, 1000 / 60);

    // Cleanup
    return () => {
      clearInterval(interval);
      window.removeEventListener("resize", resizeCanvas);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        zIndex: 1,
        pointerEvents: "none",
      }}
    />
  );
};
```

### Template Básico (CSS)

```jsx
export const MeuEfeitoCSS = () => {
  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        zIndex: 1,
        pointerEvents: "none",
        // Seu CSS aqui
        background: "linear-gradient(...)",
        animation: "minhaAnimation 5s infinite",
      }}
    />
  );
};
```

---

## 💡 Ideias para Novos Efeitos

### Nível Fácil (⭐)

- **Gradient Shift**: Gradiente que muda de cor suavemente
- **Pulse**: Pulsação de luz do centro
- **Grid Lines**: Linhas de grid se movendo

### Nível Médio (⭐⭐)

- **DNA Helix**: Hélice dupla rotacionando
- **Binary Rain**: Similar ao Matrix mas mais aleatório
- **Starfield**: Campo de estrelas se movendo

### Nível Avançado (⭐⭐⭐)

- **Neural Network**: Nodes conectados como rede neural
- **Fractal**: Padrões fractais animados
- **3D Cube**: Cubo wireframe rotacionando (perspective CSS)
- **Waveform**: Forma de onda de áudio (pode conectar com microfone!)

---

## 🧪 Testing

### Checklist para Novo Efeito

- [ ] Performance: Mantém 60 FPS?
- [ ] Responsive: Funciona em diferentes resoluções?
- [ ] Cleanup: Remove listeners/timers corretamente?
- [ ] Cores: Usa paleta MAXIMUS?
- [ ] Opacidade: BEM sutil (não distrai do conteúdo)?
- [ ] Pointer Events: `pointerEvents: 'none'`?
- [ ] Z-Index: Correto (atrás do conteúdo)?

### Testar Performance

```javascript
// Adicionar no início do draw()
const startTime = performance.now();

// Seu código de desenho

// Adicionar no final do draw()
const endTime = performance.now();
console.log(`Frame time: ${(endTime - startTime).toFixed(2)}ms`);
// Target: < 16.6ms (60 FPS)
```

---

## 📊 Comparação de Efeitos

| Efeito    | Performance | Complexidade | Uso de CPU | Uso de GPU |
| --------- | ----------- | ------------ | ---------- | ---------- |
| Scanline  | ⭐⭐⭐⭐⭐  | ⭐           | Baixo      | Alto       |
| Matrix    | ⭐⭐⭐⭐    | ⭐⭐⭐       | Médio      | Médio      |
| Particles | ⭐⭐⭐⭐    | ⭐⭐         | Médio      | Médio      |
| None      | ⭐⭐⭐⭐⭐  | -            | Zero       | Zero       |

---

## 🔧 Troubleshooting

### Efeito não aparece

1. Verificar se foi adicionado ao `AVAILABLE_EFFECTS`
2. Verificar console do browser por erros
3. Confirmar que `z-index: 1` (atrás do header que é `10`)

### Performance ruim

1. Reduzir número de elementos desenhados
2. Usar `requestAnimationFrame` em vez de `setInterval`
3. Implementar culling (não desenhar fora da viewport)
4. Reduzir opacidade (menos blend operations)

### Efeito não responde ao resize

Adicionar listener:

```javascript
window.addEventListener("resize", resizeCanvas);
// Cleanup:
return () => window.removeEventListener("resize", resizeCanvas);
```

---

## 📝 Contribuindo

### Regras para PRs de Novos Efeitos

1. **Performance**: Deve manter 60 FPS em máquinas médias
2. **Documentação**: Adicionar comentários explicando lógica
3. **Naming**: Nome descritivo e único
4. **Icon**: Escolher emoji/caractere representativo
5. **Description**: Descrever em 1 linha o que faz

### Exemplo de Commit

```
feat(effects): Add DNA Helix background effect

- Animated double helix rotating smoothly
- Uses purple/cyan gradient
- 60 FPS on mid-tier hardware
- Cleanup handles resize events properly
```

---

## 🎓 Recursos de Aprendizado

### Canvas API

- [MDN Canvas Tutorial](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API/Tutorial)
- [Canvas Cheat Sheet](https://simon.html5.org/dump/html5-canvas-cheat-sheet.html)

### Math para Animações

- `Math.sin()` / `Math.cos()` - Ondas e rotações
- `Math.random()` - Aleatoriedade
- `Math.atan2()` - Ângulos entre pontos

### Performance

- [Rendering Performance](https://web.dev/rendering-performance/)
- [requestAnimationFrame](https://developer.mozilla.org/en-US/docs/Web/API/window/requestAnimationFrame)

---

## 🏆 Hall da Fama

Melhores efeitos criados pela comunidade (espaço reservado para futuro):

1. **TBD** - Aguardando primeiro efeito custom!
2. **TBD**
3. **TBD**

---

**Criado com 💜 para o Projeto MAXIMUS**

_"Ensine a AI a sonhar visualmente"_
