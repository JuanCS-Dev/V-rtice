# ⚠️ REVERTER MODELO GEMINI APÓS TESTES

**Data**: 04 de Outubro de 2025
**Motivo**: Teste temporário com `gemini-1.5-flash` (sem quota)

---

## 🔄 MUDANÇAS TEMPORÁRIAS

### Arquivos Modificados:
1. `backend/services/maximus_core_service/gemini_client.py`
2. `backend/services/maximus_core_service/main.py`

### Mudança Feita:
```python
# ANTES (modelo original - quota esgotada até amanhã 09:47):
model: str = "gemini-2.0-flash-exp"

# DEPOIS (modelo temporário para testes):
model: str = "gemini-1.5-flash"
```

---

## 🔙 COMO REVERTER

### Opção 1: Restaurar Backups
```bash
cd /home/juan/vertice-dev/backend/services/maximus_core_service

# Restaurar arquivos originais
cp gemini_client.py.backup gemini_client.py
cp main.py.backup main.py

# Reiniciar serviço
docker compose restart maximus_core_service
```

### Opção 2: Edição Manual
Editar os arquivos e mudar de volta:
```python
# gemini_client.py linha 26
model: str = "gemini-2.0-flash-exp"  # Fastest & cheapest

# main.py linha 111
model="gemini-2.0-flash-exp",
```

---

## ⏰ QUANDO REVERTER

**DEPOIS DE 05 de Outubro de 2025 às 09:47**
(quando a quota do gemini-2.0-flash-exp resetar)

---

## ✅ CHECKLIST DE REVERSÃO

- [ ] Data/hora passou de 05/Out/2025 09:47
- [ ] Restaurar `gemini_client.py` do backup
- [ ] Restaurar `main.py` do backup
- [ ] Reiniciar `maximus_core_service`
- [ ] Testar endpoint `/api/analyze`
- [ ] Deletar arquivo `gemini_client.py.backup`
- [ ] Deletar arquivo `main.py.backup`
- [ ] Deletar este arquivo de instrução

---

**Comando único para reverter tudo:**
```bash
cd /home/juan/vertice-dev/backend/services/maximus_core_service && \
cp gemini_client.py.backup gemini_client.py && \
cp main.py.backup main.py && \
cd /home/juan/vertice-dev && \
docker compose restart maximus_core_service && \
echo "✅ Modelo revertido para gemini-2.0-flash-exp"
```
