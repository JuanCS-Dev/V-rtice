
# 🚀 Guia de Deploy e Publicação do Vértice CLI

Este guia descreve o processo de build, versionamento e publicação do Vértice CLI no PyPI (Python Package Index) para que ele possa ser instalado via `pip`.

## 1. Build do Pacote

O Vértice CLI usa `setuptools` para o empacotamento. O arquivo `setup.py` na raiz do projeto define a configuração do pacote.

Para criar os artefatos de distribuição, execute o seguinte comando na raiz do projeto:

```bash
python3 setup.py sdist bdist_wheel
```

- `sdist`: Cria uma distribuição de fonte (`.tar.gz`), que inclui os metadados e o código-fonte.
- `bdist_wheel`: Cria uma distribuição "Wheel" (`.whl`), que é um formato de build pré-compilado e mais rápido de instalar.

Após a execução, você encontrará os arquivos gerados em um novo diretório chamado `dist/`.

## 2. Versionamento

Seguimos o padrão de Versionamento Semântico (SemVer): `MAJOR.MINOR.PATCH`.

- **MAJOR:** Incrementado para mudanças incompatíveis de API (breaking changes).
- **MINOR:** Incrementado para adicionar novas funcionalidades de forma retrocompatível.
- **PATCH:** Incrementado para correções de bugs retrocompatíveis.

Antes de publicar uma nova versão, certifique-se de que a variável `version` no arquivo `setup.py` foi atualizada.

```python
# setup.py

setup(
    name='vcli',
    version='1.1.0',  # ATUALIZE AQUI
    # ...
)
```

## 3. Publicação no PyPI

A publicação é feita usando a ferramenta `twine`.

### Pré-requisitos:

1.  **Instalar o `twine`:**
    ```bash
    pip install twine
    ```

2.  **Criar uma conta no PyPI:**
    - Crie uma conta em [pypi.org](https://pypi.org/).
    - É altamente recomendado usar a autenticação de dois fatores (2FA).

3.  **Gerar um Token de API:**
    - Nas configurações da sua conta no PyPI, vá para "API tokens".
    - Crie um novo token. Você pode escopá-lo para um projeto específico.
    - **Copie o token imediatamente.** Você não poderá vê-lo novamente.

### Processo de Publicação:

1.  **Limpe o diretório `dist/` antigo:**
    ```bash
    rm -rf dist/
    ```

2.  **Construa a nova versão:**
    ```bash
    python3 setup.py sdist bdist_wheel
    ```

3.  **Faça o Upload com `twine`:**
    - O `twine` solicitará seu nome de usuário e senha. Para o nome de usuário, use `__token__`. Para a senha, cole o token de API que você gerou.
    ```bash
    twine upload dist/*
    ```

    - **Nome de usuário:** `__token__`
    - **Senha:** `pypi-AgEIcHlwaS5vcmc...` (seu token)

Após o upload bem-sucedido, a nova versão do `vcli` estará disponível publicamente e poderá ser instalada por qualquer pessoa com:

```bash
pip install vcli
```

## 4. Checklist de Release

Antes de publicar uma nova versão, siga este checklist:

- [ ] A versão no `setup.py` foi incrementada?
- [ ] Todas as novas funcionalidades estão documentadas?
- [ ] O `CHANGELOG.md` foi atualizado com as mudanças da nova versão?
- [ ] Todos os testes estão passando (`pytest`)?
- [ ] O linter não reporta erros (`flake8` / `pylint`)?
- [ ] O build local (`python3 setup.py sdist bdist_wheel`) funciona sem erros?
- [ ] As mudanças foram mescladas na branch `main`?
- [ ] Uma tag Git foi criada para a versão (ex: `git tag -a v1.1.0 -m "Version 1.1.0"`)?
