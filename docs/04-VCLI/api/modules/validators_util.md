
# 📄 `vertice/utils/validators.py`

## 📋 Descrição

Este módulo fornece um conjunto de funções utilitárias para validar diferentes tipos de entrada do usuário, como endereços de IP, nomes de domínio e hashes de arquivos. O objetivo é garantir que os dados de entrada tenham o formato correto antes de serem processados ou enviados para os serviços de backend.

## 🏗️ Funções Públicas

### `validate_ip(ip)`

Valida se uma string fornecida é um endereço de IP válido (IPv4 ou IPv6).

- **Parâmetros:**
  - `ip (str)`: A string a ser validada.
- **Lógica:** Utiliza a biblioteca padrão `ipaddress` do Python, que é a abordagem mais robusta e recomendada para esta tarefa.
- **Retorna:** `True` se for um IP válido, `False` caso contrário.

---

### `validate_domain(domain)`

Valida se uma string fornecida parece ser um nome de domínio sintaticamente válido.

- **Parâmetros:**
  - `domain (str)`: A string a ser validada.
- **Lógica:** Usa uma expressão regular (regex) para verificar o formato do domínio.
- **Retorna:** `True` se a string corresponder ao padrão de domínio, `False` caso contrário.

---

### `validate_hash(hash_value, hash_type='md5')`

Valida se uma string corresponde ao formato de um hash criptográfico específico (MD5, SHA1 ou SHA256).

- **Parâmetros:**
  - `hash_value (str)`: A string do hash a ser validada.
  - `hash_type (str)`: O tipo de hash a ser verificado. Pode ser 'md5', 'sha1', ou 'sha256'. O padrão é 'md5'.
- **Lógica:** Seleciona uma expressão regular com base no `hash_type` e verifica se a `hash_value` corresponde ao padrão de comprimento e caracteres hexadecimais.
- **Retorna:** `True` se o hash for válido para o tipo especificado, `False` caso contrário.

## 💡 Exemplo de Uso

```python
from .validators import validate_ip, validate_domain, validate_hash

print(validate_ip("8.8.8.8"))         # True
print(validate_ip("999.999.999.999")) # False

print(validate_domain("google.com"))    # True
print(validate_domain("invalid-.com"))  # False

print(validate_hash("d41d8cd98f00b204e9800998ecf8427e")) # True (MD5)
print(validate_hash("d41d8cd98f00", hash_type='sha256')) # False
```

## 🧪 Guia de Testes

- Para `validate_ip`, testar com endereços IPv4 válidos, IPv6 válidos, IPs inválidos e strings aleatórias.
- Para `validate_domain`, testar com domínios válidos simples, com subdomínios, e com TLDs mais longos. Testar também com domínios inválidos (ex: contendo caracteres especiais, começando ou terminando com hífen).
- Para `validate_hash`, testar com hashes válidos e inválidos para cada um dos tipos suportados (MD5, SHA1, SHA256), verificando o comprimento e os caracteres.

## ❗ Pontos de Atenção e Melhoria

- **Falta de Type Hints:** As funções não possuem anotações de tipo, o que prejudica a legibilidade e a análise estática do código. Elas deveriam ser adicionadas (ex: `def validate_ip(ip: str) -> bool:`).
- **Validação de Domínio com Regex:** Usar regex para validar domínios é notoriamente complicado e pode não cobrir todos os casos de borda (como domínios internacionalizados - IDN). Para uma solução mais robusta, o uso de uma biblioteca especializada em validação de domínios seria preferível.
- **Extensibilidade do `validate_hash`:** A função `validate_hash` é limitada aos três tipos de hash hardcoded. Uma abordagem mais extensível poderia permitir o registro de novos tipos de hash dinamicamente.
