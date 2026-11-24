import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


CAMPOS = ("temperatura", "energia", "estabilidade", "contencao", "anomalia", "progresso")


class Diario:
    def __init__(self, experimento, semente):
        self.experimento = experimento
        self.semente = semente
        self.inicio = datetime.now(timezone.utc)
        self.amostras = []
        self.operacoes = []
        self.tempo_em_equilibrio = 0
        self.pico_temperatura = 0
        self.menor_contencao = 100
        self.proxima_amostra = 0
        self.resultado = None
        self.duracao = 0

    def _leitura(self, segundos, valores):
        return {"segundos": round(segundos, 4), **{
            campo: round(valores[campo], 4) for campo in CAMPOS
        }}

    def _acompanhar_extremos(self, valores):
        self.pico_temperatura = max(self.pico_temperatura, valores["temperatura"])
        self.menor_contencao = min(self.menor_contencao, valores["contencao"])

    def observar(self, segundos, valores, em_equilibrio=False, delta=0):
        if self.resultado is not None:
            return
        self._acompanhar_extremos(valores)
        if em_equilibrio:
            self.tempo_em_equilibrio += delta
        if segundos + 1e-9 >= self.proxima_amostra:
            self.amostras.append(self._leitura(segundos, valores))
            self.proxima_amostra = int(segundos + 1e-9) + 1

    def registrar_operacao(self, segundos, acao, valores):
        if self.resultado is not None:
            return
        self._acompanhar_extremos(valores)
        leitura = self._leitura(segundos, valores)
        self.operacoes.append({"acao": acao, **leitura})
        # Preserva também picos breves provocados por um comando.
        self.amostras.append(leitura)

    def finalizar(self, segundos, resultado, valores):
        if self.resultado is not None:
            return
        self._acompanhar_extremos(valores)
        leitura = self._leitura(segundos, valores)
        if not self.amostras or self.amostras[-1] != leitura:
            self.amostras.append(leitura)
        self.duracao = segundos
        self.resultado = resultado

    def dados(self):
        return {
            "versao": 1,
            "experimento": self.experimento,
            "semente": self.semente,
            "iniciado_em_utc": self.inicio.isoformat(),
            "resultado": self.resultado,
            "duracao_segundos": round(self.duracao, 4),
            "tempo_em_equilibrio_segundos": round(self.tempo_em_equilibrio, 4),
            "pico_temperatura": round(self.pico_temperatura, 4),
            "menor_contencao": round(self.menor_contencao, 4),
            "amostras": self.amostras,
            "operacoes": self.operacoes,
        }

    def salvar(self, pasta=None):
        if self.resultado is None:
            raise ValueError("Conclua o experimento antes de salvar o diário.")
        destino = Path(pasta) if pasta is not None else Path.home() / "QuantumControlRoom" / "diarios"
        destino.mkdir(parents=True, exist_ok=True)
        nome = f"{self.inicio:%Y%m%dT%H%M%SZ}_{self.experimento}_{uuid4().hex[:8]}.json"
        arquivo = destino / nome
        with arquivo.open("x", encoding="utf-8") as saida:
            json.dump(self.dados(), saida, ensure_ascii=False, indent=2, allow_nan=False)
            saida.write("\n")
        return arquivo
