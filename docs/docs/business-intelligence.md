# 📊 Business Intelligence e Analytics

Este documento detalha o sistema de análise e relatórios de negócio.

## 📈 Dashboard Executivo

```mermaid
graph TB
    subgraph "KPIs Principais"
        KPI1[Ocupação Média<br/>85% Van1 | 78% Van2]
        KPI2[Receita Diária<br/>R$ 12.500]
        KPI3[Margem Líquida<br/>32%]
        KPI4[Escalas Aprovadas<br/>94%]
    end
    
    subgraph "Métricas Operacionais"
        OP1[Serviços/Dia<br/>45 avg]
        OP2[PAX/Van<br/>28 avg]
        OP3[Tempo Médio<br/>6.5h operação]
        OP4[Eficiência Rota<br/>92%]
    end
    
    subgraph "Análise Financeira"
        FIN1[Receita por PAX<br/>R$ 145]
        FIN2[Custo Operacional<br/>R$ 8.200]
        FIN3[ROI Diário<br/>52%]
        FIN4[Projeção Mensal<br/>R$ 375.000]
    end
    
    subgraph "Tendências"
        TREND1[Crescimento Semanal<br/>+12%]
        TREND2[Sazonalidade<br/>Pico: Quinta-Sexta]
        TREND3[Cliente Top<br/>Hotelbeds 35%]
        TREND4[Rota Mais Rentável<br/>Aeroportos]
    end
    
    KPI1 --> OP1
    KPI2 --> FIN1
    KPI3 --> FIN2
    KPI4 --> OP4
    
    OP2 --> FIN1
    OP3 --> FIN2
    
    FIN3 --> TREND1
    FIN4 --> TREND2
    
    classDef kpi fill:#e8f5e8
    classDef operational fill:#e3f2fd
    classDef financial fill:#fff3e0
    classDef trend fill:#fce4ec
    
    class KPI1,KPI2,KPI3,KPI4 kpi
    class OP1,OP2,OP3,OP4 operational
    class FIN1,FIN2,FIN3,FIN4 financial
    class TREND1,TREND2,TREND3,TREND4 trend
```

## 🔍 Análise de Lucratividade por Serviço

```mermaid
flowchart TD
    START([Dados da escala]) --> EXTRACT[Extrair dados<br/>por serviço]
    
    EXTRACT --> CALC_REVENUE[Calcular receita<br/>Preço × Quantidade]
    
    CALC_REVENUE --> CALC_DIRECT_COST[Custos diretos<br/>- Combustível<br/>- Motorista<br/>- Pedágio]
    
    CALC_DIRECT_COST --> CALC_INDIRECT_COST[Custos indiretos<br/>- Manutenção<br/>- Seguro<br/>- Depreciação]
    
    CALC_INDIRECT_COST --> NET_MARGIN[Margem líquida<br/>(Receita - Custos) / Receita]
    
    NET_MARGIN --> EFFICIENCY[Eficiência<br/>Receita / PAX / Hora]
    
    EFFICIENCY --> SCORE_SERVICE[Score do serviço<br/>Margem × Eficiência × PAX]
    
    SCORE_SERVICE --> CATEGORIZE[Categorizar serviços<br/>🟢 Alto valor<br/>🟡 Médio valor<br/>🔴 Baixo valor]
    
    CATEGORIZE --> INSIGHTS[Gerar insights<br/>- Top 10 mais rentáveis<br/>- Serviços críticos<br/>- Oportunidades de melhoria]
    
    INSIGHTS --> RECOMMENDATIONS[Recomendações<br/>- Ajustes de preço<br/>- Otimizações de rota<br/>- Negociações com clientes]
    
    RECOMMENDATIONS --> EXPORT_REPORT[Exportar relatório<br/>Excel + PDF]
    
    EXPORT_REPORT --> END([Análise concluída])
    
    classDef input fill:#e3f2fd
    classDef calculation fill:#e8f5e8
    classDef analysis fill:#fff3e0
    classDef output fill:#fce4ec
    
    class START,EXTRACT input
    class CALC_REVENUE,CALC_DIRECT_COST,CALC_INDIRECT_COST,NET_MARGIN,EFFICIENCY,SCORE_SERVICE calculation
    class CATEGORIZE,INSIGHTS,RECOMMENDATIONS analysis
    class EXPORT_REPORT,END output
```

## 📊 Análise de Tendências Temporais

```mermaid
gantt
    title Análise Temporal de Ocupação - Semana Tipo
    dateFormat X
    axisFormat %d
    
    section Segunda
    Van 1 Ocupação     :active, mon1, 0, 8
    Van 2 Ocupação     :        mon2, 0, 6
    
    section Terça
    Van 1 Ocupação     :active, tue1, 0, 9
    Van 2 Ocupação     :        tue2, 0, 7
    
    section Quarta
    Van 1 Ocupação     :active, wed1, 0, 10
    Van 2 Ocupação     :        wed2, 0, 8
    
    section Quinta
    Van 1 Ocupação     :crit, thu1, 0, 12
    Van 2 Ocupação     :crit, thu2, 0, 11
    
    section Sexta
    Van 1 Ocupação     :crit, fri1, 0, 14
    Van 2 Ocupação     :crit, fri2, 0, 13
    
    section Sábado
    Van 1 Ocupação     :active, sat1, 0, 7
    Van 2 Ocupação     :        sat2, 0, 5
    
    section Domingo
    Van 1 Ocupação     :        sun1, 0, 4
    Van 2 Ocupação     :        sun2, 0, 3
```

## 🎯 Segmentação de Clientes

```mermaid
pie title Distribuição de Receita por Cliente
    "Hotelbeds" : 35
    "Holiday" : 22
    "CVC" : 18
    "Decolar" : 12
    "Outros" : 13
```

```mermaid
graph TB
    subgraph "Clientes Premium (>R$ 50k/mês)"
        PREM1[Hotelbeds<br/>R$ 87.500<br/>35% do volume]
        PREM2[Holiday<br/>R$ 55.000<br/>22% do volume]
    end
    
    subgraph "Clientes Gold (R$ 20k-50k/mês)"
        GOLD1[CVC<br/>R$ 45.000<br/>18% do volume]
        GOLD2[Decolar<br/>R$ 30.000<br/>12% do volume]
    end
    
    subgraph "Clientes Silver (<R$ 20k/mês)"
        SILVER1[Agências Locais<br/>R$ 32.500<br/>13% do volume]
    end
    
    subgraph "Características"
        CHAR1[Premium: Reservas antecipadas<br/>Volumes garantidos<br/>Pagamento pontual]
        CHAR2[Gold: Sazonalidade média<br/>Negociação de preços<br/>Bom relacionamento]
        CHAR3[Silver: Demanda irregular<br/>Preço sensível<br/>Pagamento variável]
    end
    
    PREM1 --> CHAR1
    PREM2 --> CHAR1
    GOLD1 --> CHAR2
    GOLD2 --> CHAR2
    SILVER1 --> CHAR3
    
    classDef premium fill:#ffd700
    classDef gold fill:#c0c0c0
    classDef silver fill:#cd7f32
    classDef characteristics fill:#e8f5e8
    
    class PREM1,PREM2 premium
    class GOLD1,GOLD2 gold
    class SILVER1 silver
    class CHAR1,CHAR2,CHAR3 characteristics
```

## 📈 Análise de Correlações

```mermaid
graph LR
    subgraph "Variáveis Independentes"
        VAR1[Dia da Semana]
        VAR2[Horário]
        VAR3[Cliente]
        VAR4[Destino]
        VAR5[PAX]
        VAR6[Antecedência]
    end
    
    subgraph "Correlações"
        CORR1[VAR1 → RECEITA<br/>r = 0.73]
        CORR2[VAR2 → OCUPAÇÃO<br/>r = 0.65]
        CORR3[VAR3 → MARGEM<br/>r = 0.81]
        CORR4[VAR4 → TEMPO<br/>r = 0.59]
        CORR5[VAR5 → VEÍCULO<br/>r = 0.92]
        CORR6[VAR6 → PREÇO<br/>r = -0.34]
    end
    
    subgraph "Variáveis Dependentes"
        DEP1[Receita Diária]
        DEP2[Taxa Ocupação]
        DEP3[Margem Líquida]
        DEP4[Tempo Operação]
        DEP5[Tipo Veículo]
        DEP6[Preço Unitário]
    end
    
    VAR1 --> CORR1 --> DEP1
    VAR2 --> CORR2 --> DEP2
    VAR3 --> CORR3 --> DEP3
    VAR4 --> CORR4 --> DEP4
    VAR5 --> CORR5 --> DEP5
    VAR6 --> CORR6 --> DEP6
    
    classDef variable fill:#e3f2fd
    classDef correlation fill:#e8f5e8
    classDef dependent fill:#fff3e0
    
    class VAR1,VAR2,VAR3,VAR4,VAR5,VAR6 variable
    class CORR1,CORR2,CORR3,CORR4,CORR5,CORR6 correlation
    class DEP1,DEP2,DEP3,DEP4,DEP5,DEP6 dependent
```

## 🎲 Modelos Preditivos

```mermaid
flowchart TD
    START([Dados históricos]) --> PREP[Preparação dos dados<br/>- Limpeza<br/>- Normalização<br/>- Feature engineering]
    
    PREP --> SPLIT[Divisão treino/teste<br/>80% / 20%]
    
    SPLIT --> MODELS[Treinar modelos<br/>- Linear Regression<br/>- Random Forest<br/>- XGBoost]
    
    MODELS --> VALIDATE[Validação cruzada<br/>k-fold (k=5)]
    
    VALIDATE --> METRICS[Métricas<br/>- MAE<br/>- RMSE<br/>- R²]
    
    METRICS --> SELECT[Selecionar melhor modelo<br/>Random Forest: R² = 0.87]
    
    SELECT --> DEPLOY[Deploy em produção<br/>API de predição]
    
    DEPLOY --> PREDICT[Predições<br/>- Demanda diária<br/>- Receita estimada<br/>- Ocupação prevista]
    
    PREDICT --> FEEDBACK[Feedback loop<br/>Atualizar modelo<br/>com novos dados]
    
    FEEDBACK --> MODELS
    
    classDef process fill:#e3f2fd
    classDef model fill:#e8f5e8
    classDef prediction fill:#fff3e0
    classDef feedback fill:#fce4ec
    
    class START,PREP,SPLIT,VALIDATE,METRICS,SELECT,DEPLOY process
    class MODELS model
    class PREDICT prediction
    class FEEDBACK feedback
```

## 📊 Relatórios Automatizados

```mermaid
sequenceDiagram
    participant CRON as Cron Job
    participant REPORT as Report Generator
    participant DB as Database
    participant CALC as Calculator
    participant EMAIL as Email Service
    participant STORAGE as File Storage
    
    Note over CRON,STORAGE: Relatório Diário (6:00 AM)
    
    CRON->>REPORT: Trigger daily report
    REPORT->>DB: Query yesterday data
    DB-->>REPORT: Escala data
    
    REPORT->>CALC: Calculate KPIs
    CALC->>CALC: Process metrics
    CALC-->>REPORT: Calculated results
    
    REPORT->>REPORT: Generate Excel
    REPORT->>REPORT: Generate PDF summary
    
    REPORT->>STORAGE: Save files
    STORAGE-->>REPORT: URLs
    
    REPORT->>EMAIL: Send to managers
    EMAIL-->>REPORT: Delivery confirmation
    
    Note over CRON,STORAGE: Relatório Semanal (Segunda 8:00 AM)
    
    CRON->>REPORT: Trigger weekly report
    REPORT->>DB: Query week data
    DB-->>REPORT: Aggregated data
    
    REPORT->>CALC: Calculate trends
    CALC->>CALC: Week-over-week analysis
    CALC-->>REPORT: Trend analysis
    
    REPORT->>REPORT: Generate dashboard
    REPORT->>EMAIL: Send executive summary
    
    Note over CRON,STORAGE: Relatório Mensal (1º dia 9:00 AM)
    
    CRON->>REPORT: Trigger monthly report
    REPORT->>DB: Query month data
    REPORT->>CALC: Full P&L analysis
    CALC-->>REPORT: Financial report
    
    REPORT->>EMAIL: Send to stakeholders
```

## 🎯 Sistema de Alertas Inteligentes

```mermaid
graph TB
    subgraph "Monitoramento"
        MON1[Ocupação < 70%<br/>⚠️ Alert Amarelo]
        MON2[Margem < 25%<br/>🚨 Alert Vermelho]
        MON3[Atraso > 30min<br/>⚠️ Alert Amarelo]
        MON4[Cancelamentos > 10%<br/>🚨 Alert Vermelho]
    end
    
    subgraph "Processamento"
        PROC1[Avaliar criticidade<br/>- Impacto no negócio<br/>- Urgência da ação<br/>- Tendência histórica]
        PROC2[Gerar recomendações<br/>- Ações corretivas<br/>- Responsáveis<br/>- Prazos]
    end
    
    subgraph "Notificações"
        NOT1[SMS Urgente<br/>Gerência]
        NOT2[Email Detalhado<br/>Operação]
        NOT3[WhatsApp<br/>Motoristas]
        NOT4[Dashboard<br/>Tempo Real]
    end
    
    subgraph "Ações Automáticas"
        AUTO1[Realocar serviços<br/>automaticamente]
        AUTO2[Ajustar preços<br/>dinamicamente]
        AUTO3[Contatar clientes<br/>proativamente]
        AUTO4[Escalar para<br/>supervisão]
    end
    
    MON1 --> PROC1
    MON2 --> PROC1
    MON3 --> PROC1
    MON4 --> PROC1
    
    PROC1 --> PROC2
    
    PROC2 --> NOT1
    PROC2 --> NOT2
    PROC2 --> NOT3
    PROC2 --> NOT4
    
    PROC2 --> AUTO1
    PROC2 --> AUTO2
    PROC2 --> AUTO3
    PROC2 --> AUTO4
    
    classDef monitoring fill:#e3f2fd
    classDef processing fill:#e8f5e8
    classDef notification fill:#fff3e0
    classDef automation fill:#fce4ec
    
    class MON1,MON2,MON3,MON4 monitoring
    class PROC1,PROC2 processing
    class NOT1,NOT2,NOT3,NOT4 notification
    class AUTO1,AUTO2,AUTO3,AUTO4 automation
```

## 📈 Benchmarking Competitivo

```mermaid
graph TB
    subgraph "Nossos KPIs"
        OUR1[Ocupação: 85%]
        OUR2[Margem: 32%]
        OUR3[Satisfação: 4.2/5]
        OUR4[On-time: 94%]
    end
    
    subgraph "Mercado"
        MKT1[Ocupação Média: 78%<br/>📈 +7% vs mercado]
        MKT2[Margem Média: 28%<br/>📈 +4% vs mercado]
        MKT3[Satisfação Média: 3.9/5<br/>📈 +0.3 vs mercado]
        MKT4[On-time Médio: 89%<br/>📈 +5% vs mercado]
    end
    
    subgraph "Líderes de Mercado"
        LEAD1[Líder Ocupação: 92%<br/>📊 Gap: -7%]
        LEAD2[Líder Margem: 35%<br/>📊 Gap: -3%]
        LEAD3[Líder Satisfação: 4.5/5<br/>📊 Gap: -0.3]
        LEAD4[Líder On-time: 96%<br/>📊 Gap: -2%]
    end
    
    subgraph "Oportunidades"
        OPP1[Melhorar rotas<br/>para aumentar ocupação]
        OPP2[Otimizar custos<br/>para aumentar margem]
        OPP3[Treinamento equipe<br/>para satisfação]
        OPP4[Sistema GPS<br/>para pontualidade]
    end
    
    OUR1 --> MKT1 --> LEAD1 --> OPP1
    OUR2 --> MKT2 --> LEAD2 --> OPP2
    OUR3 --> MKT3 --> LEAD3 --> OPP3
    OUR4 --> MKT4 --> LEAD4 --> OPP4
    
    classDef our fill:#e8f5e8
    classDef market fill:#e3f2fd
    classDef leaders fill:#fff3e0
    classDef opportunities fill:#fce4ec
    
    class OUR1,OUR2,OUR3,OUR4 our
    class MKT1,MKT2,MKT3,MKT4 market
    class LEAD1,LEAD2,LEAD3,LEAD4 leaders
    class OPP1,OPP2,OPP3,OPP4 opportunities
```

## 🔮 Cenários de Projeção

```mermaid
graph TB
    subgraph "Cenário Conservador (+5% aa)"
        CONS1[Receita Atual: R$ 375k/mês]
        CONS2[Crescimento: +5% ao ano]
        CONS3[Projeção 12 meses: R$ 394k/mês]
        CONS4[Margem mantida: 32%]
    end
    
    subgraph "Cenário Moderado (+15% aa)"
        MOD1[Novos clientes: +2]
        MOD2[Crescimento: +15% ao ano]
        MOD3[Projeção 12 meses: R$ 431k/mês]
        MOD4[Margem melhorada: 35%]
    end
    
    subgraph "Cenário Otimista (+25% aa)"
        OPT1[Expansão frota: +1 van]
        OPT2[Crescimento: +25% ao ano]
        OPT3[Projeção 12 meses: R$ 469k/mês]
        OPT4[Margem otimizada: 38%]
    end
    
    subgraph "Investimentos Necessários"
        INV1[Conservador: R$ 50k<br/>Manutenção atual]
        INV2[Moderado: R$ 150k<br/>Marketing + tecnologia]
        INV3[Otimista: R$ 350k<br/>Van nova + equipe]
    end
    
    CONS1 --> CONS2 --> CONS3 --> CONS4
    MOD1 --> MOD2 --> MOD3 --> MOD4
    OPT1 --> OPT2 --> OPT3 --> OPT4
    
    CONS4 --> INV1
    MOD4 --> INV2
    OPT4 --> INV3
    
    classDef conservative fill:#e3f2fd
    classDef moderate fill:#e8f5e8
    classDef optimistic fill:#fff3e0
    classDef investment fill:#fce4ec
    
    class CONS1,CONS2,CONS3,CONS4 conservative
    class MOD1,MOD2,MOD3,MOD4 moderate
    class OPT1,OPT2,OPT3,OPT4 optimistic
    class INV1,INV2,INV3 investment
```

---

## 💡 Insights Estratégicos

### 🎯 Principais Descobertas
1. **Quinta e sexta** são os dias mais lucrativos (+45% vs média)
2. **Hotelbeds** representa 35% da receita mas 45% da margem
3. **Horário 14h-16h** tem menor ocupação mas maior margem
4. **Aeroportos** são 23% mais rentáveis que city tours

### 📊 Recomendações Imediatas
1. **Focar em clientes premium** para maximizar margem
2. **Otimizar rotas do meio-dia** para aumentar ocupação
3. **Implementar preços dinâmicos** nos horários de pico
4. **Desenvolver parcerias** com hotéis de luxo

### 🚀 Oportunidades de Crescimento
1. **Expansão para Búzios** nos fins de semana
2. **Parcerias com cruzeiros** para transfer portuário
3. **Serviços corporativos** para empresas locais
4. **App para clientes finais** para reservas diretas

---

Este sistema de BI fornece uma visão 360° do negócio, permitindo:
- **Decisões baseadas em dados** reais
- **Identificação proativa** de oportunidades
- **Otimização contínua** da operação
- **Crescimento sustentável** e rentável