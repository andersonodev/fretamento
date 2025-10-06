import os
import itertools
import django
import pytest
from datetime import date, time, timedelta
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import Client
from django.test.utils import setup_test_environment
from django.urls import reverse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()
if not os.environ.get('DJANGO_TEST_ENVIRONMENT_INITIALIZED'):
    setup_test_environment()
    os.environ['DJANGO_TEST_ENVIRONMENT_INITIALIZED'] = '1'

from core.models import Servico
from escalas.models import Escala, AlocacaoVan, GrupoServico


@pytest.fixture
def escala_para_escalar():
    data_servico = date(2025, 1, 2)
    Escala.objects.filter(data=data_servico).delete()
    Servico.objects.filter(data_do_servico=data_servico).delete()

    escala = Escala.objects.create(data=data_servico, etapa='DADOS_PUXADOS')

    servico_1 = Servico.objects.create(
        numero_venda='Venda010',
        cliente='Holiday',
        local_pickup='Copacabana',
        pax=4,
        horario=time(9, 0),
        data_do_servico=data_servico,
        servico='TOUR REGULAR RIO'
    )
    servico_2 = Servico.objects.create(
        numero_venda='Venda011',
        cliente='Holiday',
        local_pickup='Copacabana',
        pax=2,
        horario=time(9, 20),
        data_do_servico=data_servico,
        servico='TOUR REGULAR RIO'
    )

    alocacao_1 = AlocacaoVan.objects.create(
        escala=escala,
        servico=servico_1,
        van='VAN1',
        ordem=1,
    )
    alocacao_2 = AlocacaoVan.objects.create(
        escala=escala,
        servico=servico_2,
        van='VAN1',
        ordem=2,
    )

    return {
        'escala': escala,
        'alocacoes': (alocacao_1, alocacao_2),
        'data': data_servico,
    }


def test_botao_escalar_distribui_servicos(escala_para_escalar):
    client = Client()
    User = get_user_model()
    User.objects.filter(username='responsavel').delete()
    usuario = User.objects.create_user('responsavel', password='senhaSegura!')
    assert client.login(username=usuario.username, password='senhaSegura!')

    escala = escala_para_escalar['escala']
    data_servico = escala_para_escalar['data']
    url = reverse('escalas:visualizar_escala', kwargs={'data': data_servico.strftime('%d-%m-%Y')})

    # Primeiro, garantir que os serviços estejam agrupados
    resposta_agrupamento = client.post(url, {'acao': 'agrupar'}, follow=True)
    assert resposta_agrupamento.status_code == 200
    escala.refresh_from_db()
    assert escala.grupos.count() == 1

    resposta_escalar = client.post(url, {'acao': 'otimizar'}, follow=True)
    assert resposta_escalar.status_code == 200

    escala.refresh_from_db()
    assert escala.etapa == 'OTIMIZADA'

    alocacoes = list(escala.alocacoes.order_by('id'))
    assert all(alocacao.status_alocacao == 'ALOCADO' for alocacao in alocacoes)
    assert all(alocacao.ordem > 0 for alocacao in alocacoes)

    mensagens = list(get_messages(resposta_escalar.wsgi_request))
    assert any('Escala escalada com sucesso' in str(mensagem) for mensagem in mensagens)


def test_escalar_nao_executa_agrupamento_automatico(escala_para_escalar):
    client = Client()
    User = get_user_model()
    User.objects.filter(username='responsavel2').delete()
    usuario = User.objects.create_user('responsavel2', password='senhaSegura!')
    assert client.login(username=usuario.username, password='senhaSegura!')

    escala = escala_para_escalar['escala']
    data_servico = escala_para_escalar['data']
    url = reverse('escalas:visualizar_escala', kwargs={'data': data_servico.strftime('%d-%m-%Y')})

    assert GrupoServico.objects.filter(escala=escala).count() == 0

    resposta_escalar = client.post(url, {'acao': 'otimizar'}, follow=True)
    assert resposta_escalar.status_code == 200

    escala.refresh_from_db()
    assert GrupoServico.objects.filter(escala=escala).count() == 0
    assert escala.alocacoes.filter(grupo_info__isnull=False).count() == 0
    assert escala.etapa == 'OTIMIZADA'

    mensagens = list(get_messages(resposta_escalar.wsgi_request))
    assert any('Escala escalada com sucesso' in str(mensagem) for mensagem in mensagens)


def test_agrupar_apos_escalar_mantem_independencia(escala_para_escalar):
    client = Client()
    User = get_user_model()
    User.objects.filter(username='responsavel3').delete()
    usuario = User.objects.create_user('responsavel3', password='senhaSegura!')
    assert client.login(username=usuario.username, password='senhaSegura!')

    escala = escala_para_escalar['escala']
    data_servico = escala_para_escalar['data']
    url = reverse('escalas:visualizar_escala', kwargs={'data': data_servico.strftime('%d-%m-%Y')})

    resposta_escalar = client.post(url, {'acao': 'otimizar'}, follow=True)
    assert resposta_escalar.status_code == 200

    escala.refresh_from_db()
    assert escala.etapa == 'OTIMIZADA'
    assert escala.grupos.count() == 0

    status_antes_do_agrupamento = list(
        escala.alocacoes.order_by('id').values_list('id', 'status_alocacao')
    )

    resposta_agrupar = client.post(url, {'acao': 'agrupar'}, follow=True)
    assert resposta_agrupar.status_code == 200

    escala.refresh_from_db()
    assert escala.etapa == 'OTIMIZADA'
    assert escala.grupos.count() == 1

    grupo = escala.grupos.first()
    assert grupo.total_pax == 6
    assert grupo.numeros_venda == 'Venda010 / Venda011'

    alocacoes_associadas = escala.alocacoes.filter(grupo_info__grupo=grupo).order_by('id')
    assert alocacoes_associadas.count() == 2

    status_depois = list(
        escala.alocacoes.order_by('id').values_list('id', 'status_alocacao')
    )
    assert status_depois == status_antes_do_agrupamento

    mensagens = list(get_messages(resposta_agrupar.wsgi_request))
    assert any('Agrupamento concluído' in str(mensagem) for mensagem in mensagens)


@pytest.mark.django_db
def test_botoes_funcionam_em_qualquer_ordem(monkeypatch):
    client = Client()
    User = get_user_model()
    User.objects.filter(username='sequencial').delete()
    usuario = User.objects.create_user('sequencial', password='senhaSegura!')
    assert client.login(username=usuario.username, password='senhaSegura!')

    def fake_precificar(self):
        self.preco_calculado = 123.45
        self.veiculo_recomendado = 'Van Teste'
        self.save(update_fields=['preco_calculado', 'veiculo_recomendado'])
        return self.veiculo_recomendado, self.preco_calculado

    monkeypatch.setattr(AlocacaoVan, 'calcular_preco_e_veiculo', fake_precificar)

    base_data = date(2025, 1, 10)
    acoes = ['precificar', 'agrupar', 'escalar']

    for indice, ordem in enumerate(itertools.permutations(acoes)):
        data_servico = base_data + timedelta(days=indice)

        Escala.objects.filter(data=data_servico).delete()
        Servico.objects.filter(data_do_servico=data_servico).delete()

        escala = Escala.objects.create(data=data_servico, etapa='DADOS_PUXADOS')

        servico_a = Servico.objects.create(
            numero_venda=f'VendaA{indice:02d}',
            cliente='Holiday',
            local_pickup='Copacabana',
            pax=4,
            horario=time(9, 0),
            data_do_servico=data_servico,
            servico='TOUR REGULAR RIO'
        )
        servico_b = Servico.objects.create(
            numero_venda=f'VendaB{indice:02d}',
            cliente='Holiday',
            local_pickup='Copacabana',
            pax=2,
            horario=time(9, 20),
            data_do_servico=data_servico,
            servico='TOUR REGULAR RIO'
        )

        AlocacaoVan.objects.create(escala=escala, servico=servico_a, van='VAN1', ordem=1)
        AlocacaoVan.objects.create(escala=escala, servico=servico_b, van='VAN1', ordem=2)

        data_str = data_servico.strftime('%d-%m-%Y')
        url_visualizar = reverse('escalas:visualizar_escala', kwargs={'data': data_str})
        url_precificar = reverse('escalas:precificar_escala', kwargs={'data': data_str})

        for acao in ordem:
            if acao == 'precificar':
                resposta = client.post(url_precificar, data='{}', content_type='application/json')
                assert resposta.status_code == 200
                payload = resposta.json()
                assert payload['success'] is True
                escala.refresh_from_db()
                assert escala.etapa in ['DADOS_PUXADOS', 'OTIMIZADA']
            elif acao == 'agrupar':
                resposta = client.post(url_visualizar, {'acao': 'agrupar'}, follow=True)
                assert resposta.status_code == 200
                escala.refresh_from_db()
                assert escala.grupos.count() == 1
            elif acao == 'escalar':
                resposta = client.post(url_visualizar, {'acao': 'otimizar'}, follow=True)
                assert resposta.status_code == 200
                escala.refresh_from_db()
                assert escala.etapa == 'OTIMIZADA'
            else:
                raise AssertionError(f'Ação desconhecida na ordem de testes: {acao}')

        # Após todas as ações, garantir que dados essenciais foram preservados
        escala.refresh_from_db()
        assert escala.alocacoes.count() == 2
        assert escala.grupos.count() in {0, 1}
