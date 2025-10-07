#!/usr/bin/env python3
"""
Utilitário para gerar SECRET_KEY segura para Django
"""

import secrets
import string

def generate_secret_key(length=50):
    """
    Gera uma SECRET_KEY segura para Django
    
    Args:
        length (int): Comprimento da chave (padrão: 50)
        
    Returns:
        str: Chave secreta segura
    """
    # Caracteres seguros para SECRET_KEY
    alphabet = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
    
    # Gera chave aleatória
    secret_key = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    return secret_key

def main():
    """Gera e exibe uma nova SECRET_KEY"""
    print("🔐 Gerando nova SECRET_KEY segura...")
    print()
    
    secret_key = generate_secret_key()
    
    print("SECRET_KEY gerada:")
    print(f"'{secret_key}'")
    print()
    
    print("📋 Para usar no .env:")
    print(f"SECRET_KEY={secret_key}")
    print()
    
    print("⚠️  IMPORTANTE:")
    print("- Mantenha esta chave secreta e segura")
    print("- Não commite a chave no controle de versão") 
    print("- Use uma chave diferente para cada ambiente")
    print("- Configure como variável de ambiente em produção")

if __name__ == "__main__":
    main()