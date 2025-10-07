#!/usr/bin/env python3
"""
Script para verificar o status do deployment do Azure
"""
import requests
import time
from datetime import datetime

def check_azure_app():
    """Verifica se a aplicação Azure está respondendo"""
    url = "https://fretamento.azurewebsites.net"
    
    try:
        print(f"🔍 Verificando {url} às {datetime.now().strftime('%H:%M:%S')}")
        
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            print("✅ App Azure está online!")
            print(f"📊 Status Code: {response.status_code}")
            
            # Verificar se é a página Django ou página de placeholder
            if "Django" in response.text or "fretamento" in response.text.lower():
                print("🎉 Django app está funcionando!")
                return True
            else:
                print("⚠️  Respondendo mas pode ser página de placeholder")
                print(f"📄 Primeiros 200 chars: {response.text[:200]}")
                return False
        else:
            print(f"❌ Status Code: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na conexão: {e}")
        return False

def main():
    """Monitora o deployment por alguns minutos"""
    print("🚀 Monitorando deployment do Azure...")
    print("⏱️  Aguardando deployment ser processado...")
    
    max_attempts = 10
    for attempt in range(1, max_attempts + 1):
        print(f"\n--- Tentativa {attempt}/{max_attempts} ---")
        
        if check_azure_app():
            print("\n🎊 Deployment bem-sucedido!")
            break
        
        if attempt < max_attempts:
            print("⏳ Aguardando 30 segundos...")
            time.sleep(30)
    else:
        print("\n⚠️  Deployment ainda processando. Verifique manualmente:")
        print("🔗 GitHub Actions: https://github.com/andersonodev/fretamento/actions")
        print("🔗 Azure Portal: https://portal.azure.com")

if __name__ == "__main__":
    main()