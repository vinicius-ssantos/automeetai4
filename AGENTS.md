# Instruções para a Junie AI

Este repositório utiliza o arquivo **AGENTS.md** para fornecer diretrizes à Junie AI durante a criação de PRs.

## Regras Gerais

- **Sempre execute os testes** antes de criar um PR. Use:
  ```bash
  python tests/run_tests_with_coverage.py
  ```
  Ajuste as opções conforme necessário (por exemplo `--html` ou `--min-coverage`).
- Siga as práticas descritas em `docs/developer_guide.md` e `.junie/guidelines.md`:
  - Use Python 3.8+ e preferencialmente um ambiente virtual.
  - Inclua *type hints* e docstrings no estilo Google, em português.
  - Respeite os princípios SOLID e utilize injeção de dependência.
- Não inclua chaves de API ou dados sensíveis no repositório.
- Documente qualquer nova configuração ou funcionalidade na pasta `docs/`.

Consulte a documentação em `docs/` para detalhes sobre arquitetura, estilo de código e procedimentos de contribuição.
