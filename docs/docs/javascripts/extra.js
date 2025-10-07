// Scripts customizados para a documentação

document.addEventListener('DOMContentLoaded', function() {
    // Inicialização de funcionalidades
    initializeTooltips();
    initializeCopyButtons();
    initializeSearchEnhancements();
    initializeDiagramInteractions();
    initializeAnimations();
    initializeThemeToggle();
});

// Função para inicializar tooltips
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            const tooltip = document.createElement('div');
            tooltip.className = 'custom-tooltip';
            tooltip.textContent = this.getAttribute('data-tooltip');
            tooltip.style.cssText = `
                position: absolute;
                background: #333;
                color: white;
                padding: 0.5rem;
                border-radius: 4px;
                font-size: 0.8rem;
                z-index: 1000;
                pointer-events: none;
                white-space: nowrap;
                opacity: 0;
                transition: opacity 0.2s ease;
            `;
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.left = rect.left + 'px';
            tooltip.style.top = (rect.bottom + 5) + 'px';
            
            requestAnimationFrame(() => {
                tooltip.style.opacity = '1';
            });
            
            this.addEventListener('mouseleave', function() {
                if (tooltip.parentNode) {
                    tooltip.style.opacity = '0';
                    setTimeout(() => {
                        if (tooltip.parentNode) {
                            tooltip.parentNode.removeChild(tooltip);
                        }
                    }, 200);
                }
            });
        });
    });
}

// Função para adicionar botões de cópia nos blocos de código
function initializeCopyButtons() {
    const codeBlocks = document.querySelectorAll('pre code');
    codeBlocks.forEach(codeBlock => {
        const pre = codeBlock.parentElement;
        if (pre.querySelector('.copy-button')) return; // Evitar duplicação
        
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-button';
        copyButton.innerHTML = '📋';
        copyButton.title = 'Copiar código';
        copyButton.style.cssText = `
            position: absolute;
            top: 0.5rem;
            right: 0.5rem;
            background: rgba(255, 255, 255, 0.8);
            border: none;
            border-radius: 4px;
            padding: 0.25rem 0.5rem;
            cursor: pointer;
            font-size: 0.8rem;
            transition: background-color 0.2s ease;
        `;
        
        copyButton.addEventListener('click', function() {
            navigator.clipboard.writeText(codeBlock.textContent).then(() => {
                copyButton.innerHTML = '✅';
                copyButton.style.background = 'rgba(76, 175, 80, 0.8)';
                setTimeout(() => {
                    copyButton.innerHTML = '📋';
                    copyButton.style.background = 'rgba(255, 255, 255, 0.8)';
                }, 2000);
            });
        });
        
        pre.style.position = 'relative';
        pre.appendChild(copyButton);
    });
}

// Melhorias na busca
function initializeSearchEnhancements() {
    const searchInput = document.querySelector('.md-search__input');
    if (searchInput) {
        // Adicionar placeholder dinâmico
        const placeholders = [
            'Buscar documentação...',
            'Pesquisar arquitetura...',
            'Encontrar algoritmos...',
            'Buscar business intelligence...'
        ];
        
        let placeholderIndex = 0;
        setInterval(() => {
            searchInput.placeholder = placeholders[placeholderIndex];
            placeholderIndex = (placeholderIndex + 1) % placeholders.length;
        }, 3000);
        
        // Adicionar histórico de busca
        const searchHistory = JSON.parse(localStorage.getItem('searchHistory') || '[]');
        
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && this.value.trim()) {
                const searchTerm = this.value.trim();
                if (!searchHistory.includes(searchTerm)) {
                    searchHistory.unshift(searchTerm);
                    if (searchHistory.length > 10) {
                        searchHistory.pop();
                    }
                    localStorage.setItem('searchHistory', JSON.stringify(searchHistory));
                }
            }
        });
    }
}

// Interações com diagramas Mermaid
function initializeDiagramInteractions() {
    const diagrams = document.querySelectorAll('.mermaid');
    diagrams.forEach(diagram => {
        // Adicionar zoom nos diagramas
        diagram.style.cursor = 'zoom-in';
        diagram.addEventListener('click', function() {
            const modal = document.createElement('div');
            modal.className = 'diagram-modal';
            modal.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.8);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 10000;
                cursor: zoom-out;
            `;
            
            const clonedDiagram = this.cloneNode(true);
            clonedDiagram.style.cssText = `
                max-width: 90%;
                max-height: 90%;
                background: white;
                border-radius: 8px;
                padding: 1rem;
                cursor: zoom-out;
            `;
            
            modal.appendChild(clonedDiagram);
            document.body.appendChild(modal);
            
            modal.addEventListener('click', function() {
                document.body.removeChild(modal);
            });
            
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape' && modal.parentNode) {
                    document.body.removeChild(modal);
                }
            });
        });
    });
}

// Animações suaves
function initializeAnimations() {
    // Animação de aparição para elementos
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Aplicar animação em cards e seções importantes
    const animatedElements = document.querySelectorAll('.feature-card, .admonition, .mermaid');
    animatedElements.forEach(element => {
        element.style.cssText += `
            opacity: 0;
            transform: translateY(20px);
            transition: opacity 0.6s ease, transform 0.6s ease;
        `;
        observer.observe(element);
    });
}

// Toggle de tema customizado
function initializeThemeToggle() {
    // Verificar se já existe um toggle de tema
    if (document.querySelector('.custom-theme-toggle')) return;
    
    const themeToggle = document.createElement('button');
    themeToggle.className = 'custom-theme-toggle';
    themeToggle.innerHTML = '🌓';
    themeToggle.title = 'Alternar tema';
    themeToggle.style.cssText = `
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        width: 3rem;
        height: 3rem;
        border-radius: 50%;
        border: none;
        background: #1976d2;
        color: white;
        font-size: 1.2rem;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3);
        z-index: 1000;
        transition: all 0.3s ease;
    `;
    
    themeToggle.addEventListener('click', function() {
        const body = document.body;
        const isDark = body.getAttribute('data-md-color-scheme') === 'slate';
        
        if (isDark) {
            body.setAttribute('data-md-color-scheme', 'default');
            this.innerHTML = '🌙';
            localStorage.setItem('theme', 'light');
        } else {
            body.setAttribute('data-md-color-scheme', 'slate');
            this.innerHTML = '☀️';
            localStorage.setItem('theme', 'dark');
        }
    });
    
    themeToggle.addEventListener('mouseenter', function() {
        this.style.transform = 'scale(1.1)';
    });
    
    themeToggle.addEventListener('mouseleave', function() {
        this.style.transform = 'scale(1)';
    });
    
    document.body.appendChild(themeToggle);
    
    // Restaurar tema salvo
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.setAttribute('data-md-color-scheme', 'slate');
        themeToggle.innerHTML = '☀️';
    }
}

// Funcionalidade de estatísticas de página
function trackPageStats() {
    const pageStats = JSON.parse(localStorage.getItem('pageStats') || '{}');
    const currentPage = window.location.pathname;
    
    if (!pageStats[currentPage]) {
        pageStats[currentPage] = {
            visits: 0,
            timeSpent: 0,
            lastVisit: null
        };
    }
    
    pageStats[currentPage].visits++;
    pageStats[currentPage].lastVisit = new Date().toISOString();
    
    const startTime = Date.now();
    
    window.addEventListener('beforeunload', function() {
        const timeSpent = Date.now() - startTime;
        pageStats[currentPage].timeSpent += timeSpent;
        localStorage.setItem('pageStats', JSON.stringify(pageStats));
    });
    
    localStorage.setItem('pageStats', JSON.stringify(pageStats));
}

// Funcionalidade de favoritos
function initializeFavorites() {
    const favorites = JSON.parse(localStorage.getItem('favorites') || '[]');
    
    // Adicionar botão de favorito nas páginas
    const title = document.querySelector('h1');
    if (title) {
        const favoriteButton = document.createElement('button');
        favoriteButton.className = 'favorite-button';
        favoriteButton.innerHTML = favorites.includes(window.location.pathname) ? '⭐' : '☆';
        favoriteButton.title = 'Adicionar aos favoritos';
        favoriteButton.style.cssText = `
            margin-left: 1rem;
            background: none;
            border: none;
            font-size: 1.2rem;
            cursor: pointer;
            color: #1976d2;
        `;
        
        favoriteButton.addEventListener('click', function() {
            const currentPage = window.location.pathname;
            const pageTitle = title.textContent;
            
            if (favorites.some(fav => fav.path === currentPage)) {
                const index = favorites.findIndex(fav => fav.path === currentPage);
                favorites.splice(index, 1);
                this.innerHTML = '☆';
            } else {
                favorites.push({
                    path: currentPage,
                    title: pageTitle,
                    addedAt: new Date().toISOString()
                });
                this.innerHTML = '⭐';
            }
            
            localStorage.setItem('favorites', JSON.stringify(favorites));
        });
        
        title.appendChild(favoriteButton);
    }
}

// Inicializar funcionalidades adicionais
document.addEventListener('DOMContentLoaded', function() {
    trackPageStats();
    initializeFavorites();
});

// Função para smooth scroll personalizado
function smoothScroll(target, duration = 800) {
    const targetPosition = target.offsetTop - 100; // Offset para header fixo
    const startPosition = window.pageYOffset;
    const distance = targetPosition - startPosition;
    let startTime = null;
    
    function animation(currentTime) {
        if (startTime === null) startTime = currentTime;
        const timeElapsed = currentTime - startTime;
        const run = ease(timeElapsed, startPosition, distance, duration);
        window.scrollTo(0, run);
        if (timeElapsed < duration) requestAnimationFrame(animation);
    }
    
    function ease(t, b, c, d) {
        t /= d / 2;
        if (t < 1) return c / 2 * t * t + b;
        t--;
        return -c / 2 * (t * (t - 2) - 1) + b;
    }
    
    requestAnimationFrame(animation);
}

// Aplicar smooth scroll em links internos
document.addEventListener('click', function(e) {
    if (e.target.tagName === 'A' && e.target.getAttribute('href').startsWith('#')) {
        e.preventDefault();
        const target = document.querySelector(e.target.getAttribute('href'));
        if (target) {
            smoothScroll(target);
        }
    }
});

// Console log para debug (remover em produção)
console.log('📚 Documentação do Sistema de Fretamento carregada com sucesso!');
console.log('✨ Funcionalidades ativas: tooltips, copy buttons, search enhancements, diagram interactions, animations, theme toggle');