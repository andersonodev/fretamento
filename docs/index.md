# Documentação do Sistema de Fretamento

Bem-vindo à documentação oficial do sistema de gestão de escalas e fretamentos. Este material reúne as informações necessárias para entender a arquitetura da aplicação, executar procedimentos operacionais e garantir um deploy seguro.

## Seções Principais

- [Arquitetura Geral](architecture.md)
- [Melhorias de Performance](performance.md)
- [Segurança e Boas Práticas](security.md)
- [Guia de Deploy com SQLite](deployment.md)
- [Diagramas de Referência](diagrams/README.md)

## Visão Geral

O sistema é uma aplicação Django focada na administração de escalas de transporte, com workflows que englobam criação, agrupamento, otimização e exportação de dados. As melhorias recentes priorizaram:

- Redução significativa do número de consultas em páginas críticas (seleção de ano, mês e gerenciamento diário).
- Ajustes de segurança alinhados a um ambiente de produção, incluindo proteção de cookies, uso de variáveis de ambiente e middleware de arquivos estáticos.
- Preparação completa para documentação com MkDocs, permitindo a publicação rápida deste conteúdo.

## Como Navegar

1. Instale as dependências de documentação (ver `requirements.txt`).
2. Execute `mkdocs serve` para visualizar a documentação localmente.
3. Utilize a navegação lateral do MkDocs para acessar os tópicos detalhados.

Boa leitura e bons deploys!
