/**
 * Sistema Global de Loading - Fretamento Intertouring
 * Gerencia barras de carregamento, modais e estados de loading para botões e formulários
 */

class LoadingManager {
    constructor() {
        this.isLoading = false;
        this.loadingModal = null;
        this.loadingQueue = new Set();
        this.currentProgress = 0;
        this.progressInterval = null;
        this.progressSteps = [];
        this.currentStepIndex = 0;
        
        this.defaultMessages = {
            upload: 'Enviando arquivo...',
            save: 'Salvando dados...',
            delete: 'Removendo item...',
            process: 'Processando...',
            load: 'Carregando...',
            search: 'Buscando...',
            export: 'Exportando dados...',
            import: 'Importando dados...',
            generate: 'Gerando relatório...',
            default: 'Processando...'
        };

        // Etapas de progresso por tipo de operação
        this.progressStagesByType = {
            upload: [
                { progress: 10, message: 'Preparando arquivo...', duration: 500 },
                { progress: 30, message: 'Validando formato...', duration: 800 },
                { progress: 60, message: 'Enviando dados...', duration: 2000 },
                { progress: 85, message: 'Processando informações...', duration: 1000 },
                { progress: 100, message: 'Upload concluído!', duration: 300 }
            ],
            save: [
                { progress: 20, message: 'Validando dados...', duration: 400 },
                { progress: 50, message: 'Salvando no banco...', duration: 800 },
                { progress: 80, message: 'Atualizando índices...', duration: 600 },
                { progress: 100, message: 'Dados salvos!', duration: 300 }
            ],
            delete: [
                { progress: 30, message: 'Verificando dependências...', duration: 500 },
                { progress: 70, message: 'Removendo registros...', duration: 800 },
                { progress: 100, message: 'Item removido!', duration: 300 }
            ],
            search: [
                { progress: 25, message: 'Preparando consulta...', duration: 300 },
                { progress: 70, message: 'Buscando resultados...', duration: 800 },
                { progress: 100, message: 'Busca concluída!', duration: 200 }
            ],
            export: [
                { progress: 15, message: 'Coletando dados...', duration: 600 },
                { progress: 40, message: 'Formatando planilha...', duration: 1000 },
                { progress: 75, message: 'Gerando arquivo...', duration: 1200 },
                { progress: 100, message: 'Exportação concluída!', duration: 300 }
            ],
            import: [
                { progress: 10, message: 'Lendo arquivo...', duration: 500 },
                { progress: 30, message: 'Validando dados...', duration: 800 },
                { progress: 60, message: 'Importando registros...', duration: 1500 },
                { progress: 90, message: 'Finalizando importação...', duration: 500 },
                { progress: 100, message: 'Importação concluída!', duration: 300 }
            ],
            process: [
                { progress: 20, message: 'Iniciando processamento...', duration: 500 },
                { progress: 50, message: 'Executando operações...', duration: 1200 },
                { progress: 80, message: 'Finalizando processo...', duration: 800 },
                { progress: 100, message: 'Processamento concluído!', duration: 300 }
            ],
            generate: [
                { progress: 15, message: 'Coletando informações...', duration: 600 },
                { progress: 45, message: 'Calculando métricas...', duration: 1000 },
                { progress: 75, message: 'Formatando relatório...', duration: 1200 },
                { progress: 100, message: 'Relatório gerado!', duration: 300 }
            ],
            default: [
                { progress: 30, message: 'Processando...', duration: 800 },
                { progress: 70, message: 'Quase terminando...', duration: 1000 },
                { progress: 100, message: 'Concluído!', duration: 300 }
            ]
        };
        
        this.init();
    }

    /**
     * Inicializa o sistema de loading
     */
    init() {
        this.createLoadingModal();
        this.setupFormHandlers();
        this.setupButtonHandlers();
        this.setupAjaxHandlers();
        console.log('🔄 Sistema de Loading inicializado');
    }

    /**
     * Cria o modal de loading principal
     */
    createLoadingModal() {
        if (document.getElementById('globalLoadingModal')) {
            this.loadingModal = document.getElementById('globalLoadingModal');
            return;
        }

        const modalHTML = `
            <div id="globalLoadingModal" class="loading-modal">
                <div class="loading-content">
                    <div class="loading-spinner"></div>
                    <div class="loading-text" id="loadingText">Carregando...</div>
                    <div class="loading-subtitle" id="loadingSubtitle">Por favor, aguarde</div>
                    <div class="loading-bar-container">
                        <div class="loading-bar indeterminate" id="loadingBar"></div>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.loadingModal = document.getElementById('globalLoadingModal');
    }

    /**
     * Mostra o loading com opções personalizadas
     */
    show(options = {}) {
        const config = {
            message: options.message || this.getMessageByType(options.type) || this.defaultMessages.default,
            subtitle: options.subtitle || 'Processando operação...',
            type: options.type || 'default',
            progress: options.progress !== undefined ? options.progress : null,
            timeout: options.timeout || null,
            autoProgress: options.autoProgress !== false, // Por padrão, usar progresso automático
            ...options
        };

        this.isLoading = true;
        this.currentProgress = 0;
        this.currentStepIndex = 0;
        
        // Parar qualquer progresso anterior
        this.stopProgress();
        
        // Atualizar conteúdo do modal
        this.updateModalContent(config);
        
        // Mostrar modal
        if (this.loadingModal) {
            this.loadingModal.classList.add('show');
            document.body.classList.add('no-select', 'cursor-wait');
        }

        // Iniciar progresso automático se habilitado
        if (config.autoProgress && config.progress === null) {
            this.startAutoProgress(config.type);
        } else if (config.progress !== null) {
            this.updateProgress(config.progress, config.message);
        }

        // Auto-hide se timeout especificado
        if (config.timeout) {
            setTimeout(() => {
                this.hide();
            }, config.timeout);
        }

        return config;
    }

    /**
     * Esconde o loading
     */
    hide() {
        this.isLoading = false;
        this.stopProgress();
        
        if (this.loadingModal) {
            this.loadingModal.classList.remove('show');
            document.body.classList.remove('no-select', 'cursor-wait');
        }

        // Limpar todos os botões em loading
        this.clearAllButtonLoading();
    }

    /**
     * Inicia progresso automático baseado no tipo
     */
    startAutoProgress(type = 'default') {
        const stages = this.progressStagesByType[type] || this.progressStagesByType.default;
        this.progressSteps = [...stages];
        this.currentStepIndex = 0;
        this.currentProgress = 0;

        // Iniciar com 0%
        this.updateProgress(0, `Iniciando ${this.getMessageByType(type)}...`);
        
        // Começar sequência de progresso
        this.executeNextProgressStep();
    }

    /**
     * Executa a próxima etapa do progresso
     */
    executeNextProgressStep() {
        if (!this.isLoading || this.currentStepIndex >= this.progressSteps.length) {
            return;
        }

        const step = this.progressSteps[this.currentStepIndex];
        
        this.progressInterval = setTimeout(() => {
            if (this.isLoading) {
                this.updateProgress(step.progress, step.message);
                this.currentProgress = step.progress;
                this.currentStepIndex++;
                
                // Se chegou a 100%, auto-hide após delay
                if (step.progress >= 100) {
                    setTimeout(() => {
                        if (this.isLoading) {
                            this.hide();
                        }
                    }, 800);
                } else {
                    // Continuar para próxima etapa
                    this.executeNextProgressStep();
                }
            }
        }, step.duration);
    }

    /**
     * Para o progresso automático
     */
    stopProgress() {
        if (this.progressInterval) {
            clearTimeout(this.progressInterval);
            this.progressInterval = null;
        }
    }

    /**
     * Atualiza o conteúdo do modal
     */
    updateModalContent(config) {
        const textElement = document.getElementById('loadingText');
        const subtitleElement = document.getElementById('loadingSubtitle');
        const barElement = document.getElementById('loadingBar');

        if (textElement) textElement.textContent = config.message;
        
        if (subtitleElement) {
            if (config.progress !== null && config.progress !== undefined) {
                const percentage = Math.round(Math.min(100, Math.max(0, config.progress)));
                subtitleElement.textContent = `${percentage}% concluído`;
            } else {
                subtitleElement.textContent = '0% concluído';
            }
        }

        if (barElement) {
            // Remover classes anteriores
            barElement.className = 'loading-bar';
            
            if (config.progress !== null && config.progress !== undefined) {
                // Barra determinada
                barElement.style.width = `${config.progress}%`;
            } else {
                // Começar com 0% - o progresso automático cuidará do resto
                barElement.style.width = '0%';
            }

            // Adicionar classe do tipo
            if (config.type !== 'default') {
                barElement.classList.add(`loading-${config.type}`);
            }
        }
    }

    /**
     * Atualiza o progresso da barra
     */
    updateProgress(progress, message = null) {
        const barElement = document.getElementById('loadingBar');
        const textElement = document.getElementById('loadingText');
        const subtitleElement = document.getElementById('loadingSubtitle');

        if (barElement) {
            barElement.classList.remove('indeterminate');
            barElement.style.width = `${Math.min(100, Math.max(0, progress))}%`;
        }

        if (message && textElement) {
            textElement.textContent = message;
        }

        // Atualizar subtitle com porcentagem
        if (subtitleElement) {
            const percentage = Math.round(Math.min(100, Math.max(0, progress)));
            subtitleElement.textContent = `${percentage}% concluído`;
        }
    }

    /**
     * Aplica loading a um botão específico
     */
    setButtonLoading(button, options = {}) {
        if (!button) return;

        const config = {
            text: options.text || 'Carregando...',
            spinner: options.spinner !== false,
            disabled: options.disabled !== false,
            ...options
        };

        // Salvar estado original
        if (!button.dataset.originalContent) {
            button.dataset.originalContent = button.innerHTML;
            button.dataset.originalDisabled = button.disabled;
        }

        // Aplicar loading
        button.classList.add('btn-loading');
        
        if (config.disabled) {
            button.disabled = true;
        }

        if (config.spinner) {
            button.innerHTML = `
                <span class="loading-spinner-small"></span>
                ${config.text}
            `;
        } else {
            button.innerHTML = config.text;
        }

        this.loadingQueue.add(button);
    }

    /**
     * Remove loading de um botão específico
     */
    clearButtonLoading(button) {
        if (!button || !button.dataset.originalContent) return;

        button.classList.remove('btn-loading');
        button.innerHTML = button.dataset.originalContent;
        button.disabled = button.dataset.originalDisabled === 'true';

        // Limpar dados salvos
        delete button.dataset.originalContent;
        delete button.dataset.originalDisabled;

        this.loadingQueue.delete(button);
    }

    /**
     * Remove loading de todos os botões
     */
    clearAllButtonLoading() {
        this.loadingQueue.forEach(button => {
            this.clearButtonLoading(button);
        });
        this.loadingQueue.clear();
    }

    /**
     * Aplica overlay de loading a um formulário
     */
    setFormLoading(form, options = {}) {
        if (!form) return;

        const config = {
            message: options.message || 'Processando formulário...',
            ...options
        };

        // Adicionar classe container se não existir
        if (!form.classList.contains('form-container')) {
            form.classList.add('form-container');
        }

        // Criar overlay se não existir
        let overlay = form.querySelector('.form-loading-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'form-loading-overlay';
            overlay.innerHTML = `
                <div class="text-center">
                    <div class="loading-spinner"></div>
                    <div class="loading-text">${config.message}</div>
                </div>
            `;
            form.appendChild(overlay);
        }

        overlay.classList.add('show');
    }

    /**
     * Remove overlay de loading de um formulário
     */
    clearFormLoading(form) {
        if (!form) return;

        const overlay = form.querySelector('.form-loading-overlay');
        if (overlay) {
            overlay.classList.remove('show');
        }
    }

    /**
     * Configura handlers automáticos para formulários
     */
    setupFormHandlers() {
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (!form.classList.contains('no-auto-loading')) {
                
                // Detectar tipo de formulário
                const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
                const formType = this.detectFormType(form);
                
                // Aplicar loading ao botão submit
                if (submitBtn) {
                    this.setButtonLoading(submitBtn, {
                        text: this.getMessageByType(formType),
                        type: formType
                    });
                }

                // Para uploads de arquivo, mostrar modal
                const fileInputs = form.querySelectorAll('input[type="file"]');
                if (fileInputs.length > 0) {
                    this.show({
                        type: 'upload',
                        message: 'Enviando arquivo...',
                        subtitle: 'Isso pode levar alguns minutos'
                    });
                }
            }
        });
    }

    /**
     * Configura handlers automáticos para botões
     */
    setupButtonHandlers() {
        document.addEventListener('click', (e) => {
            const button = e.target.closest('button, .btn, input[type="submit"]');
            
            if (button && !button.classList.contains('no-auto-loading')) {
                const buttonType = this.detectButtonType(button);
                
                // Aplicar loading apenas para certas ações
                if (this.shouldApplyLoading(button, buttonType)) {
                    this.setButtonLoading(button, {
                        type: buttonType
                    });

                    // Auto-clear após timeout
                    setTimeout(() => {
                        this.clearButtonLoading(button);
                    }, 5000);
                }
            }
        });
    }

    /**
     * Configura handlers para requisições AJAX
     */
    setupAjaxHandlers() {
        // Interceptar fetch
        const originalFetch = window.fetch;
        window.fetch = (...args) => {
            this.show({ type: 'load' });
            
            return originalFetch(...args)
                .then(response => {
                    this.hide();
                    return response;
                })
                .catch(error => {
                    this.hide();
                    throw error;
                });
        };

        // Interceptar XMLHttpRequest
        const originalOpen = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function(...args) {
            this.addEventListener('loadstart', () => {
                window.LoadingManager?.show({ type: 'load' });
            });
            
            this.addEventListener('loadend', () => {
                window.LoadingManager?.hide();
            });
            
            return originalOpen.apply(this, args);
        };
    }

    /**
     * Detecta o tipo de formulário
     */
    detectFormType(form) {
        const action = form.action?.toLowerCase() || '';
        const method = form.method?.toLowerCase() || 'get';
        
        if (form.querySelector('input[type="file"]')) return 'upload';
        if (action.includes('delete')) return 'delete';
        if (action.includes('save') || method === 'post') return 'save';
        if (action.includes('search')) return 'search';
        if (action.includes('export')) return 'export';
        if (action.includes('import')) return 'import';
        
        return 'process';
    }

    /**
     * Detecta o tipo de botão
     */
    detectButtonType(button) {
        const text = button.textContent?.toLowerCase() || '';
        const classes = button.className?.toLowerCase() || '';
        const id = button.id?.toLowerCase() || '';
        
        if (text.includes('upload') || text.includes('enviar')) return 'upload';
        if (text.includes('salvar') || text.includes('save')) return 'save';
        if (text.includes('excluir') || text.includes('delete') || text.includes('remover')) return 'delete';
        if (text.includes('buscar') || text.includes('search')) return 'search';
        if (text.includes('exportar') || text.includes('export')) return 'export';
        if (text.includes('importar') || text.includes('import')) return 'import';
        if (text.includes('gerar') || text.includes('generate')) return 'generate';
        if (text.includes('processar') || text.includes('process')) return 'process';
        
        return 'default';
    }

    /**
     * Verifica se deve aplicar loading ao botão
     */
    shouldApplyLoading(button, type) {
        // Não aplicar em botões de navegação simples
        if (button.tagName === 'A' && !button.onclick) return false;
        
        // Não aplicar em botões de dropdown/modal toggle
        if (button.dataset.bsToggle) return false;
        
        // Aplicar em botões de ação
        return ['upload', 'save', 'delete', 'process', 'search', 'export', 'import', 'generate'].includes(type);
    }

    /**
     * Retorna mensagem baseada no tipo
     */
    getMessageByType(type) {
        return this.defaultMessages[type] || this.defaultMessages.default;
    }

    /**
     * API pública para usar em templates
     */
    static show(options) {
        return window.LoadingManager?.show(options);
    }

    static hide() {
        return window.LoadingManager?.hide();
    }

    static updateProgress(progress, message) {
        return window.LoadingManager?.updateProgress(progress, message);
    }

    static setButtonLoading(button, options) {
        return window.LoadingManager?.setButtonLoading(button, options);
    }

    static clearButtonLoading(button) {
        return window.LoadingManager?.clearButtonLoading(button);
    }

    static setFormLoading(form, options) {
        return window.LoadingManager?.setFormLoading(form, options);
    }

    static clearFormLoading(form) {
        return window.LoadingManager?.clearFormLoading(form);
    }
}

/**
 * Funções utilitárias globais para fácil uso
 */
window.showLoading = (options) => LoadingManager.show(options);
window.hideLoading = () => LoadingManager.hide();
window.updateLoadingProgress = (progress, message) => LoadingManager.updateProgress(progress, message);

/**
 * Inicializar quando DOM estiver pronto
 */
document.addEventListener('DOMContentLoaded', function() {
    window.LoadingManager = new LoadingManager();
    
    console.log('✅ Sistema de Loading Global ativo!');
    
    // Adicionar métodos ao objeto global para compatibilidade
    window.Loading = {
        show: LoadingManager.show,
        hide: LoadingManager.hide,
        updateProgress: LoadingManager.updateProgress,
        setButtonLoading: LoadingManager.setButtonLoading,
        clearButtonLoading: LoadingManager.clearButtonLoading,
        setFormLoading: LoadingManager.setFormLoading,
        clearFormLoading: LoadingManager.clearFormLoading
    };
});

/**
 * Exemplos de uso:
 * 
 * // Mostrar loading simples
 * showLoading();
 * 
 * // Loading com opções
 * showLoading({
 *     message: 'Enviando dados...',
 *     subtitle: 'Isso pode demorar um pouco',
 *     type: 'upload'
 * });
 * 
 * // Loading com progresso
 * showLoading({ progress: 50 });
 * updateLoadingProgress(75, 'Quase terminando...');
 * 
 * // Loading em botão específico
 * const btn = document.getElementById('meuBotao');
 * Loading.setButtonLoading(btn, { text: 'Salvando...' });
 * 
 * // Esconder loading
 * hideLoading();
 */