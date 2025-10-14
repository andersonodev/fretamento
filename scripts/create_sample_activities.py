#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import ActivityLog

def create_sample_activities():
    user = User.objects.first()
    if not user:
        print('❌ Usuário não encontrado')
        return

    activities = [
        {
            'activity_type': 'LOGIN',
            'description': 'Login realizado no sistema',
            'details': 'Acesso ao dashboard principal às 09:30'
        },
        {
            'activity_type': 'UPLOAD',
            'description': 'Upload de planilha OS realizado',
            'details': 'Arquivo planilha_servicos_outubro.xlsx processado com 58 serviços',
            'object_type': 'Arquivo',
            'object_id': '1'
        },
        {
            'activity_type': 'CREATE',
            'description': 'Novo serviço de fretamento criado',
            'details': 'Serviço para Aeroporto Guarulhos - 4 passageiros',
            'object_type': 'Serviço',
            'object_id': '123'
        },
        {
            'activity_type': 'PROCESS',
            'description': 'Processamento de escalas executado',
            'details': 'Geração automática de escalas para os próximos 7 dias',
            'object_type': 'Escala'
        },
        {
            'activity_type': 'UPDATE',
            'description': 'Configurações de tarifário atualizadas',
            'details': 'Ajuste nos valores de quilometragem urbana'
        },
        {
            'activity_type': 'EXPORT',
            'description': 'Relatório mensal exportado',
            'details': 'Relatório de outubro em formato Excel gerado',
            'object_type': 'Relatório'
        },
        {
            'activity_type': 'VIEW',
            'description': 'Página de diagnóstico acessada',
            'details': 'Visualização de estatísticas e gráficos'
        },
        {
            'activity_type': 'DELETE',
            'description': 'Serviço cancelado removido',
            'details': 'Exclusão de serviço duplicado do sistema',
            'object_type': 'Serviço'
        }
    ]

    for activity in activities:
        ActivityLog.objects.create(
            user=user,
            activity_type=activity['activity_type'],
            description=activity['description'],
            details=activity['details'],
            object_type=activity.get('object_type', ''),
            object_id=activity.get('object_id', ''),
            ip_address='127.0.0.1'
        )

    print(f'✅ {len(activities)} atividades de exemplo criadas com sucesso!')

if __name__ == '__main__':
    create_sample_activities()