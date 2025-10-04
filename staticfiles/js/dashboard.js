/**
 * Dashboard Interativo - Sistema de Fretamento
 * Funcionalidades avançadas para o dashboard moderno
 */

class DashboardManager {
    constructor() {
        this.initializeComponents();
        this.setupEventListeners();
        this.startRealTimeUpdates();
    }

    /**
     * Inicializa componentes do dashboard
     */
    initializeComponents() {
        this.initializeCounters();
        this.initializeCharts();
        this.initializeNotifications();
        this.initializeSearchFunctionality();
        this.initializeThemeManager();
    }

    /**
     * Configura event listeners
     */
    setupEventListeners() {
        // Auto-hide alerts
        this.setupAutoHideAlerts();
        
        // Smooth scroll para links internos
        this.setupSmoothScroll();
        
        // Loading states para formulários
        this.setupFormLoadingStates();
        
        // Keyboard shortcuts
        this.setupKeyboardShortcuts();
        
        // Lazy loading para imagens
        this.setupLazyLoading();
    }

    /**
     * Inicializa contadores animados
     */
    initializeCounters() {
        const counters = document.querySelectorAll('.stat-number');
        
        const observerOptions = {
            threshold: 0.5,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.animateCounter(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        counters.forEach(counter => {
            const target = parseInt(counter.getAttribute('data-target') || counter.textContent);
            counter.setAttribute('data-target', target);
            counter.textContent = '0';
            observer.observe(counter);
        });
    }

    /**
     * Anima um contador específico
     */
    animateCounter(element, duration = 2000) {
        const target = parseInt(element.getAttribute('data-target'));
        const start = 0;
        const increment = target / (duration / 16);
        let current = start;
        
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(timer);
                element.classList.add('animate-pulse');
                setTimeout(() => element.classList.remove('animate-pulse'), 500);
            }
            element.textContent = Math.floor(current);
        }, 16);
    }

    /**
     * Inicializa gráficos (usando Chart.js se disponível)
     */
    initializeCharts() {
        // Gráfico de eficiência das vans
        this.createVanEfficiencyChart();
        
        // Gráfico de distribuição por tipo
        this.createServiceTypeChart();
        
        // Gráfico de crescimento
        this.createGrowthChart();
    }

    /**
     * Cria gráfico de eficiência das vans
     */
    createVanEfficiencyChart() {
        const canvas = document.getElementById('vanEfficiencyChart');
        if (!canvas || typeof Chart === 'undefined') return;

        const van1 = parseInt(document.querySelector('[data-van1]')?.dataset.van1 || 0);
        const van2 = parseInt(document.querySelector('[data-van2]')?.dataset.van2 || 0);

        new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: ['Van 1', 'Van 2'],
                datasets: [{
                    data: [van1, van2],
                    backgroundColor: [
                        'rgba(102, 126, 234, 0.8)',
                        'rgba(72, 187, 120, 0.8)'
                    ],
                    borderColor: [
                        'rgba(102, 126, 234, 1)',
                        'rgba(72, 187, 120, 1)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    /**
     * Cria gráfico de distribuição por tipo de serviço
     */
    createServiceTypeChart() {
        const canvas = document.getElementById('serviceTypeChart');
        if (!canvas || typeof Chart === 'undefined') return;

        // Extrair dados dos elementos DOM
        const typeData = [];
        const typeLabels = [];
        
        document.querySelectorAll('[data-service-type]').forEach(elem => {
            typeLabels.push(elem.dataset.serviceType);
            typeData.push(parseInt(elem.dataset.count));
        });

        new Chart(canvas, {
            type: 'bar',
            data: {
                labels: typeLabels,
                datasets: [{
                    label: 'Quantidade',
                    data: typeData,
                    backgroundColor: 'rgba(102, 126, 234, 0.6)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    /**
     * Cria gráfico de crescimento
     */
    createGrowthChart() {
        const canvas = document.getElementById('growthChart');
        if (!canvas || typeof Chart === 'undefined') return;

        // Dados simulados para demonstração
        const growthData = [12, 19, 3, 5, 2, 3, 10, 15, 8, 12, 18, 25];
        const months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];

        new Chart(canvas, {
            type: 'line',
            data: {
                labels: months,
                datasets: [{
                    label: 'Serviços por Mês',
                    data: growthData,
                    borderColor: 'rgba(102, 126, 234, 1)',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    /**
     * Sistema de notificações
     */
    initializeNotifications() {
        this.notificationContainer = this.createNotificationContainer();
        this.checkForUpdates();
    }

    /**
     * Cria container para notificações
     */
    createNotificationContainer() {
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 400px;
        `;
        document.body.appendChild(container);
        return container;
    }

    /**
     * Mostra notificação
     */
    showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-${this.getIconForType(type)} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        notification.style.cssText = `
            margin-bottom: 10px;
            animation: slideInRight 0.3s ease;
        `;

        this.notificationContainer.appendChild(notification);

        // Auto-remove após duration
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideOutRight 0.3s ease';
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                }, 300);
            }
        }, duration);
    }

    /**
     * Retorna ícone para tipo de notificação
     */
    getIconForType(type) {
        const icons = {
            'success': 'check-circle',
            'danger': 'exclamation-triangle',
            'warning': 'exclamation-circle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    /**
     * Verifica atualizações em tempo real
     */
    checkForUpdates() {
        setInterval(async () => {
            try {
                // Simular verificação de atualizações
                const response = await fetch('/api/dashboard/updates/');
                if (response.ok) {
                    const data = await response.json();
                    if (data.hasUpdates) {
                        this.showNotification(data.message, 'info');
                    }
                }
            } catch (error) {
                console.log('Verificação de atualizações falhou:', error);
            }
        }, 60000); // Verificar a cada minuto
    }

    /**
     * Funcionalidade de busca avançada
     */
    initializeSearchFunctionality() {
        const searchInput = document.getElementById('global-search');
        if (!searchInput) return;

        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.performSearch(e.target.value);
            }, 300);
        });
    }

    /**
     * Executa busca
     */
    async performSearch(query) {
        if (query.length < 2) return;

        try {
            const response = await fetch(`/api/search/?q=${encodeURIComponent(query)}`);
            if (response.ok) {
                const results = await response.json();
                this.displaySearchResults(results);
            }
        } catch (error) {
            console.error('Erro na busca:', error);
        }
    }

    /**
     * Exibe resultados da busca
     */
    displaySearchResults(results) {
        const container = document.getElementById('search-results');
        if (!container) return;

        container.innerHTML = results.map(result => `
            <div class="search-result-item p-3 border-bottom">
                <h6>${result.title}</h6>
                <p class="text-muted mb-1">${result.description}</p>
                <a href="${result.url}" class="btn btn-sm btn-outline-primary">Ver detalhes</a>
            </div>
        `).join('');
    }

    /**
     * Gerenciador de temas
     */
    initializeThemeManager() {
        this.currentTheme = localStorage.getItem('dashboard-theme') || 'light';
        this.applyTheme(this.currentTheme);
        
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                this.toggleTheme();
            });
        }
    }

    /**
     * Alterna tema
     */
    toggleTheme() {
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(this.currentTheme);
        localStorage.setItem('dashboard-theme', this.currentTheme);
    }

    /**
     * Aplica tema
     */
    applyTheme(theme) {
        document.body.setAttribute('data-theme', theme);
        
        if (theme === 'dark') {
            document.body.style.background = 'linear-gradient(135deg, #1a202c 0%, #2d3748 100%)';
        } else {
            document.body.style.background = 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)';
        }
    }

    /**
     * Auto-hide para alerts
     */
    setupAutoHideAlerts() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            setTimeout(() => {
                if (alert.parentNode) {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }
            }, 5000);
        });
    }

    /**
     * Smooth scroll para links internos
     */
    setupSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    /**
     * Loading states para formulários
     */
    setupFormLoadingStates() {
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', function() {
                const submitBtn = this.querySelector('button[type="submit"], input[type="submit"]');
                if (submitBtn) {
                    const originalText = submitBtn.innerHTML || submitBtn.value;
                    
                    if (submitBtn.tagName === 'BUTTON') {
                        submitBtn.innerHTML = '<span class="loading-spinner me-2"></span>Processando...';
                    } else {
                        submitBtn.value = 'Processando...';
                    }
                    
                    submitBtn.disabled = true;
                    
                    // Restaurar após 5 segundos (fallback)
                    setTimeout(() => {
                        if (submitBtn.tagName === 'BUTTON') {
                            submitBtn.innerHTML = originalText;
                        } else {
                            submitBtn.value = originalText;
                        }
                        submitBtn.disabled = false;
                    }, 5000);
                }
            });
        });
    }

    /**
     * Atalhos de teclado
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+K para busca
            if (e.ctrlKey && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.getElementById('global-search');
                if (searchInput) {
                    searchInput.focus();
                }
            }
            
            // Ctrl+H para home
            if (e.ctrlKey && e.key === 'h') {
                e.preventDefault();
                window.location.href = '/';
            }
            
            // Ctrl+E para escalas
            if (e.ctrlKey && e.key === 'e') {
                e.preventDefault();
                window.location.href = '/escalas/';
            }
        });
    }

    /**
     * Lazy loading para imagens
     */
    setupLazyLoading() {
        const images = document.querySelectorAll('img[data-src]');
        
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('loading');
                    imageObserver.unobserve(img);
                }
            });
        });

        images.forEach(img => imageObserver.observe(img));
    }

    /**
     * Atualiza tempo em tempo real
     */
    startRealTimeUpdates() {
        this.updateTime();
        setInterval(() => {
            this.updateTime();
        }, 60000); // Atualizar a cada minuto
    }

    /**
     * Atualiza exibição do tempo
     */
    updateTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('pt-BR', {
            hour: '2-digit',
            minute: '2-digit'
        });
        const dateString = now.toLocaleDateString('pt-BR', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        
        const timeElement = document.querySelector('.welcome-time');
        if (timeElement) {
            timeElement.innerHTML = `<i class="fas fa-clock me-2"></i>${dateString} - ${timeString}`;
        }
    }

    /**
     * Performance monitor
     */
    initializePerformanceMonitor() {
        // Monitor tempo de carregamento
        window.addEventListener('load', () => {
            const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
            console.log(`Dashboard carregado em ${loadTime}ms`);
            
            if (loadTime > 3000) {
                this.showNotification('Dashboard demorou para carregar. Verifique sua conexão.', 'warning');
            }
        });
    }

    /**
     * Inicializa tooltips e popovers
     */
    initializeBootstrapComponents() {
        // Tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });

        // Popovers
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }
}

/**
 * Utility functions
 */
const DashboardUtils = {
    /**
     * Formata números com separadores
     */
    formatNumber(num) {
        return new Intl.NumberFormat('pt-BR').format(num);
    },

    /**
     * Formata datas
     */
    formatDate(date) {
        return new Intl.DateTimeFormat('pt-BR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        }).format(new Date(date));
    },

    /**
     * Debounce function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Throttle function
     */
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    /**
     * Copia texto para clipboard
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            console.error('Falha ao copiar:', err);
            return false;
        }
    },

    /**
     * Gera cor baseada em string
     */
    stringToColor(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            hash = str.charCodeAt(i) + ((hash << 5) - hash);
        }
        let color = '#';
        for (let i = 0; i < 3; i++) {
            const value = (hash >> (i * 8)) & 0xFF;
            color += ('00' + value.toString(16)).substr(-2);
        }
        return color;
    }
};

// Inicializar dashboard quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    const dashboard = new DashboardManager();
    
    // Expor dashboard globalmente para debug
    window.Dashboard = dashboard;
    window.DashboardUtils = DashboardUtils;
    
    // Adicionar CSS para animações customizadas
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        @keyframes slideOutRight {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
        
        .loading {
            opacity: 0.5;
            filter: blur(2px);
        }
        
        .search-result-item {
            transition: all 0.3s ease;
        }
        
        .search-result-item:hover {
            background: rgba(102, 126, 234, 0.05);
            transform: translateX(5px);
        }
    `;
    document.head.appendChild(style);
    
    console.log('Dashboard inicializado com sucesso! 🚀');
});