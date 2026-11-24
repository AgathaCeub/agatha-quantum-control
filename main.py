import argparse
import math
import random
import sys

import pygame


# ============================================================
# CONFIGURAÇÕES INICIAIS
# ============================================================

LARGURA = 1280
ALTURA = 720
FPS = 60
PASSO_SIMULACAO = 1 / 60


# ============================================================
# CORES
# ============================================================

FUNDO = (5, 9, 20)
PAINEL = (14, 23, 42)
PAINEL_CLARO = (23, 37, 63)
BORDA = (71, 103, 145)

BRANCO = (235, 244, 255)
CINZA = (145, 165, 190)
AZUL = (48, 175, 255)
CIANO = (67, 245, 255)
VERDE = (71, 235, 151)
AMARELO = (255, 210, 74)
LARANJA = (255, 139, 55)
VERMELHO = (255, 70, 90)
ROXO = (180, 91, 255)
ROSA = (255, 105, 210)
PRETO = (0, 0, 0)


# ============================================================
# FONTES
# ============================================================

def preparar_interface():
    global TELA, RELOGIO
    global FONTE_TITULO, FONTE_SUBTITULO, FONTE_MEDIA, FONTE_PEQUENA, FONTE_MICRO

    pygame.init()
    TELA = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("ÁGATHA: Quantum Control Room")
    RELOGIO = pygame.time.Clock()

    FONTE_TITULO = pygame.font.SysFont("arial", 45, bold=True)
    FONTE_SUBTITULO = pygame.font.SysFont("arial", 25, bold=True)
    FONTE_MEDIA = pygame.font.SysFont("arial", 20)
    FONTE_PEQUENA = pygame.font.SysFont("arial", 16)
    FONTE_MICRO = pygame.font.SysFont("arial", 13)


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def limitar(valor, minimo, maximo):
    """Mantém um valor entre um mínimo e um máximo."""
    return max(minimo, min(valor, maximo))


def desenhar_texto(texto, fonte, cor, x, y, centralizado=False):
    """Desenha um texto na tela."""
    superficie = fonte.render(str(texto), True, cor)

    if centralizado:
        retangulo = superficie.get_rect(center=(x, y))
        TELA.blit(superficie, retangulo)
    else:
        TELA.blit(superficie, (x, y))


def desenhar_texto_quebrado(texto, fonte, cor, retangulo, espacamento=5):
    """Quebra um texto automaticamente dentro de uma área."""
    palavras = texto.split()
    linhas = []
    linha_atual = ""

    for palavra in palavras:
        teste = linha_atual + palavra + " "

        if fonte.size(teste)[0] <= retangulo.width:
            linha_atual = teste
        else:
            linhas.append(linha_atual)
            linha_atual = palavra + " "

    linhas.append(linha_atual)

    y = retangulo.y

    for linha in linhas:
        superficie = fonte.render(linha.strip(), True, cor)
        TELA.blit(superficie, (retangulo.x, y))
        y += fonte.get_height() + espacamento


def cor_por_valor(valor, invertido=False):
    """
    Retorna uma cor baseada no valor.
    Para temperatura e anomalia, valores altos são ruins.
    """
    if invertido:
        if valor < 40:
            return VERDE
        if valor < 70:
            return AMARELO
        return VERMELHO

    if valor >= 70:
        return VERDE
    if valor >= 40:
        return AMARELO
    return VERMELHO


# ============================================================
# BOTÃO
# ============================================================

class Botao:
    def __init__(self, x, y, largura, altura, texto, cor=AZUL):
        self.retangulo = pygame.Rect(x, y, largura, altura)
        self.texto = texto
        self.cor = cor
        self.ativo = True

    def desenhar(self):
        mouse = pygame.mouse.get_pos()
        sobre = self.retangulo.collidepoint(mouse)

        cor_atual = self.cor

        if sobre and self.ativo:
            cor_atual = tuple(min(255, componente + 35) for componente in self.cor)

        if not self.ativo:
            cor_atual = (60, 68, 80)

        pygame.draw.rect(
            TELA,
            cor_atual,
            self.retangulo,
            border_radius=8
        )

        pygame.draw.rect(
            TELA,
            BRANCO if sobre and self.ativo else BORDA,
            self.retangulo,
            2,
            border_radius=8
        )

        desenhar_texto(
            self.texto,
            FONTE_PEQUENA,
            BRANCO,
            self.retangulo.centerx,
            self.retangulo.centery,
            centralizado=True
        )

    def foi_clicado(self, evento):
        return (
            self.ativo
            and evento.type == pygame.MOUSEBUTTONDOWN
            and evento.button == 1
            and self.retangulo.collidepoint(evento.pos)
        )


# ============================================================
# PARTÍCULAS DO REATOR
# ============================================================

class Particula:
    def __init__(self, centro_x, centro_y, raio_maximo, cor):
        self.centro_x = centro_x
        self.centro_y = centro_y
        self.raio_maximo = raio_maximo
        self.cor = cor

        self.angulo = random.uniform(0, math.tau)
        self.distancia = random.uniform(20, raio_maximo)
        self.velocidade = random.uniform(0.005, 0.025)
        self.tamanho = random.randint(2, 5)

    def atualizar(self, intensidade):
        self.angulo += self.velocidade * intensidade

    def desenhar(self):
        x = self.centro_x + math.cos(self.angulo) * self.distancia
        y = self.centro_y + math.sin(self.angulo) * self.distancia * 0.58

        pygame.draw.circle(
            TELA,
            self.cor,
            (int(x), int(y)),
            self.tamanho
        )


# ============================================================
# JOGO PRINCIPAL
# ============================================================

class Jogo:
    def __init__(self, semente=None):
        self.semente = semente
        self.sorteio = random.Random(semente)
        self.acumulador = 0
        self.proximo_evento = 0
        self.tela_atual = "menu"
        self.experimento = None

        self.tempo = 0
        self.tempo_evento = 0
        self.tempo_mensagem = 0

        self.temperatura = 35
        self.energia = 40
        self.estabilidade = 80
        self.contencao = 85
        self.anomalia = 10
        self.progresso = 0

        self.mensagem = (
            "Selecione um experimento para iniciar a operação."
        )

        self.estado_final = None
        self.particulas = []

        self.criar_botoes()

    def criar_botoes(self):
        # Menu
        self.botao_estrela = Botao(
            130, 230, 300, 90,
            "REATOR ESTELAR",
            LARANJA
        )

        self.botao_singularidade = Botao(
            490, 230, 300, 90,
            "SINGULARIDADE",
            ROXO
        )

        self.botao_quantico = Botao(
            850, 230, 300, 90,
            "NÚCLEO QUÂNTICO",
            AZUL
        )

        # Sala de controle
        self.botao_energia = Botao(
            70, 505, 230, 55,
            "AUMENTAR ENERGIA",
            AZUL
        )

        self.botao_resfriar = Botao(
            325, 505, 230, 55,
            "ATIVAR RESFRIAMENTO",
            CIANO
        )

        self.botao_estabilizar = Botao(
            70, 580, 230, 55,
            "ESTABILIZAR CAMPO",
            VERDE
        )

        self.botao_analisar = Botao(
            325, 580, 230, 55,
            "ANALISAR ANOMALIA",
            ROXO
        )

        self.botao_emergencia = Botao(
            895, 580, 300, 55,
            "PROTOCOLO DE EMERGÊNCIA",
            VERMELHO
        )

        self.botao_reiniciar = Botao(
            490, 560, 300, 65,
            "REINICIAR EXPERIMENTO",
            AZUL
        )

        self.botao_menu = Botao(
            490, 645, 300, 45,
            "VOLTAR AO MENU",
            PAINEL_CLARO
        )

    def iniciar_experimento(self, experimento):
        self.sorteio.seed(self.semente)
        self.acumulador = 0
        self.proximo_evento = self.sorteio.uniform(7, 12)
        self.experimento = experimento
        self.tela_atual = "jogo"
        self.estado_final = None

        self.tempo = 0
        self.tempo_evento = 0
        self.tempo_mensagem = 0

        self.temperatura = 32
        self.energia = 35
        self.estabilidade = 85
        self.contencao = 90
        self.anomalia = 8
        self.progresso = 0

        if experimento == "estrela":
            self.mensagem = (
                "Objetivo: formar uma estrela artificial estável. "
                "Aumente a energia sem deixar a temperatura sair do controle."
            )
            cor = LARANJA

        elif experimento == "singularidade":
            self.mensagem = (
                "Objetivo: manter a singularidade confinada. "
                "O campo de contenção é sua principal proteção."
            )
            cor = ROXO

        else:
            self.mensagem = (
                "Objetivo: observar o núcleo quântico. "
                "Equilibre energia, estabilidade e nível de anomalia."
            )
            cor = CIANO

        self.particulas = [
            Particula(875, 300, random.randint(70, 170), cor)
            for _ in range(85)
        ]

    def definir_mensagem(self, texto):
        self.mensagem = texto
        self.tempo_mensagem = 0

    def aumentar_energia(self):
        aumento = self.sorteio.randint(8, 15)

        self.energia += aumento
        self.temperatura += self.sorteio.randint(5, 11)
        self.estabilidade -= self.sorteio.randint(2, 7)
        self.anomalia += self.sorteio.randint(1, 5)

        self.definir_mensagem(
            f"Energia elevada em {aumento}%. "
            "Mais energia acelera o experimento, mas também aumenta "
            "temperatura e instabilidade."
        )

    def resfriar(self):
        reducao = self.sorteio.randint(10, 18)

        self.temperatura -= reducao
        self.energia -= self.sorteio.randint(2, 6)
        self.contencao += self.sorteio.randint(1, 4)

        self.definir_mensagem(
            f"Temperatura reduzida em {reducao}%. "
            "O resfriamento protege o sistema, mas consome parte da energia."
        )

    def estabilizar(self):
        ganho = self.sorteio.randint(8, 15)

        self.estabilidade += ganho
        self.contencao += self.sorteio.randint(4, 9)
        self.energia -= self.sorteio.randint(3, 8)

        self.definir_mensagem(
            f"Campo estabilizado em {ganho}%. "
            "Estabilidade evita reações imprevisíveis, mas exige energia."
        )

    def analisar(self):
        if self.sorteio.random() < 0.72:
            reducao = self.sorteio.randint(5, 12)
            self.anomalia -= reducao
            self.estabilidade += self.sorteio.randint(2, 6)

            self.definir_mensagem(
                f"Análise concluída. A anomalia foi reduzida em {reducao}%. "
                "Observar o sistema antes de agir diminui a incerteza."
            )
        else:
            self.anomalia += self.sorteio.randint(5, 11)

            self.definir_mensagem(
                "A medição interferiu no experimento! "
                "Em sistemas quânticos fictícios, observar também pode "
                "alterar o resultado."
            )

    def emergencia(self):
        self.energia -= 25
        self.temperatura -= 22
        self.anomalia -= 15
        self.contencao += 18
        self.estabilidade += 10

        self.definir_mensagem(
            "Protocolo de emergência ativado. "
            "O progresso foi reduzido para priorizar a segurança."
        )

        self.progresso -= 12

    def evento_aleatorio(self):
        eventos = [
            "oscilacao",
            "falha_sensor",
            "pulso",
            "calmaria",
            "interferencia"
        ]

        evento = self.sorteio.choice(eventos)

        if evento == "oscilacao":
            self.estabilidade -= self.sorteio.randint(5, 12)

            self.definir_mensagem(
                "ALERTA: uma oscilação inesperada reduziu a estabilidade."
            )

        elif evento == "falha_sensor":
            self.anomalia += self.sorteio.randint(4, 9)

            self.definir_mensagem(
                "ALERTA: sensores apresentaram leituras contraditórias. "
                "A incerteza do sistema aumentou."
            )

        elif evento == "pulso":
            self.energia += self.sorteio.randint(5, 12)
            self.temperatura += self.sorteio.randint(4, 10)

            self.definir_mensagem(
                "Um pulso energético atravessou o núcleo. "
                "A energia subiu junto com a temperatura."
            )

        elif evento == "calmaria":
            self.estabilidade += self.sorteio.randint(4, 10)
            self.anomalia -= self.sorteio.randint(2, 7)

            self.definir_mensagem(
                "O sistema entrou em uma fase de equilíbrio temporário."
            )

        elif evento == "interferencia":
            self.contencao -= self.sorteio.randint(5, 12)

            self.definir_mensagem(
                "ALERTA: interferência externa detectada no campo de contenção."
            )

    def atualizar(self, delta):
        if self.tela_atual != "jogo" or self.estado_final:
            return

        if not math.isfinite(delta) or delta <= 0:
            return

        self.acumulador += delta
        while self.acumulador + 1e-10 >= PASSO_SIMULACAO and not self.estado_final:
            self.acumulador = max(0, self.acumulador - PASSO_SIMULACAO)
            self.avancar_passo()

    def avancar_passo(self):
        # A tela pode desenhar em outro FPS; o experimento mantém o mesmo ritmo.
        self.tempo += PASSO_SIMULACAO
        self.tempo_evento += PASSO_SIMULACAO
        self.tempo_mensagem += PASSO_SIMULACAO

        # Mudanças naturais do sistema
        self.temperatura += self.energia * 0.0018
        self.temperatura -= 0.018

        self.energia -= 0.008
        self.estabilidade -= self.anomalia * 0.00045

        if self.temperatura > 75:
            self.estabilidade -= 0.035

        if self.energia > 80:
            self.anomalia += 0.018

        if self.estabilidade < 45:
            self.contencao -= 0.025

        # Progresso depende de equilíbrio
        condicao_segura = (
            35 <= self.temperatura <= 78
            and self.estabilidade >= 45
            and self.contencao >= 50
            and self.anomalia <= 65
            and self.energia >= 35
        )

        if condicao_segura:
            self.progresso += 0.025
        else:
            self.progresso -= 0.006

        # Eventos aleatórios
        if self.tempo_evento >= self.proximo_evento:
            self.evento_aleatorio()
            self.tempo_evento -= self.proximo_evento
            self.proximo_evento = self.sorteio.uniform(7, 12)

        # Limites
        self.temperatura = limitar(self.temperatura, 0, 100)
        self.energia = limitar(self.energia, 0, 100)
        self.estabilidade = limitar(self.estabilidade, 0, 100)
        self.contencao = limitar(self.contencao, 0, 100)
        self.anomalia = limitar(self.anomalia, 0, 100)
        self.progresso = limitar(self.progresso, 0, 100)

        intensidade = 0.5 + self.energia / 40

        for particula in self.particulas:
            particula.atualizar(intensidade)

        self.verificar_final()

    def verificar_final(self):
        if self.progresso >= 100:
            self.estado_final = "vitoria"

        elif self.temperatura >= 100:
            self.estado_final = "superaquecimento"

        elif self.contencao <= 0:
            self.estado_final = "colapso"

        elif self.estabilidade <= 0:
            self.estado_final = "instabilidade"

        elif self.anomalia >= 100:
            self.estado_final = "anomalia"

        elif self.energia <= 0:
            self.estado_final = "sem_energia"

    def desenhar_barra(self, nome, valor, x, y, invertido=False):
        largura = 250
        altura = 20

        desenhar_texto(
            f"{nome}: {int(valor)}%",
            FONTE_PEQUENA,
            BRANCO,
            x,
            y - 24
        )

        pygame.draw.rect(
            TELA,
            (34, 44, 60),
            (x, y, largura, altura),
            border_radius=6
        )

        pygame.draw.rect(
            TELA,
            cor_por_valor(valor, invertido),
            (x, y, largura * valor / 100, altura),
            border_radius=6
        )

        pygame.draw.rect(
            TELA,
            BORDA,
            (x, y, largura, altura),
            2,
            border_radius=6
        )

    def desenhar_menu(self):
        TELA.fill(FUNDO)

        # Linhas decorativas
        for x in range(0, LARGURA, 80):
            pygame.draw.line(
                TELA,
                (10, 21, 39),
                (x, 0),
                (x, ALTURA)
            )

        for y in range(0, ALTURA, 80):
            pygame.draw.line(
                TELA,
                (10, 21, 39),
                (0, y),
                (LARGURA, y)
            )

        desenhar_texto(
            "ÁGATHA",
            FONTE_TITULO,
            CIANO,
            LARGURA // 2,
            75,
            centralizado=True
        )

        desenhar_texto(
            "QUANTUM CONTROL ROOM",
            FONTE_SUBTITULO,
            BRANCO,
            LARGURA // 2,
            125,
            centralizado=True
        )

        desenhar_texto(
            "Selecione o experimento que será iniciado na instalação.",
            FONTE_MEDIA,
            CINZA,
            LARGURA // 2,
            175,
            centralizado=True
        )

        self.botao_estrela.desenhar()
        self.botao_singularidade.desenhar()
        self.botao_quantico.desenhar()

        descricoes = [
            (
                "Crie uma estrela artificial e aprenda sobre "
                "energia, calor e equilíbrio."
            ),
            (
                "Mantenha uma singularidade fictícia presa em "
                "um campo de contenção."
            ),
            (
                "Explore probabilidades, partículas e anomalias "
                "em um núcleo experimental."
            )
        ]

        posicoes = [130, 490, 850]

        for x, descricao in zip(posicoes, descricoes):
            area = pygame.Rect(x, 345, 300, 100)

            desenhar_texto_quebrado(
                descricao,
                FONTE_PEQUENA,
                CINZA,
                area
            )

        pygame.draw.rect(
            TELA,
            PAINEL,
            (210, 500, 860, 105),
            border_radius=12
        )

        pygame.draw.rect(
            TELA,
            BORDA,
            (210, 500, 860, 105),
            2,
            border_radius=12
        )

        desenhar_texto(
            "MISSÃO",
            FONTE_SUBTITULO,
            AMARELO,
            LARGURA // 2,
            530,
            centralizado=True
        )

        desenhar_texto(
            "Concluir o experimento sem perder a estabilidade da instalação.",
            FONTE_MEDIA,
            BRANCO,
            LARGURA // 2,
            570,
            centralizado=True
        )

        desenhar_texto(
            "Projeto educacional fictício — nenhuma operação nuclear real é simulada.",
            FONTE_MICRO,
            CINZA,
            LARGURA // 2,
            675,
            centralizado=True
        )

    def desenhar_nucleo(self):
        # Janela de observação
        janela = pygame.Rect(600, 105, 550, 390)

        pygame.draw.rect(
            TELA,
            (2, 7, 16),
            janela,
            border_radius=25
        )

        pygame.draw.rect(
            TELA,
            BORDA,
            janela,
            7,
            border_radius=25
        )

        # Reflexos no vidro
        pygame.draw.line(
            TELA,
            (35, 62, 85),
            (630, 140),
            (770, 110),
            5
        )

        pygame.draw.line(
            TELA,
            (28, 53, 75),
            (1020, 470),
            (1120, 400),
            4
        )

        # Cor do núcleo
        if self.experimento == "estrela":
            cor_nucleo = LARANJA
        elif self.experimento == "singularidade":
            cor_nucleo = ROXO
        else:
            cor_nucleo = CIANO

        pulsacao = math.sin(pygame.time.get_ticks() * 0.004)
        tamanho = int(55 + pulsacao * 8 + self.energia * 0.25)

        # Campo externo
        for raio in range(tamanho + 70, tamanho, -12):
            cor_campo = (
                max(0, cor_nucleo[0] // 4),
                max(0, cor_nucleo[1] // 4),
                max(0, cor_nucleo[2] // 4)
            )

            pygame.draw.circle(
                TELA,
                cor_campo,
                (875, 300),
                raio,
                2
            )

        for particula in self.particulas:
            particula.desenhar()

        # Núcleo
        pygame.draw.circle(
            TELA,
            cor_nucleo,
            (875, 300),
            tamanho
        )

        pygame.draw.circle(
            TELA,
            BRANCO,
            (875, 300),
            max(12, tamanho // 3)
        )

        pygame.draw.circle(
            TELA,
            cor_nucleo,
            (875, 300),
            tamanho,
            4
        )

        if self.anomalia >= 70:
            desenhar_texto(
                "ANOMALIA CRÍTICA",
                FONTE_SUBTITULO,
                VERMELHO,
                875,
                455,
                centralizado=True
            )
        else:
            desenhar_texto(
                "JANELA DE OBSERVAÇÃO DO NÚCLEO",
                FONTE_PEQUENA,
                CINZA,
                875,
                455,
                centralizado=True
            )

    def desenhar_sala(self):
        TELA.fill(FUNDO)

        # Cabeçalho
        pygame.draw.rect(
            TELA,
            PAINEL,
            (0, 0, LARGURA, 70)
        )

        desenhar_texto(
            "ÁGATHA // CENTRAL DE COMANDO",
            FONTE_SUBTITULO,
            CIANO,
            35,
            20
        )

        desenhar_texto(
            f"PROGRESSO DO EXPERIMENTO: {int(self.progresso)}%",
            FONTE_PEQUENA,
            BRANCO,
            935,
            25
        )

        # Painel esquerdo
        pygame.draw.rect(
            TELA,
            PAINEL,
            (35, 95, 540, 375),
            border_radius=14
        )

        pygame.draw.rect(
            TELA,
            BORDA,
            (35, 95, 540, 375),
            2,
            border_radius=14
        )

        desenhar_texto(
            "DADOS DO SISTEMA",
            FONTE_SUBTITULO,
            BRANCO,
            65,
            120
        )

        self.desenhar_barra(
            "Temperatura",
            self.temperatura,
            70,
            180,
            invertido=True
        )

        self.desenhar_barra(
            "Energia",
            self.energia,
            320,
            180
        )

        self.desenhar_barra(
            "Estabilidade",
            self.estabilidade,
            70,
            255
        )

        self.desenhar_barra(
            "Contenção",
            self.contencao,
            320,
            255
        )

        self.desenhar_barra(
            "Anomalia",
            self.anomalia,
            70,
            330,
            invertido=True
        )

        self.desenhar_barra(
            "Progresso",
            self.progresso,
            320,
            330
        )

        # Mensagem educativa
        pygame.draw.rect(
            TELA,
            PAINEL_CLARO,
            (60, 390, 490, 60),
            border_radius=8
        )

        area_texto = pygame.Rect(75, 400, 460, 45)

        desenhar_texto_quebrado(
            self.mensagem,
            FONTE_MICRO,
            BRANCO,
            area_texto,
            espacamento=2
        )

        # Núcleo e controles
        self.desenhar_nucleo()

        self.botao_energia.desenhar()
        self.botao_resfriar.desenhar()
        self.botao_estabilizar.desenhar()
        self.botao_analisar.desenhar()
        self.botao_emergencia.desenhar()

        desenhar_texto(
            "Meta: leve o progresso a 100% mantendo todos os sistemas seguros.",
            FONTE_PEQUENA,
            CINZA,
            895,
            545,
            centralizado=True
        )

        # Barra inferior
        pygame.draw.rect(
            TELA,
            PAINEL,
            (0, 680, LARGURA, 40)
        )

        desenhar_texto(
            "OPERADORA: ÁGATHA CASTRO",
            FONTE_MICRO,
            CIANO,
            30,
            693
        )

        desenhar_texto(
            "STATUS: EXPERIMENTO ATIVO",
            FONTE_MICRO,
            VERDE,
            1055,
            693
        )

    def desenhar_final(self):
        TELA.fill(FUNDO)

        if self.estado_final == "vitoria":
            titulo = "EXPERIMENTO CONCLUÍDO"
            cor = VERDE
            explicacao = (
                "Você conseguiu equilibrar energia, temperatura, "
                "estabilidade e contenção. Sistemas complexos funcionam "
                "melhor quando nenhuma variável é analisada isoladamente."
            )

        elif self.estado_final == "superaquecimento":
            titulo = "SUPERAQUECIMENTO"
            cor = VERMELHO
            explicacao = (
                "A temperatura atingiu o limite. Aumentar energia sem "
                "controlar o calor criou um desequilíbrio no sistema."
            )

        elif self.estado_final == "colapso":
            titulo = "FALHA DE CONTENÇÃO"
            cor = VERMELHO
            explicacao = (
                "O campo de contenção chegou a zero. Um sistema de proteção "
                "precisa ser mantido antes que uma emergência aconteça."
            )

        elif self.estado_final == "instabilidade":
            titulo = "COLAPSO DE ESTABILIDADE"
            cor = VERMELHO
            explicacao = (
                "O experimento tornou-se imprevisível. Pequenas alterações "
                "acumuladas podem provocar grandes consequências."
            )

        elif self.estado_final == "anomalia":
            titulo = "ANOMALIA FORA DE CONTROLE"
            cor = ROXO
            explicacao = (
                "A incerteza ultrapassou o limite de observação. Nem sempre "
                "produzir mais energia significa obter melhores resultados."
            )

        else:
            titulo = "ENERGIA ESGOTADA"
            cor = AMARELO
            explicacao = (
                "A instalação ficou sem energia. Segurança, pesquisa e "
                "progresso precisam compartilhar recursos limitados."
            )

        desenhar_texto(
            titulo,
            FONTE_TITULO,
            cor,
            LARGURA // 2,
            150,
            centralizado=True
        )

        pygame.draw.rect(
            TELA,
            PAINEL,
            (290, 230, 700, 220),
            border_radius=18
        )

        pygame.draw.rect(
            TELA,
            cor,
            (290, 230, 700, 220),
            3,
            border_radius=18
        )

        area = pygame.Rect(350, 285, 580, 120)

        desenhar_texto_quebrado(
            explicacao,
            FONTE_MEDIA,
            BRANCO,
            area,
            espacamento=10
        )

        self.botao_reiniciar.desenhar()
        self.botao_menu.desenhar()

    def tratar_evento(self, evento):
        if evento.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if self.tela_atual == "menu":
            if self.botao_estrela.foi_clicado(evento):
                self.iniciar_experimento("estrela")

            elif self.botao_singularidade.foi_clicado(evento):
                self.iniciar_experimento("singularidade")

            elif self.botao_quantico.foi_clicado(evento):
                self.iniciar_experimento("quantico")

        elif self.tela_atual == "jogo":
            if self.estado_final:
                if self.botao_reiniciar.foi_clicado(evento):
                    self.iniciar_experimento(self.experimento)

                elif self.botao_menu.foi_clicado(evento):
                    self.tela_atual = "menu"

            else:
                if self.botao_energia.foi_clicado(evento):
                    self.aumentar_energia()

                elif self.botao_resfriar.foi_clicado(evento):
                    self.resfriar()

                elif self.botao_estabilizar.foi_clicado(evento):
                    self.estabilizar()

                elif self.botao_analisar.foi_clicado(evento):
                    self.analisar()

                elif self.botao_emergencia.foi_clicado(evento):
                    self.emergencia()

    def desenhar(self):
        if self.tela_atual == "menu":
            self.desenhar_menu()

        elif self.estado_final:
            self.desenhar_final()

        else:
            self.desenhar_sala()


# ============================================================
# LOOP PRINCIPAL
# ============================================================

def executar():
    argumentos = argparse.ArgumentParser(description="Sala de controle experimental da Ágatha")
    argumentos.add_argument("--semente", type=int, help="Repete a sequência de eventos ao reiniciar")
    opcoes = argumentos.parse_args()

    preparar_interface()
    jogo = Jogo(semente=opcoes.semente)

    while True:
        delta = RELOGIO.tick(FPS) / 1000

        for evento in pygame.event.get():
            jogo.tratar_evento(evento)

        jogo.atualizar(delta)
        jogo.desenhar()
        pygame.display.flip()


if __name__ == "__main__":
    executar()

