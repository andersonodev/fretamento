# Melhorias de Performance

## Resumo das Otimizações

1. **Consultas Agregadas**
   - Páginas de seleção de ano e mês passaram a usar `ExtractYear/ExtractMonth` com agregações (`Count`, `Sum`) para reduzir centenas de consultas N+1.
   - A tela de gerenciamento mensal anota `total_servicos`, `total_pax` e `total_valor`, evitando cálculos em templates.

2. **Prefetch e Cache Local**
   - A visualização diária de escalas pré-carrega alocações e grupos com `Prefetch`, garantindo que loops em memória não gerem consultas extras.
   - O resultado fornece totais por van e totais gerais sem hits adicionais ao banco.

3. **Remoção de `print` e Logs Ineficientes**
   - Logs de depuração substituíram `print`, reduzindo I/O desnecessário e melhorando a legibilidade do log de produção.

## Métricas Esperadas

| Página                              | Antes                               | Depois                              |
|-------------------------------------|--------------------------------------|-------------------------------------|
| Selecionar Ano                      | Consultas por escala + propriedades  | 1 consulta agregada por ano         |
| Selecionar Mês                      | Consultas por mês + soma manual      | 1 consulta agregada por mês         |
| Gerenciar Escalas (lista diária)    | 1 consulta + N propriedades (somatórias)| 1 consulta anotada com totais      |
| Visualizar Escala (detalhe diário)  | Múltiplas consultas por van/grupo    | 1 carregamento com `prefetch_related` |

## Recomendações

- Utilizar `django-debug-toolbar` em ambientes de homologação para confirmar contagem de queries.
- Manter o uso de `Prefetch` e `select_related` ao adicionar novos relacionamentos.
- Validar periodicamente índices no banco caso migre para outra engine (PostgreSQL, por exemplo).
