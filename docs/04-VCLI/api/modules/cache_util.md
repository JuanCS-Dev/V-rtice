
# 📄 `vertice/utils/cache.py`

## 📋 Descrição

Este módulo define uma classe `Cache` destinada a fornecer uma funcionalidade de cache simples baseada em arquivos para a CLI.

**IMPORTANTE:** No estado atual, este módulo é um **placeholder**. Nenhuma das funcionalidades de cache (get, set, clear) está implementada. A classe apenas cria o diretório de cache.

## 🏗️ Classes

### `Cache`

Classe que deveria gerenciar o cache em disco.

**Atributos:**
- `cache_dir (Path)`: O diretório `~/.vertice/cache` onde os itens de cache seriam armazenados.

**Métodos Públicos:**

#### `__init__(self, cache_dir=None)`
Inicializa o gerenciador de cache. Cria o diretório `~/.vertice/cache` se ele não existir.

#### `get(self, key, ttl=3600)`
**NÃO IMPLEMENTADO.** Deveria recuperar um valor do cache, respeitando um tempo de vida (TTL - Time To Live).

#### `set(self, key, value)`
**NÃO IMPLEMENTADO.** Deveria salvar um par chave-valor no cache.

#### `clear(self)`
**NÃO IMPLEMENTADO.** Deveria limpar todos os itens do diretório de cache.

## 💡 Exemplo de Uso (Teórico)

```python
from .cache import Cache

cache = Cache()

# Tenta obter dados do cache
cached_data = cache.get("my_api_data")

if cached_data:
    print("Data loaded from cache!")
    data = cached_data
else:
    print("Fetching data from API...")
    # data = api_call()
    # cache.set("my_api_data", data)
```

## 🧪 Guia de Testes

Como o módulo não está implementado, não há o que testar.

**Para a implementação real:**
- Testar se `set` cria um arquivo com o conteúdo correto.
- Testar se `get` recupera o conteúdo de um arquivo existente.
- Testar se `get` retorna `None` para uma chave inexistente.
- Testar a lógica de expiração do TTL: `get` deve retornar `None` se o item no cache for mais antigo que o `ttl` especificado.
- Testar se `clear` remove todos os arquivos do diretório de cache.

## ❗ Pontos de Atenção e Melhoria

- **Funcionalidade Inexistente (Crítico):** O débito técnico aqui é total. A ausência de um sistema de cache funcional impacta diretamente a performance da aplicação, resultando em chamadas de API desnecessárias e maior latência para o usuário. A implementação desta classe é de alta prioridade.
- **Alternativa Pronta:** A biblioteca `diskcache` já está listada no `requirements.txt`. Em vez de reinventar a roda, a classe `Cache` poderia ser um wrapper simples em torno do `diskcache.Cache`, o que já forneceria uma solução robusta, thread-safe e com gerenciamento de TTL.
- **Segurança:** Se o cache for implementado manualmente, é preciso garantir que a `key` seja sanitizada para evitar vulnerabilidades de Path Traversal ao criar os arquivos de cache.
