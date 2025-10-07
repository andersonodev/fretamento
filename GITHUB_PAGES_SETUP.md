# 📋 GitHub Pages Setup

Para habilitar o GitHub Pages e permitir que a documentação seja publicada:

## 🔧 Configuração Necessária no GitHub

1. **Acesse as configurações do repositório:**
   - Vá para: `https://github.com/andersonodev/fretamento/settings/pages`

2. **Configure a fonte:**
   - Source: `GitHub Actions`
   - Não selecione branch específica, pois estamos usando GitHub Actions

3. **Verificar permissões:**
   - Certifique-se que Actions têm permissão para escrever no Pages
   - Settings > Actions > General > Workflow permissions
   - Selecione "Read and write permissions"

## 🚀 Após a configuração

O workflow será executado automaticamente quando:
- Houver push na branch `main`
- Arquivos na pasta `docs/` forem modificados
- O workflow `.github/workflows/docs.yml` for alterado

A documentação estará disponível em:
`https://andersonodev.github.io/fretamento/`

## 🐛 Troubleshooting

Se o workflow ainda falhar:
1. Verifique se o GitHub Pages está habilitado
2. Confirme se as permissões do GITHUB_TOKEN estão corretas
3. Verifique os logs do workflow no GitHub Actions

## 📁 Estrutura Atual

```
docs/
├── mkdocs.yml          # Configuração principal (simplificada)
├── docs/
│   ├── index.md        # Página inicial
│   ├── architecture.md # Arquitetura
│   ├── algorithms.md   # Algoritmos
│   └── ...
└── site/              # Gerado pelo MkDocs (não commitado)
```