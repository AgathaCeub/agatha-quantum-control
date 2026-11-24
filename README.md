# Ágatha · Quantum Control Room

Uma sala de comando para brincar com uma ideia: o que acontece quando tento controlar algo que não para de mudar?

O jogo tem três cenários: reator estelar, singularidade e núcleo quântico. A operação depende de energia, temperatura, estabilidade, contenção e anomalia. Chegar a 100% de progresso exige cuidar dessas leituras ao mesmo tempo.

É um jogo de ficção científica em Python e Pygame. Os indicadores são regras do jogo, não grandezas de uma simulação física.

## Rodar

Python 3.10 ou mais recente:

```sh
python -m pip install -r requirements.txt
python main.py
```

Os controles estão nos botões da sala. Para repetir uma sequência de eventos ao reiniciar:

```sh
python main.py --semente 43
```

Com a mesma semente e as mesmas ações nos mesmos instantes, o experimento se repete. As partículas decorativas continuam livres.

## Uma decisão do jogo

A simulação avança em passos de 1/60 de segundo. Antes, as leituras mudavam a cada quadro: um computador mais lento também deixava o experimento mais lento. Agora, a renderização e o tempo do experimento podem seguir ritmos diferentes. Cada próximo evento recebe seu intervalo uma única vez, entre 7 e 12 segundos.

Os testes comparam os mesmos vinte segundos em 30, 60 e 144 FPS, além de quadros irregulares:

```sh
python -m unittest discover -s tests -v
```
