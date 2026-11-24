import unittest
from unittest.mock import Mock

from main import Jogo, PASSO_SIMULACAO


LEITURAS = ("tempo", "temperatura", "energia", "estabilidade", "contencao", "anomalia", "progresso")


def experimento():
    jogo = Jogo(semente=43)
    jogo.iniciar_experimento("singularidade")
    return jogo


class TempoDoExperimento(unittest.TestCase):
    def test_mesmos_vinte_segundos_em_tres_taxas_de_quadros(self):
        resultados = []
        for fps in (30, 60, 144):
            jogo = experimento()
            for _ in range(20 * fps):
                jogo.atualizar(1 / fps)
            resultados.append(tuple(getattr(jogo, nome) for nome in LEITURAS))
        self.assertEqual(resultados[0], resultados[1])
        self.assertEqual(resultados[0], resultados[2])

    def test_quadro_lento_e_quadro_curto_preservam_o_tempo(self):
        regular = experimento()
        irregular = experimento()
        for _ in range(600):
            regular.atualizar(1 / 60)
        for _ in range(50):
            for delta in (0.003, 0.027, 0.17):
                irregular.atualizar(delta)
        for nome in LEITURAS:
            self.assertEqual(getattr(regular, nome), getattr(irregular, nome), nome)

    def test_resto_de_tempo_passa_para_o_proximo_quadro(self):
        jogo = experimento()
        jogo.atualizar(PASSO_SIMULACAO / 2)
        self.assertEqual(jogo.tempo, 0)
        jogo.atualizar(PASSO_SIMULACAO / 2)
        self.assertEqual(jogo.tempo, PASSO_SIMULACAO)

    def test_menu_e_final_nao_avancam(self):
        jogo = Jogo()
        jogo.atualizar(1)
        self.assertEqual(jogo.tempo, 0)
        jogo.iniciar_experimento("estrela")
        jogo.estado_final = "vitoria"
        jogo.atualizar(1)
        self.assertEqual(jogo.tempo, 0)

    def test_intervalo_do_evento_nao_e_sorteado_a_cada_quadro(self):
        jogo = experimento()
        jogo.sorteio_eventos.uniform = Mock(return_value=9)
        jogo.atualizar(1)
        jogo.sorteio_eventos.uniform.assert_not_called()
        jogo.atualizar(11)
        jogo.sorteio_eventos.uniform.assert_called_once_with(7, 12)

    def test_reiniciar_repete_eventos_e_acoes_da_mesma_semente(self):
        jogo = experimento()
        resultados = []
        for _ in range(2):
            jogo.iniciar_experimento("singularidade")
            jogo.aumentar_energia()
            jogo.resfriar()
            jogo.estabilizar()
            jogo.analisar()
            jogo.atualizar(15)
            resultados.append(tuple(getattr(jogo, nome) for nome in LEITURAS))
        self.assertEqual(*resultados)
        jogo.atualizar(PASSO_SIMULACAO / 2)
        jogo.iniciar_experimento("estrela")
        self.assertEqual(jogo.acumulador, 0)

    def test_delta_invalido_nao_afeta_a_simulacao(self):
        jogo = experimento()
        for delta in (0, -1, float("nan"), float("inf")):
            jogo.atualizar(delta)
        self.assertEqual(jogo.tempo, 0)


if __name__ == "__main__":
    unittest.main()
