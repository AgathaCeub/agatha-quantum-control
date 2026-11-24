import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pygame

from diario import CAMPOS, Diario
from main import Jogo


def valores(**alteracoes):
    return {**dict.fromkeys(CAMPOS, 50), **alteracoes}


class CadernoDeBordo(unittest.TestCase):
    def test_amostras_acompanham_segundos_e_extremos_entre_amostras(self):
        diario = Diario("estrela", 43)
        for passo in range(121):
            temperatura = 90 if passo == 15 else 40
            diario.observar(passo / 60, valores(temperatura=temperatura), True, 1 / 60)
        self.assertEqual([a["segundos"] for a in diario.amostras], [0, 1, 2])
        self.assertEqual(diario.pico_temperatura, 90)

    def test_exporta_um_relatorio_fechado_sem_sobrescrever_outro(self):
        diario = Diario("singularidade", 43)
        diario.observar(0, valores())
        diario.registrar_operacao(0.2, "estabilizar", valores(contencao=60))
        diario.observar(1, valores(), True, 1)
        diario.finalizar(1.2, "colapso", valores(contencao=0))
        # Chamadas posteriores ao término não mudam o relatório.
        diario.observar(5, valores(temperatura=100), True, 4)
        diario.finalizar(5, "vitoria", valores())
        with tempfile.TemporaryDirectory() as pasta:
            primeiro = diario.salvar(Path(pasta) / "diarios")
            segundo = diario.salvar(Path(pasta) / "diarios")
            self.assertNotEqual(primeiro, segundo)
            dados = json.loads(primeiro.read_text(encoding="utf-8"))
            self.assertEqual(dados["resultado"], "colapso")
            self.assertEqual(dados["duracao_segundos"], 1.2)
            self.assertEqual(dados["tempo_em_equilibrio_segundos"], 1)
            self.assertEqual(dados["menor_contencao"], 0)
            self.assertEqual(dados["operacoes"][0]["acao"], "estabilizar")
            self.assertEqual(dados["amostras"][-1]["segundos"], 1.2)

    def test_tentativa_em_andamento_nao_e_exportada_como_concluida(self):
        with tempfile.TemporaryDirectory() as pasta:
            with self.assertRaises(ValueError):
                Diario("estrela", 1).salvar(pasta)
            self.assertEqual(list(Path(pasta).iterdir()), [])

    def test_comandos_do_jogo_chegam_ao_diario_pelo_clique(self):
        jogo = Jogo(semente=43)
        jogo.iniciar_experimento("quantico")
        jogo.tratar_evento(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=jogo.botao_energia.retangulo.center
        ))
        jogo.atualizar(2)
        self.assertEqual(jogo.diario.operacoes[0]["acao"], "aumentar_energia")
        self.assertEqual(jogo.diario.operacoes[0]["segundos"], 0)
        self.assertGreater(jogo.diario.operacoes[0]["energia"], 35)
        self.assertAlmostEqual(jogo.tempo, 2)

    def test_final_automatico_e_comparacao_entre_tentativas(self):
        jogo = Jogo(semente=43)
        jogo.iniciar_experimento("estrela")
        jogo.temperatura = 99.999
        jogo.atualizar(1 / 60)
        anterior = jogo.diario
        self.assertEqual(anterior.resultado, "superaquecimento")
        jogo.iniciar_experimento("singularidade")
        self.assertIsNone(jogo.diario_anterior)
        jogo.iniciar_experimento("estrela")
        self.assertIs(jogo.diario_anterior, anterior)
        self.assertEqual(jogo.diario.amostras[0]["segundos"], 0)
        self.assertEqual(jogo.diario.tempo_em_equilibrio, 0)

    def test_semente_sorteada_pode_ser_reproduzida(self):
        original = Jogo()
        original.iniciar_experimento("estrela")
        repeticao = Jogo(semente=original.diario.semente)
        repeticao.iniciar_experimento("estrela")
        for jogo in (original, repeticao):
            jogo.aumentar_energia()
            jogo.atualizar(10)
        self.assertEqual(original.leituras(), repeticao.leituras())

    def test_erro_ao_salvar_permite_nova_tentativa(self):
        jogo = Jogo(semente=43)
        jogo.iniciar_experimento("estrela")
        jogo.temperatura = 100
        jogo.verificar_final()
        with patch.object(jogo.diario, "salvar", side_effect=PermissionError):
            jogo.salvar_diario()
        self.assertIn("Não foi possível", jogo.aviso_diario)
        self.assertTrue(jogo.botao_salvar.ativo)
        with tempfile.TemporaryDirectory() as pasta:
            salvar = jogo.diario.salvar
            with patch.object(jogo.diario, "salvar", side_effect=lambda: salvar(pasta)):
                jogo.salvar_diario()
            self.assertFalse(jogo.botao_salvar.ativo)
            self.assertEqual(len(list(Path(pasta).glob("*.json"))), 1)
        jogo.iniciar_experimento("estrela")
        self.assertTrue(jogo.botao_salvar.ativo)

    def test_outros_comandos_nao_mudam_a_sequencia_dos_eventos(self):
        tentativas = [Jogo(semente=43), Jogo(semente=43)]
        for jogo in tentativas:
            jogo.iniciar_experimento("estrela")
        tentativas[1].resfriar()
        tentativas[1].estabilizar()
        for jogo in tentativas:
            jogo.atualizar(20)
        eventos = [
            [(op["segundos"], op["acao"]) for op in jogo.diario.operacoes
             if op["acao"].startswith("evento:")]
            for jogo in tentativas
        ]
        self.assertGreaterEqual(len(eventos[0]), 2)
        self.assertEqual(*eventos)


if __name__ == "__main__":
    unittest.main()
