# 🔧 Melhoria: Padronização de C/GUIA e S/GUIA

**Data:** 17 de outubro de 2025  
**Desenvolvedor:** Anderson

## 📋 Resumo

Implementada a separação e padronização de "C/GUIA" e "S/GUIA" nos nomes de serviços.

---

## Problema Identificado

Na importação de planilhas, os serviços vinham com abreviações como:
- `TOUR P/ BÚZIOS C/GUIA` 
- `CITY TOUR S/GUIA`

Essas abreviações eram removidas completamente, perdendo informação importante sobre se o tour inclui ou não guia.

---

## Solução Implementada

### Arquivo Modificado: `core/processors.py`

Alteradas as linhas 207-208 do método `_limpar_servico`:

**ANTES:**
```python
servico = re.sub(r'S\s*\/\s*GUIA', '', servico, flags=re.IGNORECASE)  # Remove "S / GUIA"
servico = re.sub(r'C\s*\/\s*GUIA', '', servico, flags=re.IGNORECASE)  # Remove "C / GUIA"
```

**DEPOIS:**
```python
servico = re.sub(r'S\s*\/\s*GUIA', 'Sem Guia', servico, flags=re.IGNORECASE)  # Substitui "S/GUIA" por "Sem Guia"
servico = re.sub(r'C\s*\/\s*GUIA', 'Com Guia', servico, flags=re.IGNORECASE)  # Substitui "C/GUIA" por "Com Guia"
```

---

## Regras de Transformação

| Original | Transformado |
|----------|--------------|
| `C/GUIA` | `Com Guia` |
| `C / GUIA` | `Com Guia` |
| `c/guia` | `Com Guia` |
| `S/GUIA` | `Sem Guia` |
| `S / GUIA` | `Sem Guia` |
| `s/guia` | `Sem Guia` |

---

## Exemplos de Transformação

### Exemplo 1: Tour com Guia
```
Original:  "TOUR P/ BÚZIOS C/GUIA"
Resultado: "TOUR PARA BÚZIOS Com Guia"
```

### Exemplo 2: Tour sem Guia
```
Original:  "TOUR P/ BÚZIOS S/GUIA"
Resultado: "TOUR PARA BÚZIOS Sem Guia"
```

### Exemplo 3: Com número de linha
```
Original:  "001 - TOUR P/ BÚZIOS C/GUIA"
Resultado: "TOUR PARA BÚZIOS Com Guia"
```

### Exemplo 4: City Tour
```
Original:  "CITY TOUR C/GUIA"
Resultado: "CITY TOUR Com Guia"
```

### Exemplo 5: Com espaços
```
Original:  "TOUR P/ BÚZIOS C / GUIA"
Resultado: "TOUR PARA BÚZIOS Com Guia"
```

---

## Características da Implementação

### ✅ Case-Insensitive
A regex funciona com maiúsculas ou minúsculas:
- `C/GUIA`, `c/guia`, `C/guia` → todos viram `Com Guia`
- `S/GUIA`, `s/guia`, `S/guia` → todos viram `Sem Guia`

### ✅ Flexível com Espaços
Aceita variações de espaçamento:
- `C/GUIA`, `C / GUIA`, `C/ GUIA` → todos viram `Com Guia`

### ✅ Integrado ao Fluxo Existente
- Funciona no mesmo método `_limpar_servico`
- Aplicado automaticamente durante importação
- Combinado com outras transformações (P/ → PARA, etc.)

---

## Testes Realizados

Criado arquivo de teste: `tests/test_limpeza_guia.py`

### Casos de Teste
- ✅ TOUR P/ BÚZIOS C/GUIA
- ✅ TOUR P/ BÚZIOS S/GUIA
- ✅ TOUR P/ BÚZIOS C / GUIA (com espaços)
- ✅ TOUR P/ BÚZIOS S / GUIA (com espaços)
- ✅ 001 - TOUR P/ BÚZIOS C/GUIA (com prefixo numérico)
- ✅ CITY TOUR C/GUIA
- ✅ PASSEIO S/GUIA
- ✅ TOUR P/ BÚZIOS c/guia (lowercase)
- ✅ TOUR P/ BÚZIOS s/guia (lowercase)

**Resultado:** 🎉 Todos os 9 testes passaram!

---

## Benefícios

### 1. Preservação de Informação
- ✅ Mantém informação sobre inclusão de guia
- ✅ Facilita identificação do tipo de serviço
- ✅ Melhora a clareza dos nomes

### 2. Padronização
- ✅ Formato consistente: "Com Guia" e "Sem Guia"
- ✅ Capitalização correta
- ✅ Elimina variações de abreviação

### 3. Compatibilidade
- ✅ Não quebra lógica existente
- ✅ Funciona com outras transformações
- ✅ Retrocompatível com dados antigos

---

## Impacto no Sistema

### Upload de Planilhas
Ao fazer upload de uma planilha OS, os serviços serão automaticamente padronizados:

**Antes:**
```
001 - TRANSFER IN GIG PARA Z.SUL S/GUIA
TOUR P/ BÚZIOS C/GUIA
```

**Depois:**
```
TRANSFER IN GIG PARA ZONA SUL Sem Guia
TOUR PARA BÚZIOS Com Guia
```

### Visualização
Os serviços aparecerão com nomes mais claros e profissionais nas escalas e relatórios.

---

## Próximos Passos

1. ✅ Implementação concluída
2. ✅ Testes passando
3. ⏳ Testar com upload de planilha real
4. ⏳ Validar visualização nas escalas
5. ⏳ Documentar no manual do usuário

---

## Comandos para Testar

### Executar testes
```bash
python tests/test_limpeza_guia.py
```

### Fazer upload de planilha
1. Acesse: http://127.0.0.1:8000/core/upload/
2. Faça upload de uma planilha contendo serviços com "C/GUIA" e "S/GUIA"
3. Verifique se os nomes foram corretamente padronizados

---

## Observações Técnicas

### Regex Utilizada
```python
# Para C/GUIA
r'C\s*\/\s*GUIA'  # Aceita: C/GUIA, C / GUIA, C/ GUIA, C /GUIA

# Para S/GUIA
r'S\s*\/\s*GUIA'  # Aceita: S/GUIA, S / GUIA, S/ GUIA, S /GUIA
```

### Flags
- `re.IGNORECASE`: Aceita maiúsculas e minúsculas
- `\s*`: Aceita zero ou mais espaços

### Ordem de Execução
A transformação ocorre nesta sequência:
1. Remove prefixo numérico (001 -)
2. Substitui S/GUIA → Sem Guia
3. Substitui C/GUIA → Com Guia
4. Substitui P/ → PARA
5. Substitui Z.SUL → ZONA SUL
6. Remove espaços duplos
7. Remove hífen final

---

**Status:** ✅ Implementado e testado com sucesso

**Arquivo Modificado:** `core/processors.py` (linhas 207-208)

**Teste Criado:** `tests/test_limpeza_guia.py`
