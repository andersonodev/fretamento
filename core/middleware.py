"""
Middleware de Segurança Customizado para Fretamento Intertouring
"""
import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from django.urls import reverse
from django.contrib.auth import logout

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware para adicionar headers de segurança personalizados
    """
    
    def process_response(self, request, response):
        # Content Security Policy
        if not settings.DEBUG:
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' cdn.jsdelivr.net stackpath.bootstrapcdn.com",
                "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net stackpath.bootstrapcdn.com fonts.googleapis.com",
                "font-src 'self' fonts.gstatic.com",
                "img-src 'self' data: https:",
                "connect-src 'self'",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'"
            ]
            response['Content-Security-Policy'] = '; '.join(csp_directives)
        
        # Outros headers de segurança
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Feature Policy (deprecated but still supported)
        response['Feature-Policy'] = "geolocation 'none'; microphone 'none'; camera 'none'"
        
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """
    Middleware simples de rate limiting por IP
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_counts = {}
        self.window_start = time.time()
        self.window_size = 60  # 1 minuto
        self.max_requests = 100  # Máximo de requests por minuto
        super().__init__(get_response)
    
    def process_request(self, request):
        if settings.DEBUG:
            return None  # Não aplicar rate limiting em desenvolvimento
        
        current_time = time.time()
        
        # Reset window se necessário
        if current_time - self.window_start > self.window_size:
            self.request_counts = {}
            self.window_start = current_time
        
        # Obter IP do cliente
        ip = self.get_client_ip(request)
        
        # Contar requests
        self.request_counts[ip] = self.request_counts.get(ip, 0) + 1
        
        # Verificar limite
        if self.request_counts[ip] > self.max_requests:
            logger.warning(f'Rate limit exceeded for IP: {ip}')
            from django.http import HttpResponse
            return HttpResponse(
                'Rate limit exceeded. Please wait before making more requests.',
                status=429
            )
        
        return None
    
    def get_client_ip(self, request):
        """Obter IP real do cliente considerando proxies"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SessionTimeoutMiddleware(MiddlewareMixin):
    """
    Middleware para timeout automático de sessão por inatividade
    """
    
    def process_request(self, request):
        if not request.user.is_authenticated:
            return None
        
        # Verificar último acesso
        last_activity = request.session.get('last_activity')
        current_time = time.time()
        
        # Timeout de 30 minutos (1800 segundos)
        timeout_seconds = getattr(settings, 'SESSION_TIMEOUT', 1800)
        
        if last_activity:
            if current_time - last_activity > timeout_seconds:
                # Fazer logout por timeout
                logout(request)
                logger.info(f'Session timeout for user: {request.user.username}')
                from django.contrib import messages
                messages.warning(request, 'Sua sessão expirou por inatividade. Faça login novamente.')
                return HttpResponsePermanentRedirect(reverse('authentication:login'))
        
        # Atualizar último acesso
        request.session['last_activity'] = current_time
        return None


class AuditLogMiddleware(MiddlewareMixin):
    """
    Middleware para log de auditoria de ações importantes
    """
    
    SENSITIVE_PATHS = [
        '/admin/',
        '/escalas/',
        '/core/',
    ]
    
    def process_request(self, request):
        # Log apenas para paths sensíveis e usuários autenticados
        if request.user.is_authenticated and any(request.path.startswith(path) for path in self.SENSITIVE_PATHS):
            
            # Obter informações do request
            ip = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
            method = request.method
            path = request.path
            
            # Log da ação
            logger.info(
                f'AUDIT: User {request.user.username} ({request.user.id}) '
                f'accessed {method} {path} from IP {ip} '
                f'[User-Agent: {user_agent[:100]}]'
            )
            
            # Armazenar informações na sessão para logging posterior
            request.session['audit_info'] = {
                'ip': ip,
                'user_agent': user_agent[:200],
                'timestamp': time.time()
            }
        
        return None
    
    def get_client_ip(self, request):
        """Obter IP real do cliente considerando proxies"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityValidationMiddleware(MiddlewareMixin):
    """
    Middleware para validações adicionais de segurança
    """
    
    def process_request(self, request):
        # Validar tamanho do request
        content_length = request.META.get('CONTENT_LENGTH')
        if content_length:
            try:
                content_length = int(content_length)
                max_size = getattr(settings, 'MAX_REQUEST_SIZE', 10 * 1024 * 1024)  # 10MB
                if content_length > max_size:
                    logger.warning(f'Request too large: {content_length} bytes from IP {self.get_client_ip(request)}')
                    from django.http import HttpResponse
                    return HttpResponse('Request too large', status=413)
            except ValueError:
                pass
        
        # Validar User-Agent (bloquear bots maliciosos conhecidos)
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        malicious_agents = [
            'sqlmap', 'nikto', 'dirb', 'dirbuster', 'nessus', 
            'openvas', 'w3af', 'skipfish', 'zap'
        ]
        
        if any(agent in user_agent for agent in malicious_agents):
            logger.warning(f'Malicious User-Agent detected: {user_agent} from IP {self.get_client_ip(request)}')
            from django.http import HttpResponse
            return HttpResponse('Access denied', status=403)
        
        return None
    
    def get_client_ip(self, request):
        """Obter IP real do cliente considerando proxies"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip