# Mutation Testing

## Por que isso existe

Cobertura de testes (`% de linhas executadas`) é uma métrica enganosa: um teste pode passar por cima de uma linha sem checar nada de relevante sobre o resultado, e ainda assim contar como "coberta". **Mutation testing** prova que os testes realmente detectam bugs: a ferramenta (`mutmut`) modifica o código-fonte de propósito — troca um `>` por `<`, substitui uma string por outra, remove um argumento — gerando "mutantes", e roda a suíte de testes contra cada um. Um mutante **morto** significa que algum teste falhou (bom: o teste realmente protege aquele trecho). Um mutante **sobrevivente** significa que nenhum teste percebeu a mudança — ou seja, aquele trecho não está testado de verdade, mesmo que apareça como "coberto".

## Resultado atual

Rodado contra os módulos mais densos em lógica de negócio do core (`errors.py`, `registry.py`, `openops_business/products/models.py`):

```
54 mutantes gerados
52 mortos     (96%)
 1 sem testes (código sem cobertura, já esperado)
 1 sobrevivente — documentado abaixo
```

### O único sobrevivente (e por que ele fica assim de propósito)

```python
def http_status_for(error: OpenOpsError) -> int:
    for cls in type(error).__mro__:
        if cls in HTTP_STATUS_BY_ERROR:
            return HTTP_STATUS_BY_ERROR[cls]
    return 500  # pragma: no cover
```

Toda subclasse de `OpenOpsError` encontra `OpenOpsError` (mapeada para 500) em algum ponto do seu MRO — então essa última linha é, hoje, matematicamente inalcançável por qualquer chamada válida. Ela existe como defesa contra uma mudança futura na hierarquia de exceções que quebre essa garantia. `mutmut` a mostrou como sobrevivente corretamente: não há como escrever um teste que a exercite sem violar a assinatura de tipos da própria função.

### O que a primeira rodada encontrou (e como foi corrigido)

Antes dos ajustes, o placar era **35 mortos / 18 sobreviventes**. A maioria dos sobreviventes revelava o mesmo padrão: testes que verificavam apenas o **tipo** da exceção levantada (`pytest.raises(ConflictError)`), mas nunca o **conteúdo** — mensagem, `details`, ou os campos preenchidos por `register_module()`. Ou seja, mutantes que trocavam a mensagem de erro por `None`, ou o conteúdo de `details` por outro dicionário, passavam sem que nenhum teste percebesse.

A correção não foi enfraquecer o mutmut nem marcar tudo como `pragma: no cover` — foi reforçar os testes de verdade, verificando explicitamente mensagem, `details` e todos os campos de `ModuleInfo`. Veja o histórico de commits deste arquivo e de `openops_core/tests/test_errors.py` / `test_registry.py` para o antes/depois.

## Como rodar você mesmo

```bash
cd python
pip install -e ".[dev]"
mutmut run
mutmut results       # lista todos os mutantes e seu status
mutmut show <id>      # mostra o diff exato de um mutante específico
```

O escopo (`source_paths` em `pyproject.toml`, seção `[tool.mutmut]`) está deliberadamente limitado aos módulos de lógica pura (`errors.py`, `registry.py`, `models.py`) — módulos de I/O pesado (`db.py`, `router.py`) são mal candidatos a mutation testing (mutantes ali tendem a ser mortos ou sobreviver por motivos de infraestrutura, não de lógica de negócio) e tornariam a rodada muito mais lenta sem adicionar sinal proporcional.
