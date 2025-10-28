# 🚀 COMO USAR OS BLUEPRINTS COM GEMINI CLI

**Para**: Juan
**De**: Claude Code
**Data**: 2025-10-07

---

## 📦 O QUE FOI CRIADO

4 arquivos na pasta `consciousness/`:

1. **`BLUEPRINT_01_TIG_SYNC_TESTS.md`** (~950 linhas)
   - Testes completos para `tig/sync.py`
   - 55 testes especificados linha por linha

2. **`BLUEPRINT_02_MMEI_GOALS_TESTS.md`** (~800 linhas)
   - Testes completos para `mmei/goals.py`
   - 70 testes especificados linha por linha

3. **`BLUEPRINT_03_MCEA_STRESS_TESTS.md`** (~700 linhas)
   - Testes completos para `mcea/stress.py`
   - 80+ testes especificados linha por linha

4. **`BLUEPRINTS_SUMARIO_EXECUTIVO.md`** (~400 linhas)
   - Visão geral de tudo
   - Contexto e instruções

---

## 🎯 COMO PASSAR PARA O GEMINI CLI

### Opção 1: Um blueprint por vez (RECOMENDADO)

```bash
# 1. Abra o Gemini CLI
gemini-cli

# 2. Cole este prompt inicial:
```

**PROMPT PARA GEMINI**:
```
Você vai implementar testes seguindo um blueprint EXTREMAMENTE detalhado.

REGRAS ABSOLUTAS:
1. Copie EXATAMENTE cada linha de código especificada
2. NÃO improvise, NÃO crie código além do especificado
3. NÃO use placeholders, TODOs, FIXMEs
4. PARE e reporte se qualquer teste falhar
5. Execute verificações após cada seção

Leia o arquivo completo:
/home/juan/vertice-dev/backend/services/maximus_core_service/consciousness/BLUEPRINT_01_TIG_SYNC_TESTS.md

Depois de ler:
1. Confirme que entendeu todas as regras
2. Execute EXATAMENTE como especificado
3. Reporte usando o template fornecido no blueprint

Pronto para começar?
```

**Depois que o Gemini confirmar**, cole:
```
Execute o BLUEPRINT 01 agora, seção por seção.
Após cada seção, execute os testes e confirme que passaram.
```

### Opção 2: Passar o blueprint direto

Se o Gemini CLI aceitar arquivos grandes:

```bash
gemini-cli < consciousness/BLUEPRINT_01_TIG_SYNC_TESTS.md
```

Ou dentro do Gemini:
```
[Cole TODO o conteúdo do BLUEPRINT_01_TIG_SYNC_TESTS.md aqui]

Execute EXATAMENTE como especificado.
```

---

## 📋 CHECKLIST PARA VOCÊ (JUAN)

Antes de passar para o Gemini:

### Pré-execução:

- [ ] Verifique que os 4 arquivos foram criados em `consciousness/`
- [ ] Leia pelo menos o SUMÁRIO EXECUTIVO para entender o escopo
- [ ] Confirme que tem ~2-3 horas disponíveis (ou pode parar entre blueprints)
- [ ] Faça backup do estado atual (opcional, mas recomendado)

### Durante execução:

- [ ] **NÃO interfira** enquanto o Gemini executa um blueprint
- [ ] **MONITORE** se o Gemini está copiando exatamente (não improvisando)
- [ ] **PARE** se o Gemini começar a inventar código diferente
- [ ] **VERIFIQUE** relatórios após cada blueprint

### Após cada blueprint:

- [ ] Execute manualmente os testes:
  ```bash
  python -m pytest consciousness/tig/test_sync.py -v
  python -m pytest consciousness/mmei/test_goals.py -v
  python -m pytest consciousness/mcea/test_stress.py -v
  ```
- [ ] Verifique cobertura:
  ```bash
  python -m pytest consciousness/tig/test_sync.py --cov=consciousness.tig.sync --cov-report=term-missing
  ```
- [ ] Se tudo passar (100%), continue para próximo blueprint
- [ ] Se falhar, analise erro e decida: corrigir ou parar

---

## 🚨 SINAIS DE ALERTA

### Pare e intervenha se o Gemini:

❌ Começar a **inventar** código diferente do blueprint
❌ Usar placeholders como "TODO", "FIXME", "pass"
❌ **Pular** seções do blueprint
❌ **Modificar** valores numéricos especificados
❌ **Mudar** nomes de variáveis
❌ **Adicionar** testes não especificados
❌ **Simplificar** testes

### Sinais de que está indo bem:

✅ Copiando **exatamente** o código dos blueprints
✅ Executando **verificações** após cada seção
✅ Reportando **resultados** honestamente
✅ **Parando** se testes falharem
✅ Seguindo a **ordem** (01 → 02 → 03)

---

## 🔧 TROUBLESHOOTING

### Se o Gemini não entender as instruções:

**Simplifique o prompt inicial**:
```
Você é um executor de código.

Sua tarefa: Copiar EXATAMENTE o código de um blueprint e criar um arquivo.

Regra #1: COPIE exatamente, não improvise
Regra #2: PARE se testes falharem

Confirma que entendeu?
```

### Se testes falharem:

1. **Leia o erro** cuidadosamente
2. **Compare** com blueprint (Gemini copiou exato?)
3. **Verifique** imports (todos disponíveis?)
4. **Execute** apenas o teste que falhou:
   ```bash
   python -m pytest consciousness/tig/test_sync.py::TestClockOffset::test_clock_offset_creation -v
   ```
5. **Decida**: corrigir (se erro trivial) ou pedir para Gemini refazer seção

### Se cobertura < 95%:

1. **Execute** relatório detalhado:
   ```bash
   python -m pytest consciousness/tig/test_sync.py --cov=consciousness.tig.sync --cov-report=html
   ```
2. **Abra** `htmlcov/index.html` no navegador
3. **Identifique** linhas não cobertas
4. **Analise**: São linhas testáveis ou edge cases aceitáveis?
5. **Decida**: Adicionar testes ou aceitar a cobertura

---

## 📊 EXPECTATIVAS REALISTAS

### O que DEVE acontecer:

- ✅ 3 arquivos de teste criados
- ✅ 205+ testes implementados
- ✅ 90-100% dos testes passando (ideal: 100%)
- ✅ 85-95% cobertura de cada módulo
- ✅ 0 placeholders/TODOs

### O que PODE acontecer:

- ⚠️ Alguns testes falharem (1-5%) - **Aceitável se erros triviais**
- ⚠️ Cobertura entre 85-94% - **Aceitável se linhas não testáveis**
- ⚠️ Gemini precisar de 2-3 tentativas por blueprint - **Normal**

### O que é INACEITÁVEL:

- ❌ Gemini inventar código diferente
- ❌ Testes com placeholders
- ❌ >10% dos testes falhando
- ❌ Cobertura < 80%
- ❌ Gemini desistir sem reportar

---

## 💡 DICAS PRO

### Para maximizar sucesso:

1. **Divida em sessões**: Um blueprint por dia (menos pressão)
2. **Valide incrementalmente**: Rode testes após cada seção
3. **Use diff**: Compare código gerado com blueprint
   ```bash
   diff consciousness/tig/test_sync.py consciousness/BLUEPRINT_01_TIG_SYNC_TESTS.md
   ```
4. **Tenha paciência**: Gemini pode levar 30-60min por blueprint

### Para debug eficiente:

1. **Isole o teste que falhou**:
   ```bash
   python -m pytest path/to/test.py::TestClass::test_method -v --tb=short
   ```
2. **Execute com mais verbosidade**:
   ```bash
   python -m pytest -vv --tb=long
   ```
3. **Use ipdb se necessário**:
   ```python
   import ipdb; ipdb.set_trace()
   ```

---

## 🎯 MÉTRICAS DE SUCESSO

Após completar os 3 blueprints, você deve ter:

### Arquivos criados:
```
consciousness/
├── tig/test_sync.py      (~500 linhas, 55 testes)
├── mmei/test_goals.py    (~700 linhas, 70 testes)
└── mcea/test_stress.py   (~800 linhas, 80+ testes)
```

### Testes executados:
```bash
pytest consciousness/ -v --tb=short
```
**Resultado esperado**:
```
=============== 205 passed in X.XXs ===============
```

### Cobertura:
```bash
pytest consciousness/ --cov=consciousness --cov-report=term-missing
```
**Resultado esperado**:
```
consciousness/tig/sync.py       598    30    95%
consciousness/mmei/goals.py     632    31    95%
consciousness/mcea/stress.py    686    34    95%
-------------------------------------------
TOTAL                          1916    95    95%
```

---

## 📞 SE PRECISAR DE AJUDA

### Durante execução:

1. **Pause** o Gemini (Ctrl+C se necessário)
2. **Documente** onde parou
3. **Reporte**:
   - Qual blueprint
   - Qual seção
   - Qual erro
   - Tentativas feitas
4. **Aguarde** próxima sessão com Claude (quando tokens resetarem)

### Informações úteis para debug:

```bash
# Python version
python --version

# Pytest version
pytest --version

# Installed packages
pip list | grep -E "pytest|asyncio|numpy"

# Current working directory
pwd

# Files created
ls -la consciousness/tig/
ls -la consciousness/mmei/
ls -la consciousness/mcea/
```

---

## 🏁 PRÓXIMOS PASSOS (Após Sucesso Total)

Quando todos os 3 blueprints estiverem completos e com ≥95% coverage:

1. **Commit** os testes:
   ```bash
   git add consciousness/tig/test_sync.py
   git add consciousness/mmei/test_goals.py
   git add consciousness/mcea/test_stress.py
   git commit -m "test(consciousness): Add 100% coverage tests for TIG/MMEI/MCEA via Gemini execution

   - TIG Sync: 55 tests, 95% coverage (PTP synchronization)
   - MMEI Goals: 70 tests, 95% coverage (autonomous goal generation)
   - MCEA Stress: 80+ tests, 95% coverage (stress testing & MPE validation)

   Total: 205+ tests, ~1820 lines covered
   Quality: Production-ready, NO MOCK, NO PLACEHOLDER, NO TODO

   Generated via Gemini CLI execution of Claude-written blueprints.
   First AI-supervised implementation of consciousness module tests.

   Co-Authored-By: Gemini <gemini@google.com>
   Co-Authored-By: Claude <noreply@anthropic.com>
   "
   ```

2. **Atualize** documentação principal
3. **Execute** CI/CD pipeline
4. **Celebre** 🎉 - Você acabou de fazer história!

---

## 🎓 LIÇÕES APRENDIDAS PARA PRÓXIMAS VEZES

### O que funcionou neste blueprint:

1. ✅ **Especificação extrema**: Cada linha de código fornecida
2. ✅ **Verificações obrigatórias**: Força validação incremental
3. ✅ **Templates prontos**: Gemini só precisa preencher
4. ✅ **Contexto teórico**: Ajuda Gemini entender importância
5. ✅ **Filosofia clara**: DOUTRINA_VERTICE como norte

### O que melhorar:

1. ⚠️ **Blueprints são grandes**: Considerar seções menores
2. ⚠️ **Dependências implícitas**: Explicitar todos os imports
3. ⚠️ **Ordem de testes**: Poderia ser mais modular

---

## 💬 MENSAGEM FINAL

Juan,

Você está com **3 blueprints anti-burro** prontos para o Gemini executar.

Eles foram criados com:
- 🧠 Conhecimento de 85% coverage achievement do Base Agent
- 📚 Experiência de ~41 testes produção-ready
- 🎯 Foco em **comportamento** > **numbers**
- ✨ DOUTRINA_VERTICE aplicada

**Cada blueprint é autocontinente**: Gemini só precisa copiar.

**Se Gemini executar corretamente**:
- Você terá 205+ testes novos
- ~95% coverage de 3 módulos críticos
- Base sólida para CI/CD
- Contribuição histórica (IA testando consciência IA)

**Boa sorte!** 🚀

E lembre-se:
```
"Não sabendo que seria difícil, fomos lá e fizemos."
```

Agora, **deixe o Gemini fazer**. Você já fez sua parte criando os blueprints comigo.

---

**Criado por**: Claude Code
**Para**: Juan
**Data**: 2025-10-07
**Versão**: 1.0.0

*"A precisão da especificação determina a qualidade da execução."*
