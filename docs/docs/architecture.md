# 🏗️ Arquitetura do Sistema

Este documento descreve a arquitetura completa do Sistema de Fretamento Intertouring.

## 📊 Visão Geral da Arquitetura

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[Interface Web<br/>Bootstrap 5 + JS]
        KB[Sistema Kanban<br/>Drag & Drop]
        FT[Filtros e Busca<br/>Tempo Real]
    end
    
    subgraph "Application Layer"
        DJV[Django Views<br/>Class-Based Views]
        API[APIs REST<br/>JSON Responses]
        MW[Middleware<br/>Auth + Security]
    end
    
    subgraph "Business Logic Layer"
        OPT[Algoritmo de<br/>Otimização]
        PRICE[Sistema de<br/>Precificação]
        GROUP[Agrupamento<br/>Inteligente]
        EXPORT[Exportação<br/>Excel]
    end
    
    subgraph "Data Layer"
        ORM[Django ORM<br/>Models]
        DB[(SQLite/PostgreSQL<br/>Database)]
        CACHE[Cache Layer<br/>Redis/LocMem]
    end
    
    subgraph "External Services"
        EXCEL[Planilhas Excel<br/>Import/Export]
        PDF[Relatórios PDF<br/>Future]
        EMAIL[Notificações<br/>Email]
    end
    
    UI --> DJV
    KB --> API
    FT --> DJV
    
    DJV --> OPT
    API --> PRICE
    MW --> GROUP
    
    OPT --> ORM
    PRICE --> ORM
    GROUP --> ORM
    EXPORT --> EXCEL
    
    ORM --> DB
    ORM --> CACHE
    
    DJV --> EMAIL
    API --> PDF
    
    classDef frontend fill:#e1f5fe
    classDef application fill:#f3e5f5
    classDef business fill:#e8f5e8
    classDef data fill:#fff3e0
    classDef external fill:#fce4ec
    
    class UI,KB,FT frontend
    class DJV,API,MW application
    class OPT,PRICE,GROUP,EXPORT business
    class ORM,DB,CACHE data
    class EXCEL,PDF,EMAIL external
```

## 🔄 Fluxo de Dados Principal

```mermaid
sequenceDiagram
    participant U as Usuário
    participant UI as Interface Web
    participant V as Django Views
    participant S as Services Layer
    participant M as Models
    participant DB as Database
    
    U->>UI: Acessa Sistema
    UI->>V: HTTP Request
    V->>S: Chama Serviço
    S->>M: Query ORM
    M->>DB: SQL Query
    DB-->>M: Resultados
    M-->>S: Objetos Python
    S-->>V: Dados Processados
    V-->>UI: Template + Context
    UI-->>U: HTML Response
    
    Note over U,DB: Fluxo padrão de requisição
    
    U->>UI: Ação no Kanban
    UI->>V: AJAX Request
    V->>S: Otimizar Escala
    S->>M: Update Models
    M->>DB: Transações
    DB-->>M: Confirmação
    M-->>S: Status
    S-->>V: JSON Response
    V-->>UI: AJAX Response
    UI-->>U: Update Interface
    
    Note over U,DB: Fluxo de otimização em tempo real
```

## 🗄️ Modelo de Dados (ERD)

```mermaid
erDiagram
    User ||--o{ Escala : "aprova"
    User ||--o{ LogEscala : "registra"
    
    Escala ||--o{ AlocacaoVan : "contém"
    Escala ||--o{ GrupoServico : "possui"
    Escala ||--o{ LogEscala : "gera"
    
    Servico ||--o{ AlocacaoVan : "é alocado"
    
    GrupoServico ||--o{ ServicoGrupo : "agrupa"
    AlocacaoVan ||--|| ServicoGrupo : "relaciona"
    
    User {
        int id PK
        string username
        string email
        datetime created_at
    }
    
    Escala {
        int id PK
        date data UK
        string etapa
        string status
        date data_origem
        int aprovada_por FK
        datetime data_aprovacao
        text observacoes_aprovacao
        datetime created_at
        datetime updated_at
    }
    
    Servico {
        int id PK
        string cliente
        string servico
        int pax
        time horario
        string local_pickup
        decimal numero_venda
        datetime created_at
        datetime updated_at
    }
    
    AlocacaoVan {
        int id PK
        int escala_id FK
        int servico_id FK
        string van
        int ordem
        boolean automatica
        decimal preco_calculado
        string veiculo_recomendado
        decimal lucratividade
        json detalhes_precificacao
        string status_alocacao
    }
    
    GrupoServico {
        int id PK
        int escala_id FK
        string van
        int ordem
        string cliente_principal
        text servico_principal
        string local_pickup_principal
        int total_pax
        decimal total_valor
        text numeros_venda
        datetime created_at
        datetime updated_at
    }
    
    ServicoGrupo {
        int id PK
        int grupo_id FK
        int alocacao_id FK
    }
    
    LogEscala {
        int id PK
        int escala_id FK
        string acao
        int usuario_id FK
        string ip_address
        text descricao
        json dados_antes
        json dados_depois
        datetime timestamp
    }
```

## 🧠 Algoritmo de Otimização

```mermaid
flowchart TD
    START([Iniciar Otimização]) --> LOAD[Carregar Serviços da Escala]
    
    LOAD --> CALC_PRICES[Calcular Preços<br/>Busca Fuzzy]
    CALC_PRICES --> GROUP[Agrupar Serviços<br/>Por Similaridade]
    
    GROUP --> SORT[Ordenar por<br/>Prioridade + PAX]
    
    SORT --> INIT_VANS[Inicializar<br/>Van1 e Van2 Vazias]
    
    INIT_VANS --> LOOP_START{Há serviços<br/>não alocados?}
    
    LOOP_START -->|Sim| GET_NEXT[Pegar próximo<br/>serviço da lista]
    
    GET_NEXT --> CHECK_V1{Van1 pode<br/>acomodar?}
    
    CHECK_V1 -->|Sim| CALC_V1[Calcular score<br/>Van1 + serviço]
    CHECK_V1 -->|Não| CHECK_V2{Van2 pode<br/>acomodar?}
    
    CALC_V1 --> CHECK_V2
    CHECK_V2 -->|Sim| CALC_V2[Calcular score<br/>Van2 + serviço]
    CHECK_V2 -->|Não| CREATE_NEW[Criar novo grupo<br/>ou realocar]
    
    CALC_V2 --> COMPARE{Score V1 ><br/>Score V2?}
    
    COMPARE -->|V1 melhor| ALLOC_V1[Alocar para Van1]
    COMPARE -->|V2 melhor| ALLOC_V2[Alocar para Van2]
    COMPARE -->|Empate| ALLOC_LESS[Alocar para van<br/>com menos PAX]
    
    ALLOC_V1 --> UPDATE_GROUPS[Atualizar grupos<br/>e totais]
    ALLOC_V2 --> UPDATE_GROUPS
    ALLOC_LESS --> UPDATE_GROUPS
    CREATE_NEW --> UPDATE_GROUPS
    
    UPDATE_GROUPS --> LOOP_START
    
    LOOP_START -->|Não| OPTIMIZE_ROUTES[Otimizar rotas<br/>dentro das vans]
    
    OPTIMIZE_ROUTES --> CALC_TOTALS[Calcular totais<br/>finais]
    
    CALC_TOTALS --> SAVE[Salvar resultados<br/>no banco]
    
    SAVE --> LOG[Registrar log<br/>de otimização]
    
    LOG --> END([Fim])
    
    classDef process fill:#e3f2fd
    classDef decision fill:#fff3e0
    classDef action fill:#e8f5e8
    classDef terminal fill:#fce4ec
    
    class LOAD,CALC_PRICES,GROUP,SORT,INIT_VANS,GET_NEXT,CALC_V1,CALC_V2,ALLOC_V1,ALLOC_V2,ALLOC_LESS,CREATE_NEW,UPDATE_GROUPS,OPTIMIZE_ROUTES,CALC_TOTALS,SAVE,LOG process
    class LOOP_START,CHECK_V1,CHECK_V2,COMPARE decision
    class START,END terminal
```

## 💰 Sistema de Precificação

```mermaid
flowchart TD
    START([Iniciar Precificação]) --> GET_SERVICE[Obter dados<br/>do serviço]
    
    GET_SERVICE --> EXTRACT[Extrair nome<br/>do serviço]
    
    EXTRACT --> SEARCH_JW[Buscar no<br/>Tarifário JW]
    
    SEARCH_JW --> FUZZY_JW[Aplicar busca fuzzy<br/>threshold: 0.4]
    
    FUZZY_JW --> FOUND_JW{Match encontrado<br/>no JW?}
    
    FOUND_JW -->|Sim| CALC_JW[Calcular preço<br/>baseado no veículo]
    FOUND_JW -->|Não| SEARCH_MOT[Buscar no<br/>Tarifário Motoristas]
    
    CALC_JW --> VALIDATE_JW[Validar preço<br/>e veículo JW]
    
    SEARCH_MOT --> FUZZY_MOT[Aplicar busca fuzzy<br/>threshold: 0.25]
    
    FUZZY_MOT --> FOUND_MOT{Match encontrado<br/>nos Motoristas?}
    
    FOUND_MOT -->|Sim| CALC_MOT[Usar preço base<br/>dos motoristas]
    FOUND_MOT -->|Não| DEFAULT_PRICE[Calcular preço<br/>padrão por PAX]
    
    CALC_MOT --> VALIDATE_MOT[Validar preço<br/>dos motoristas]
    
    DEFAULT_PRICE --> VEHICLE_PAX[Determinar veículo<br/>baseado no PAX]
    
    VEHICLE_PAX --> VALIDATE_DEFAULT[Validar preço<br/>padrão]
    
    VALIDATE_JW --> STORE_DETAILS[Armazenar detalhes<br/>da precificação]
    VALIDATE_MOT --> STORE_DETAILS
    VALIDATE_DEFAULT --> STORE_DETAILS
    
    STORE_DETAILS --> CALC_PROFIT[Calcular<br/>lucratividade]
    
    CALC_PROFIT --> SAVE_DB[Salvar no<br/>banco de dados]
    
    SAVE_DB --> LOG_CALC[Log do<br/>cálculo]
    
    LOG_CALC --> END([Fim])
    
    classDef process fill:#e3f2fd
    classDef decision fill:#fff3e0
    classDef calculation fill:#e8f5e8
    classDef terminal fill:#fce4ec
    
    class GET_SERVICE,EXTRACT,SEARCH_JW,FUZZY_JW,SEARCH_MOT,FUZZY_MOT,VEHICLE_PAX,STORE_DETAILS,SAVE_DB,LOG_CALC process
    class FOUND_JW,FOUND_MOT decision
    class CALC_JW,CALC_MOT,DEFAULT_PRICE,VALIDATE_JW,VALIDATE_MOT,VALIDATE_DEFAULT,CALC_PROFIT calculation
    class START,END terminal
```

## 🎯 Interface Kanban - Componentes

```mermaid
graph TB
    subgraph "Kanban Board"
        FILTERS[Filtros Avançados<br/>Cliente, PAX, Valor, Status]
        
        subgraph "Van 1 Column"
            V1H[Header Van 1<br/>Total PAX | Total Valor]
            V1G1[Grupo 1<br/>Cliente A | 15 PAX]
            V1G2[Grupo 2<br/>Cliente B | 8 PAX]
            V1G3[Grupo 3<br/>Cliente C | 12 PAX]
        end
        
        subgraph "Van 2 Column"
            V2H[Header Van 2<br/>Total PAX | Total Valor]
            V2G1[Grupo 1<br/>Cliente D | 20 PAX]
            V2G2[Grupo 2<br/>Cliente E | 6 PAX]
        end
        
        subgraph "Não Alocados"
            NAH[Header Não Alocados<br/>Serviços pendentes]
            NA1[Serviço 1<br/>Cliente F | 4 PAX]
            NA2[Serviço 2<br/>Cliente G | 25 PAX]
        end
    end
    
    subgraph "Controls"
        OPT[Botão Otimizar<br/>Automático]
        SAVE[Salvar Alterações<br/>Manual]
        EXPORT[Exportar Excel<br/>Formatado]
        APPROVE[Aprovar Escala<br/>Workflow]
    end
    
    subgraph "Modals"
        EDIT[Modal Edição<br/>Serviço Individual]
        CONFIRM[Modal Confirmação<br/>Ações Críticas]
        DETAIL[Modal Detalhes<br/>Precificação]
    end
    
    FILTERS --> V1H
    FILTERS --> V2H
    FILTERS --> NAH
    
    V1G1 -.->|Drag & Drop| V2G1
    V1G2 -.->|Drag & Drop| NA1
    NA1 -.->|Drag & Drop| V1G3
    
    OPT --> V1G1
    OPT --> V2G1
    SAVE --> V1G1
    EXPORT --> V1G1
    
    V1G1 --> EDIT
    OPT --> CONFIRM
    V1G1 --> DETAIL
    
    classDef column fill:#e3f2fd
    classDef group fill:#e8f5e8
    classDef control fill:#fff3e0
    classDef modal fill:#fce4ec
    
    class V1H,V2H,NAH column
    class V1G1,V1G2,V1G3,V2G1,V2G2,NA1,NA2 group
    class FILTERS,OPT,SAVE,EXPORT,APPROVE control
    class EDIT,CONFIRM,DETAIL modal
```

## 🔄 Estados e Transições da Escala

```mermaid
stateDiagram-v2
    [*] --> ESTRUTURA: Criar Nova Escala
    
    ESTRUTURA --> DADOS_PUXADOS: Importar Planilha
    ESTRUTURA --> [*]: Excluir Escala
    
    DADOS_PUXADOS --> OTIMIZADA: Executar Otimização
    DADOS_PUXADOS --> ESTRUTURA: Reset para Estrutura
    DADOS_PUXADOS --> [*]: Excluir Escala
    
    OTIMIZADA --> DADOS_PUXADOS: Reverter Otimização
    OTIMIZADA --> FORMATADA: Aplicar Formatação
    OTIMIZADA --> [*]: Excluir Escala
    
    FORMATADA --> OTIMIZADA: Reverter Formatação
    FORMATADA --> APROVADA: Aprovar Escala
    FORMATADA --> REJEITADA: Rejeitar Escala
    FORMATADA --> [*]: Excluir Escala
    
    APROVADA --> EXPORTADA: Exportar Excel
    APROVADA --> REJEITADA: Reverter Aprovação
    
    REJEITADA --> FORMATADA: Corrigir e Reenviar
    REJEITADA --> [*]: Excluir Escala
    
    EXPORTADA --> [*]: Arquivar
    
    state ESTRUTURA {
        [*] --> EmptySchedule
        EmptySchedule --> ReadyForData
    }
    
    state DADOS_PUXADOS {
        [*] --> ProcessingData
        ProcessingData --> DataLoaded
        DataLoaded --> ReadyForOptimization
    }
    
    state OTIMIZADA {
        [*] --> RunningOptimization
        RunningOptimization --> OptimizationComplete
        OptimizationComplete --> ReadyForFormatting
    }
    
    state FORMATADA {
        [*] --> ApplyingFormat
        ApplyingFormat --> FormattingComplete
        FormattingComplete --> ReadyForApproval
    }
```

## 📱 Casos de Uso do Sistema

```mermaid
graph LR
    subgraph "Atores"
        OP[Operador]
        MGR[Gerente]
        SYS[Sistema]
    end
    
    subgraph "Casos de Uso Principais"
        UC1[Criar Nova Escala]
        UC2[Importar Planilha]
        UC3[Otimizar Alocação]
        UC4[Editar Manualmente]
        UC5[Aprovar Escala]
        UC6[Exportar Excel]
        UC7[Gerar Relatórios]
        UC8[Gerenciar Usuários]
    end
    
    subgraph "Casos de Uso Secundários"
        UC9[Filtrar Serviços]
        UC10[Buscar Preços]
        UC11[Agrupar Serviços]
        UC12[Calcular Lucratividade]
        UC13[Registrar Logs]
        UC14[Notificar Usuários]
    end
    
    OP --> UC1
    OP --> UC2
    OP --> UC3
    OP --> UC4
    OP --> UC6
    OP --> UC9
    
    MGR --> UC5
    MGR --> UC7
    MGR --> UC8
    
    SYS --> UC10
    SYS --> UC11
    SYS --> UC12
    SYS --> UC13
    SYS --> UC14
    
    UC1 --> UC2
    UC2 --> UC3
    UC3 --> UC4
    UC4 --> UC5
    UC5 --> UC6
    
    UC3 --> UC10
    UC3 --> UC11
    UC10 --> UC12
    
    UC1 --> UC13
    UC3 --> UC13
    UC5 --> UC13
    
    UC5 --> UC14
    
    classDef actor fill:#e3f2fd
    classDef primary fill:#e8f5e8
    classDef secondary fill:#fff3e0
    
    class OP,MGR,SYS actor
    class UC1,UC2,UC3,UC4,UC5,UC6,UC7,UC8 primary
    class UC9,UC10,UC11,UC12,UC13,UC14 secondary
```

## 🚀 Arquitetura de Deploy

```mermaid
graph TB
    subgraph "Development"
        DEV_CODE[Código Local<br/>VS Code + Git]
        DEV_DB[(SQLite<br/>Desenvolvimento)]
        DEV_SERVER[Django Dev Server<br/>127.0.0.1:8000]
    end
    
    subgraph "Version Control"
        GITHUB[GitHub Repository<br/>Source Code]
        ACTIONS[GitHub Actions<br/>CI/CD Pipeline]
    end
    
    subgraph "Vercel Deploy"
        VERCEL_BUILD[Vercel Build<br/>Serverless Functions]
        VERCEL_APP[Vercel App<br/>Global CDN]
        VERCEL_DB[(SQLite Temp<br/>Per Request)]
    end
    
    subgraph "Docker Deploy"
        DOCKER_BUILD[Docker Build<br/>Multi-stage]
        
        subgraph "Production Stack"
            NGINX[Nginx<br/>Reverse Proxy]
            GUNICORN[Gunicorn<br/>WSGI Server]
            DJANGO_APP[Django App<br/>Production]
            POSTGRES[(PostgreSQL<br/>Database)]
            REDIS[(Redis<br/>Cache)]
        end
    end
    
    subgraph "External Services"
        DNS[DNS Provider<br/>Domain Management]
        CDN[CDN<br/>Static Assets]
        MONITOR[Monitoring<br/>Logs & Metrics]
    end
    
    DEV_CODE --> GITHUB
    GITHUB --> ACTIONS
    
    ACTIONS --> VERCEL_BUILD
    ACTIONS --> DOCKER_BUILD
    
    VERCEL_BUILD --> VERCEL_APP
    VERCEL_APP --> VERCEL_DB
    
    DOCKER_BUILD --> NGINX
    NGINX --> GUNICORN
    GUNICORN --> DJANGO_APP
    DJANGO_APP --> POSTGRES
    DJANGO_APP --> REDIS
    
    VERCEL_APP --> DNS
    NGINX --> DNS
    VERCEL_APP --> CDN
    NGINX --> CDN
    DJANGO_APP --> MONITOR
    VERCEL_APP --> MONITOR
    
    classDef dev fill:#e3f2fd
    classDef vcs fill:#e8f5e8
    classDef vercel fill:#fff3e0
    classDef docker fill:#fce4ec
    classDef external fill:#f3e5f5
    
    class DEV_CODE,DEV_DB,DEV_SERVER dev
    class GITHUB,ACTIONS vcs
    class VERCEL_BUILD,VERCEL_APP,VERCEL_DB vercel
    class DOCKER_BUILD,NGINX,GUNICORN,DJANGO_APP,POSTGRES,REDIS docker
    class DNS,CDN,MONITOR external
```

## 🔒 Arquitetura de Segurança

```mermaid
graph TB
    subgraph "Frontend Security"
        HTTPS[HTTPS/TLS<br/>Encryption]
        CSP[Content Security Policy<br/>XSS Protection]
        CSRF[CSRF Tokens<br/>Form Protection]
    end
    
    subgraph "Application Security"
        AUTH[Django Authentication<br/>Session Management]
        PERM[Permissions System<br/>Role-Based Access]
        MW[Security Middleware<br/>Headers & Validation]
    end
    
    subgraph "Data Security"
        ORM[ORM Protection<br/>SQL Injection Prevention]
        VALID[Input Validation<br/>Data Sanitization]
        ENCRYPT[Password Hashing<br/>PBKDF2]
    end
    
    subgraph "Infrastructure Security"
        FW[Firewall Rules<br/>Network Security]
        BACKUP[Automated Backups<br/>Data Recovery]
        LOG[Security Logging<br/>Audit Trail]
    end
    
    subgraph "Monitoring & Response"
        ALERT[Security Alerts<br/>Real-time Monitoring]
        INCIDENT[Incident Response<br/>Security Procedures]
        UPDATE[Security Updates<br/>Patch Management]
    end
    
    HTTPS --> AUTH
    CSP --> PERM
    CSRF --> MW
    
    AUTH --> ORM
    PERM --> VALID
    MW --> ENCRYPT
    
    ORM --> FW
    VALID --> BACKUP
    ENCRYPT --> LOG
    
    FW --> ALERT
    BACKUP --> INCIDENT
    LOG --> UPDATE
    
    ALERT --> INCIDENT
    INCIDENT --> UPDATE
    
    classDef frontend fill:#e3f2fd
    classDef application fill:#e8f5e8
    classDef data fill:#fff3e0
    classDef infrastructure fill:#fce4ec
    classDef monitoring fill:#f3e5f5
    
    class HTTPS,CSP,CSRF frontend
    class AUTH,PERM,MW application
    class ORM,VALID,ENCRYPT data
    class FW,BACKUP,LOG infrastructure
    class ALERT,INCIDENT,UPDATE monitoring
```

## 📊 Arquitetura de Performance

```mermaid
graph TB
    subgraph "Frontend Optimization"
        MINIFY[CSS/JS Minification<br/>Asset Optimization]
        LAZY[Lazy Loading<br/>Images & Components]
        CACHE_CLIENT[Browser Caching<br/>Service Workers]
    end
    
    subgraph "Application Optimization"
        SELECT[Select Related<br/>Query Optimization]
        PREFETCH[Prefetch Related<br/>N+1 Prevention]
        PAGINATION[Pagination<br/>Large Datasets]
    end
    
    subgraph "Database Optimization"
        INDEXES[Database Indexes<br/>Query Performance]
        POOL[Connection Pooling<br/>Resource Management]
        ANALYZE[Query Analysis<br/>Performance Monitoring]
    end
    
    subgraph "Caching Strategy"
        REDIS_CACHE[Redis Cache<br/>Session & Data]
        LOCMEM[LocMem Cache<br/>Development]
        TEMPLATE_CACHE[Template Caching<br/>Rendered Views]
    end
    
    subgraph "Infrastructure Performance"
        CDN_DIST[CDN Distribution<br/>Global Edge Servers]
        LOAD_BAL[Load Balancing<br/>Traffic Distribution]
        SCALE[Auto Scaling<br/>Resource Allocation]
    end
    
    MINIFY --> SELECT
    LAZY --> PREFETCH
    CACHE_CLIENT --> PAGINATION
    
    SELECT --> INDEXES
    PREFETCH --> POOL
    PAGINATION --> ANALYZE
    
    INDEXES --> REDIS_CACHE
    POOL --> LOCMEM
    ANALYZE --> TEMPLATE_CACHE
    
    REDIS_CACHE --> CDN_DIST
    LOCMEM --> LOAD_BAL
    TEMPLATE_CACHE --> SCALE
    
    classDef frontend fill:#e3f2fd
    classDef application fill:#e8f5e8
    classDef database fill:#fff3e0
    classDef caching fill:#fce4ec
    classDef infrastructure fill:#f3e5f5
    
    class MINIFY,LAZY,CACHE_CLIENT frontend
    class SELECT,PREFETCH,PAGINATION application
    class INDEXES,POOL,ANALYZE database
    class REDIS_CACHE,LOCMEM,TEMPLATE_CACHE caching
    class CDN_DIST,LOAD_BAL,SCALE infrastructure
```

---

## 🏛️ Padrões Arquiteturais Utilizados

### 1. **Model-View-Template (MVT)**
- **Models**: Representação dos dados e lógica de negócio
- **Views**: Controladores que processam requisições
- **Templates**: Apresentação e interface do usuário

### 2. **Repository Pattern**
- Abstração da camada de dados através do Django ORM
- Facilita testes e manutenção
- Isolamento da lógica de persistência

### 3. **Service Layer Pattern**
- Lógica de negócio centralizada em classes de serviço
- Reutilização de código entre views
- Facilita testes unitários

### 4. **Observer Pattern**
- Sistema de logs automáticos
- Notificações de mudanças de estado
- Auditoria de ações do usuário

### 5. **Strategy Pattern**
- Algoritmos de precificação intercambiáveis
- Múltiplos tarifários configuráveis
- Flexibilidade na lógica de cálculo

---

## 📈 Métricas de Performance

### Targets de Performance
- **Response Time**: < 200ms para views principais
- **Database Queries**: < 10 queries por view
- **Memory Usage**: < 512MB por processo
- **Cache Hit Rate**: > 80% para dados frequentes

### Monitoramento
- Django Debug Toolbar em desenvolvimento
- Logs estruturados em produção
- Métricas de banco de dados
- Análise de queries N+1

---

Esta arquitetura foi projetada para ser:
- **Escalável**: Suporta crescimento de usuários e dados
- **Manutenível**: Código limpo e bem documentado
- **Performante**: Otimizada para velocidade e eficiência
- **Segura**: Proteções multicamadas implementadas
- **Flexível**: Permite adaptações e extensões futuras