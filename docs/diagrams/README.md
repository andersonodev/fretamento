# Diagramas

Esta pasta contém diagramas em Mermaid que representam fluxos chave da aplicação. Eles podem ser renderizados diretamente no MkDocs ou em ferramentas compatíveis (por exemplo, [Mermaid Live Editor](https://mermaid.live/)).

## Diagramas Disponíveis

- [architecture.mmd](architecture.mmd): visão macro dos componentes do sistema.
- [request-flow.mmd](request-flow.mmd): sequência típica desde a seleção de mês até a otimização de uma escala.

Para atualizar ou gerar imagens estáticas, execute:

```bash
mkdocs serve  # Visualização local
```

ou utilize bibliotecas como `mmdc` (Mermaid CLI).
