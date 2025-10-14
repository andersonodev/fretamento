"""
Middleware para bloquear acesso de dispositivos móveis
"""
from django.http import HttpResponse
from django.template import Template, Context
from django.conf import settings
import re


class MobileBlockMiddleware:
    """
    Middleware que bloqueia o acesso de dispositivos móveis mostrando uma página de aviso
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Padrões para detectar dispositivos móveis
        self.mobile_patterns = [
            r'Mobile', r'Android', r'iPhone', r'iPod', r'BlackBerry',
            r'Windows Phone', r'webOS', r'Opera Mini', r'IEMobile'
        ]
        
        # Compilar padrões regex
        self.mobile_regex = re.compile('|'.join(self.mobile_patterns), re.IGNORECASE)
    
    def __call__(self, request):
        # Verificar se é um dispositivo móvel
        if self._is_mobile_device(request):
            return self._render_mobile_block_page()
        
        response = self.get_response(request)
        return response
    
    def _is_mobile_device(self, request):
        """
        Detecta se o request vem de um dispositivo móvel
        """
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Verificar user agent
        if self.mobile_regex.search(user_agent):
            return True
        
        # Verificar alguns headers específicos que indicam dispositivos móveis
        mobile_headers = [
            'HTTP_X_WAP_PROFILE',
            'HTTP_X_WAP_CLIENTID',
            'HTTP_WAP_CONNECTION',
            'HTTP_PROFILE',
            'HTTP_X_OPERAMINI_PHONE_UA',
            'HTTP_X_NOKIA_GATEWAY_ID',
            'HTTP_X_ORANGE_ID',
            'HTTP_X_VODAFONE_3GPDPCONTEXT',
            'HTTP_X_HUAWEI_USERID',
        ]
        
        for header in mobile_headers:
            if request.META.get(header):
                return True
        
        return False
    
    def _render_mobile_block_page(self):
        """
        Renderiza a página de bloqueio para dispositivos móveis
        """
        template_content = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Versão Mobile em Desenvolvimento</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #1F8CCB 0%, #1a7bb8 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            text-align: center;
            padding: 20px;
        }
        
        .container {
            max-width: 400px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px 30px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .icon {
            font-size: 4rem;
            margin-bottom: 24px;
            opacity: 0.9;
        }
        
        .title {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 16px;
            line-height: 1.3;
        }
        
        .message {
            font-size: 1rem;
            line-height: 1.6;
            opacity: 0.9;
            margin-bottom: 24px;
        }
        
        .desktop-info {
            font-size: 0.875rem;
            opacity: 0.8;
            font-style: italic;
            padding: 16px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .desktop-info i {
            margin-right: 8px;
        }
        
        @media (max-width: 480px) {
            .container {
                padding: 30px 20px;
                margin: 10px;
            }
            
            .icon {
                font-size: 3rem;
            }
            
            .title {
                font-size: 1.25rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">
            <i class="fas fa-mobile-alt"></i>
        </div>
        <h1 class="title">Versão Mobile em Desenvolvimento</h1>
        <p class="message">
            Nosso sistema está otimizado para desktop. A versão mobile ainda está em desenvolvimento para garantir a melhor experiência possível.
        </p>
        <div class="desktop-info">
            <i class="fas fa-desktop"></i>
            Por favor, acesse através de um computador ou tablet em modo desktop.
        </div>
    </div>
</body>
</html>
        """
        
        template = Template(template_content)
        html = template.render(Context({}))
        
        return HttpResponse(html, content_type='text/html', status=200)