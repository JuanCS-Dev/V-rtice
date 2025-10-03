
# 📝 Relatório de Licenças de Dependências

**Data da Análise:** 2025-10-02

Este relatório resume as licenças das dependências diretas do projeto Vértice CLI, conforme especificado no `requirements.txt`.

## Resumo

A maioria das dependências usa licenças permissivas como MIT, Apache 2.0 e BSD, que são adequadas para uso em um projeto comercial. Não foram identificadas licenças restritivas (como a GPL) que pudessem impor obrigações de "copyleft" ao projeto.

## Licenças por Pacote

| Pacote                  | Versão Instalada | Licença                          | Tipo de Licença | Risco de Compatibilidade |
| ----------------------- | ---------------- | -------------------------------- | --------------- | ------------------------ |
| `typer`                 | 0.19.2           | MIT License                      | Permissiva      | Baixo                    |
| `rich`                  | 14.1.0           | MIT License                      | Permissiva      | Baixo                    |
| `httpx`                 | 0.25.0           | BSD 3-Clause                     | Permissiva      | Baixo                    |
| `PyYAML`                | 6.0.3            | MIT License                      | Permissiva      | Baixo                    |
| `python-dotenv`         | 1.0.0            | BSD 3-Clause                     | Permissiva      | Baixo                    |
| `questionary`           | 2.1.1            | MIT License                      | Permissiva      | Baixo                    |
| `diskcache`             | 5.6.3            | Apache 2.0                       | Permissiva      | Baixo                    |
| `typing-extensions`     | 4.15.0           | Python Software Foundation (PSF) | Permissiva      | Baixo                    |
| `google-auth`           | 2.40.3           | Apache 2.0                       | Permissiva      | Baixo                    |
| `google-auth-oauthlib`  | 1.2.2            | Apache 2.0                       | Permissiva      | Baixo                    |
| `google-auth-httplib2`  | 0.2.0            | Apache 2.0                       | Permissiva      | Baixo                    |
| `keyring`               | 25.6.0           | MIT License                      | Permissiva      | Baixo                    |
| `cryptography`          | 46.0.2           | Apache-2.0 OR BSD-3-Clause       | Permissiva      | Baixo                    |
| `google-generativeai`   | 0.8.5            | Apache 2.0                       | Permissiva      | Baixo                    |
| `prompt-toolkit`        | 3.0.52           | BSD 3-Clause                     | Permissiva      | Baixo                    |

## Análise de Compatibilidade

- **MIT, Apache 2.0, BSD:** Estas são licenças permissivas que permitem o uso, a modificação e a distribuição (inclusive comercial), exigindo apenas a manutenção do aviso de copyright e da licença original. Elas são compatíveis entre si e não impõem riscos ao licenciamento do projeto Vértice CLI.
- **PSF License:** A licença da Python Software Foundation também é permissiva e semelhante à licença BSD, sendo totalmente compatível.

## Conclusão

O licenciamento das dependências diretas do projeto é claro e não apresenta conflitos. O projeto pode ser distribuído e modificado sem preocupações com obrigações de "copyleft" impostas por suas dependências diretas. Uma análise mais profunda poderia incluir as licenças das dependências *transitivas*, mas, dado o conjunto de pacotes, é improvável que surjam conflitos significativos.
