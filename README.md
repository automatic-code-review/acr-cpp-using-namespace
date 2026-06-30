# acr-cpp-using-namespace

Arquivo config.json

- message
    - Mensagem que sera apresentada por arquivo
        - ${FILE_PATH} diz respeito ao path do arquivo
        - ${ORDERED} diz respeito a ordem correta dos using namespace
- regexOrder
    - Lista de objetos referente aos regex de ordenação
    - orderType
        - group: Ordena os includes do grupo inteiro
        - individual: Ordena os includes de cada refex individualmente

```json
{
  "message": "Ordenação de using namespace esta incorreta no arquivo ${FILE_PATH}<br>Ordenação correta é:<br><br>${ORDERED}",
  "regexOrder": [
    {
      "orderType": "group",
      "regex": [
        ""
      ]
    },
    {
      "orderType": "individual",
      "regex": [
        ""
      ]
    }
  ]
}
```

## Rodar teste unitario

Se ainda nao tiver um ambiente virtual criado:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Com o ambiente ativo, execute os testes:

```bash
python -m unittest tests/test_review.py -v
```

Para sair do ambiente virtual:

```bash
deactivate
```
