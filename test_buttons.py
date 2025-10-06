import os
import re
import django
import pytest
from datetime import date, time
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
from escalas.models import Escala, AlocacaoVan, GrupoServico, ServicoGrupo


@pytest.fixture
def escala_com_servicos():
    data_servico = date(2025, 1, 1)
    Escala.objects.filter(data=data_servico).delete()
    Servico.objects.filter(data_do_servico=data_servico).delete()

    escala = Escala.objects.create(data=data_servico, etapa='DADOS_PUXADOS')

    servico_1 = Servico.objects.create(
        numero_venda='Venda001',
        cliente='Hotelbeds',
        local_pickup='Copacabana',
        pax=2,
        horario=time(8, 0),
        data_do_servico=data_servico,
        servico='TOUR REGULAR RIO'
    )
    servico_2 = Servico.objects.create(
        numero_venda='Venda002',
        cliente='Hotelbeds',
        local_pickup='Copacabana',
        pax=3,
        horario=time(8, 20),
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


def test_agrupar_button_cria_grupo(escala_com_servicos):
    client = Client()
    User = get_user_model()
    User.objects.filter(username='usuario').delete()
    usuario = User.objects.create_user('usuario', password='segredo123')
    assert client.login(username=usuario.username, password='segredo123')

    escala = escala_com_servicos['escala']
    data_servico = escala_com_servicos['data']
    url = reverse('escalas:visualizar_escala', kwargs={'data': data_servico.strftime('%d-%m-%Y')})

    response = client.post(url, {'acao': 'agrupar'}, follow=True)
    assert response.status_code == 200

    escala.refresh_from_db()
    grupos = escala.grupos.all()
    assert grupos.count() == 1

    grupo = grupos.first()
    assert grupo.total_pax == 5
    assert grupo.numeros_venda == 'Venda001 / Venda002'
    assert grupo.servicos.count() == 2

    alocacoes_ids = {alocacao.id for alocacao in escala_com_servicos['alocacoes']}
    relacionamentos = ServicoGrupo.objects.filter(grupo=grupo)
    assert {rel.alocacao_id for rel in relacionamentos} == alocacoes_ids

    escala.refresh_from_db()
    assert escala.etapa == 'DADOS_PUXADOS'
    assert not escala.alocacoes.filter(status_alocacao='NAO_ALOCADO').exists()

    mensagens = list(get_messages(response.wsgi_request))
    assert any('Agrupamento concluído' in str(mensagem) for mensagem in mensagens)


def test_botao_agrupar_idempotente(escala_com_servicos):
    client = Client()
    User = get_user_model()
    User.objects.filter(username='usuario2').delete()
    usuario = User.objects.create_user('usuario2', password='segredo123')
    assert client.login(username=usuario.username, password='segredo123')

    escala = escala_com_servicos['escala']
    data_servico = escala_com_servicos['data']
    url = reverse('escalas:visualizar_escala', kwargs={'data': data_servico.strftime('%d-%m-%Y')})

    primeira_execucao = client.post(url, {'acao': 'agrupar'}, follow=True)
    assert primeira_execucao.status_code == 200
    assert GrupoServico.objects.filter(escala=escala).count() == 1

    segunda_execucao = client.post(url, {'acao': 'agrupar'}, follow=True)
    assert segunda_execucao.status_code == 200
    assert GrupoServico.objects.filter(escala=escala).count() == 1

    mensagens = list(get_messages(segunda_execucao.wsgi_request))
    assert any('Agrupamento concluído' in str(mensagem) for mensagem in mensagens)


def _assert_button_has_feedback(html, button_id):
    botao_pattern = re.compile(rf'<button[^>]*id="{button_id}"[^>]*>.*?</button>', re.DOTALL)
    match = botao_pattern.search(html)
    assert match is not None, f'Botão com id {button_id} não encontrado.'

    conteudo = match.group(0)
    assert 'button-spinner' in conteudo, f'Spinner ausente no botão {button_id}.'
    assert 'button-icon' in conteudo, f'Ícone ausente no botão {button_id}.'
    assert 'button-text' in conteudo, f'Texto dinâmico ausente no botão {button_id}.'


def test_botoes_visiveis_com_spinners_em_todas_as_etapas(escala_com_servicos):
    client = Client()
    User = get_user_model()
    User.objects.filter(username='usuario3').delete()
    usuario = User.objects.create_user('usuario3', password='segredo123')
    assert client.login(username=usuario.username, password='segredo123')

    escala = escala_com_servicos['escala']
    data_servico = escala_com_servicos['data']
    url = reverse('escalas:visualizar_escala', kwargs={'data': data_servico.strftime('%d-%m-%Y')})

    # Estado inicial: dados puxados
    resposta_dados = client.get(url)
    assert resposta_dados.status_code == 200
    html_dados = resposta_dados.content.decode()

    for botao in ['btn-precificar', 'btn-agrupar', 'btn-escalar']:
        _assert_button_has_feedback(html_dados, botao)

    # Após escalada, os botões devem permanecer disponíveis
    escala.etapa = 'OTIMIZADA'
    escala.save()

    resposta_otimizada = client.get(url)
    assert resposta_otimizada.status_code == 200
    html_otimizada = resposta_otimizada.content.decode()

    for botao in ['btn-precificar', 'btn-agrupar', 'btn-escalar']:
        _assert_button_has_feedback(html_otimizada, botao)
