#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from escalas.models import Escala, AlocacaoVan, GrupoServico

def main():
    escalas = Escala.objects.all()
    print(f'Total de escalas: {escalas.count()}')
    
    if escalas.exists():
        print('\nEscalas disponíveis:')
        for escala in escalas[:10]:
            data_str = escala.data.strftime('%d-%m-%Y')
            alocacoes_count = AlocacaoVan.objects.filter(escala=escala).count()
            grupos_count = GrupoServico.objects.filter(escala=escala).count()
            print(f'- {data_str}: {escala} ({alocacoes_count} alocações, {grupos_count} grupos)')
        
        # Pegar a primeira escala para teste
        primeira_escala = escalas.first()
        data_teste = primeira_escala.data.strftime('%d-%m-%Y')
        print(f'\nPara teste, usar: http://127.0.0.1:8000/escalas/visualizar/{data_teste}/')
    else:
        print('Nenhuma escala encontrada')

if __name__ == '__main__':
    main()