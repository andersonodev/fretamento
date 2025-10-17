"""
Teste para validar a limpeza de serviços com C/GUIA e S/GUIA
"""
import re

def limpar_servico(servico_original: str) -> str:
    """Replica a lógica de limpeza de serviços"""
    if not servico_original or servico_original == 'nan':
        return ""
    
    servico = str(servico_original).strip()
    
    # 1. Limpeza e substituições gerais
    servico = re.sub(r'^\d+\s*[-–]?\s*', '', servico)  # Remove prefixo numérico
    
    # 2. Substituições específicas para GUIA - apenas se o serviço contém esses termos
    if re.search(r'S\s*\/\s*GUIA', servico, flags=re.IGNORECASE):
        servico = re.sub(r'S\s*\/\s*GUIA', 'Sem Guia', servico, flags=re.IGNORECASE)
    
    if re.search(r'C\s*\/\s*GUIA', servico, flags=re.IGNORECASE):
        servico = re.sub(r'C\s*\/\s*GUIA', 'Com Guia', servico, flags=re.IGNORECASE)
    
    servico = re.sub(r'P\/\s*', 'PARA ', servico, flags=re.IGNORECASE)  # Substitui "P/" por "PARA "
    servico = re.sub(r'\bZ\.SUL\b', 'ZONA SUL', servico, flags=re.IGNORECASE)  # Substitui "Z.SUL"
    
    # 2. Limpeza final
    servico = re.sub(r'\s*-\s*$', '', servico).strip()  # Remove hífen final
    servico = re.sub(r'\s{2,}', ' ', servico).strip()  # Remove espaços duplos
    
    return servico

def test_limpeza_guia():
    """Testa se C/GUIA e S/GUIA são corretamente substituídos"""
    
    # Casos de teste para conversão (serviços que DEVEM ser convertidos)
    test_cases_conversao = [
        ("TOUR P/ BÚZIOS C/GUIA", "TOUR PARA BÚZIOS Com Guia"),
        ("TOUR P/ BÚZIOS S/GUIA", "TOUR PARA BÚZIOS Sem Guia"),
        ("TOUR P/ BÚZIOS C / GUIA", "TOUR PARA BÚZIOS Com Guia"),
        ("TOUR P/ BÚZIOS S / GUIA", "TOUR PARA BÚZIOS Sem Guia"),
        ("001 - TOUR P/ BÚZIOS C/GUIA", "TOUR PARA BÚZIOS Com Guia"),
        ("CITY TOUR C/GUIA", "CITY TOUR Com Guia"),
        ("PASSEIO S/GUIA", "PASSEIO Sem Guia"),
        ("TOUR P/ BÚZIOS c/guia", "TOUR PARA BÚZIOS Com Guia"),  # lowercase
        ("TOUR P/ BÚZIOS s/guia", "TOUR PARA BÚZIOS Sem Guia"),  # lowercase
    ]
    
    # Casos de teste para NÃO conversão (serviços que NÃO devem ser convertidos)
    test_cases_sem_conversao = [
        ("TRANSFER IN AEROPORTO", "TRANSFER IN AEROPORTO"),
        ("TRANSFER OUT HOTEL", "TRANSFER OUT HOTEL"),
        ("CITY TOUR PRIVATIVO", "CITY TOUR PRIVATIVO"),
        ("DISPOSIÇÃO 4H", "DISPOSIÇÃO 4H"),
        ("TOUR PARA PETRÓPOLIS", "TOUR PARA PETRÓPOLIS"),
        ("PASSEIO DE BARCO", "PASSEIO DE BARCO"),
        ("ALMOÇO RESTAURANTE", "ALMOÇO RESTAURANTE"),
        ("CORCOVADO E SANTA TERESA", "CORCOVADO E SANTA TERESA"),
        ("001 - TRANSFER VIP", "TRANSFER VIP"),
    ]
    
    print("\n=== TESTE DE LIMPEZA C/GUIA e S/GUIA ===\n")
    
    all_passed = True
    
    print("🔸 Testando conversões (S/GUIA → Sem Guia, C/GUIA → Com Guia):")
    for original, esperado in test_cases_conversao:
        resultado = limpar_servico(original)
        passou = resultado == esperado
        all_passed = all_passed and passou
        
        status = "✅ PASSOU" if passou else "❌ FALHOU"
        print(f"  {status} '{original}' → '{resultado}'")
        if not passou:
            print(f"    ⚠️  Esperado: '{esperado}'")
    
    print("\n🔸 Testando NÃO conversões (serviços sem S/GUIA ou C/GUIA):")
    for original, esperado in test_cases_sem_conversao:
        resultado = limpar_servico(original)
        passou = resultado == esperado
        all_passed = all_passed and passou
        
        status = "✅ PASSOU" if passou else "❌ FALHOU"
        print(f"  {status} '{original}' → '{resultado}'")
        if not passou:
            print(f"    ⚠️  Esperado: '{esperado}'")
    
    print()
    if all_passed:
        print("🎉 TODOS OS TESTES PASSARAM!")
        return True
    else:
        print("⚠️  ALGUNS TESTES FALHARAM")
        return False

if __name__ == '__main__':
    success = test_limpeza_guia()
    exit(0 if success else 1)

