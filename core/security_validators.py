"""
Validadores de Segurança para Fretamento Intertouring
"""
import re
import html
import logging
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)


class SecurityValidator:
    """
    Classe principal para validações de segurança
    """
    
    # Padrões para detectar tentativas de injeção
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(--|\/\*|\*\/)",
        r"(\bxp_cmdshell\b)",
        r"(\bsp_executesql\b)",
    ]
    
    XSS_PATTERNS = [
        r"<script[\s\S]*?>[\s\S]*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[\s\S]*?>",
        r"<object[\s\S]*?>",
        r"<embed[\s\S]*?>",
        r"<form[\s\S]*?>",
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e\\",
    ]
    
    @classmethod
    def validate_input(cls, value, field_name="input", max_length=None):
        """
        Validação geral de entrada
        """
        if not isinstance(value, str):
            value = str(value)
        
        # Verificar comprimento
        if max_length and len(value) > max_length:
            raise ValidationError(
                _(f'{field_name} muito longo. Máximo {max_length} caracteres.')
            )
        
        # Verificar padrões maliciosos
        cls._check_sql_injection(value, field_name)
        cls._check_xss(value, field_name)
        cls._check_path_traversal(value, field_name)
        
        return value
    
    @classmethod
    def _check_sql_injection(cls, value, field_name):
        """Verificar tentativas de SQL injection"""
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f'SQL injection attempt detected in {field_name}: {value[:100]}')
                raise ValidationError(
                    _(f'Conteúdo inválido detectado em {field_name}.')
                )
    
    @classmethod
    def _check_xss(cls, value, field_name):
        """Verificar tentativas de XSS"""
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f'XSS attempt detected in {field_name}: {value[:100]}')
                raise ValidationError(
                    _(f'Conteúdo inválido detectado em {field_name}.')
                )
    
    @classmethod
    def _check_path_traversal(cls, value, field_name):
        """Verificar tentativas de path traversal"""
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f'Path traversal attempt detected in {field_name}: {value[:100]}')
                raise ValidationError(
                    _(f'Caminho inválido detectado em {field_name}.')
                )
    
    @classmethod
    def sanitize_html(cls, value):
        """
        Sanitizar HTML removendo tags perigosas
        """
        if not isinstance(value, str):
            value = str(value)
        
        # Escapar HTML
        value = html.escape(value)
        
        # Remover caracteres de controle
        value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)
        
        return value
    
    @classmethod
    def validate_decimal(cls, value, field_name="valor", max_digits=10, decimal_places=2):
        """
        Validar valores decimais de forma segura
        """
        if value is None:
            return None
        
        try:
            # Converter para string e limpar
            if not isinstance(value, str):
                value = str(value)
            
            value = value.strip()
            
            # Remover caracteres não numéricos exceto . e ,
            value = re.sub(r'[^\d.,-]', '', value)
            
            # Converter vírgula para ponto
            value = value.replace(',', '.')
            
            # Validar formato
            if not re.match(r'^\d*\.?\d*$', value):
                raise ValidationError(
                    _(f'{field_name} deve conter apenas números.')
                )
            
            # Converter para Decimal
            decimal_value = Decimal(value)
            
            # Verificar limites
            max_value = Decimal('9' * (max_digits - decimal_places) + '.' + '9' * decimal_places)
            if decimal_value > max_value:
                raise ValidationError(
                    _(f'{field_name} muito grande. Máximo {max_value}.')
                )
            
            if decimal_value < 0:
                raise ValidationError(
                    _(f'{field_name} não pode ser negativo.')
                )
            
            return decimal_value
            
        except (InvalidOperation, ValueError) as e:
            logger.warning(f'Invalid decimal value for {field_name}: {value}')
            raise ValidationError(
                _(f'{field_name} deve ser um número válido.')
            )
    
    @classmethod
    def validate_integer(cls, value, field_name="número", min_value=None, max_value=None):
        """
        Validar valores inteiros de forma segura
        """
        if value is None:
            return None
        
        try:
            # Converter para string e limpar
            if not isinstance(value, str):
                value = str(value)
            
            value = value.strip()
            
            # Remover caracteres não numéricos
            value = re.sub(r'[^\d-]', '', value)
            
            # Converter para int
            int_value = int(value)
            
            # Verificar limites
            if min_value is not None and int_value < min_value:
                raise ValidationError(
                    _(f'{field_name} deve ser maior ou igual a {min_value}.')
                )
            
            if max_value is not None and int_value > max_value:
                raise ValidationError(
                    _(f'{field_name} deve ser menor ou igual a {max_value}.')
                )
            
            return int_value
            
        except ValueError as e:
            logger.warning(f'Invalid integer value for {field_name}: {value}')
            raise ValidationError(
                _(f'{field_name} deve ser um número inteiro válido.')
            )
    
    @classmethod
    def validate_date_string(cls, value, field_name="data"):
        """
        Validar strings de data
        """
        if not value:
            return None
        
        # Sanitizar entrada
        value = cls.validate_input(value, field_name, max_length=20)
        
        # Padrões aceitos
        date_patterns = [
            r'^\d{2}[-/]\d{2}[-/]\d{4}$',  # DD-MM-YYYY ou DD/MM/YYYY
            r'^\d{4}-\d{2}-\d{2}$',        # YYYY-MM-DD
        ]
        
        if not any(re.match(pattern, value) for pattern in date_patterns):
            raise ValidationError(
                _(f'{field_name} deve estar no formato DD/MM/YYYY ou YYYY-MM-DD.')
            )
        
        return value
    
    @classmethod
    def validate_filename(cls, filename):
        """
        Validar nomes de arquivo para upload
        """
        if not filename:
            raise ValidationError(_('Nome do arquivo é obrigatório.'))
        
        # Verificar caracteres perigosos
        dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in dangerous_chars:
            if char in filename:
                raise ValidationError(
                    _(f'Nome do arquivo contém caracteres inválidos: {char}')
                )
        
        # Verificar extensões permitidas
        allowed_extensions = ['.xlsx', '.xls', '.csv', '.pdf', '.png', '.jpg', '.jpeg']
        if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
            raise ValidationError(
                _(f'Tipo de arquivo não permitido. Extensões permitidas: {", ".join(allowed_extensions)}')
            )
        
        # Verificar tamanho do nome
        if len(filename) > 255:
            raise ValidationError(_('Nome do arquivo muito longo.'))
        
        return filename


class FormSecurityMixin:
    """
    Mixin para adicionar validações de segurança em forms Django
    """
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Aplicar validações de segurança em todos os campos de texto
        for field_name, value in cleaned_data.items():
            if isinstance(value, str) and value:
                try:
                    # Validar entrada
                    SecurityValidator.validate_input(value, field_name)
                    
                    # Sanitizar HTML
                    cleaned_data[field_name] = SecurityValidator.sanitize_html(value)
                    
                except ValidationError as e:
                    self.add_error(field_name, e)
        
        return cleaned_data


def secure_file_upload_path(instance, filename):
    """
    Função para gerar paths seguros para upload de arquivos
    """
    import uuid
    import os
    from django.utils import timezone
    
    # Validar nome do arquivo
    SecurityValidator.validate_filename(filename)
    
    # Obter extensão
    _, ext = os.path.splitext(filename)
    
    # Gerar nome único
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    
    # Organizar por data
    date_path = timezone.now().strftime('%Y/%m/%d')
    
    return f'uploads/{date_path}/{unique_filename}'