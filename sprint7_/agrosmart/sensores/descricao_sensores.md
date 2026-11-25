# Nó de sensores — TinkerCad

## Sensores utilizados

| Sensor | Mede | Pino | Conversão |
|---|---|---|---|
| Sensor de umidade do solo | Umidade do solo (%) | SIG → A0, VCC → pino 7, GND → GND | leitura 0–876 vira 0–100% |
| TMP36 | Temperatura (°C) | Vout → A1, +Vs → 5V, GND → GND | (tensão − 0,5 V) × 100 |

Atuadores de alerta local:

| Componente | Pino | Quando liga |
|---|---|---|
| LED verde + resistor 220 Ω | 12 | risco normal |
| LED amarelo + resistor 220 Ω | 11 | risco moderado |
| LED vermelho + resistor 220 Ω | 10 | risco alto |
| Buzzer piezo | 9 | risco alto (bipe de 300 ms) |

As regras no Arduino são as mesmas da automação em Python: alto se a umidade < 18% ou a temperatura ≥ 35 °C; moderado se a umidade < 22% ou a temperatura ≥ 30 °C.

## Como montar no TinkerCad

1. Em tinkercad.com, abra **Circuitos → Criar novo circuito**.
2. Arraste: Arduino Uno R3, Sensor de umidade do solo, Sensor de temperatura [TMP36], 3 LEDs (verde, amarelo, vermelho), 3 resistores de 220 Ω, Piezo e uma protoboard.
3. Ligue conforme as tabelas acima. Em cada LED, o catodo (perna reta) vai no GND e o anodo vai no resistor, que vai no pino.
4. Em **Código → Texto**, apague tudo e cole o conteúdo de `tinkercad/agrosmart_sensores.ino`.
5. Clique em **Iniciar simulação** e abra o **Monitor serial**.
6. Clique no sensor de umidade e no TMP36 e mova os controles para variar os valores. Passe pelos três cenários: normal (verde), solo secando (amarelo) e solo seco com calor (vermelho + buzzer).
7. Tire os prints: o circuito montado, a simulação rodando com o LED vermelho aceso e o Monitor Serial com as leituras.
8. Copie o texto do Monitor Serial e salve em `dados/brutos/serial_tinkercad.txt`.
9. Rode `python pipeline.py`: as leituras entram como "Talhao 05 - Bancada TinkerCad" e aparecem no dashboard.

Datas/horas de bancada atribuídas pelo script são sintéticas: 02/09/2026 às 10h UTC + 1 h por observação. Servem apenas à ordenação; não representam captura em 03/10/2026 nem o intervalo real de 2 s. KPIs e séries agrícolas excluem a bancada.

## Capturas da simulação

| Print | Cenário | Saída serial | Sinalização |
|---|---|---|---|
| `prints/01_circuito.jpg` | Circuito montado (fios: vermelho 5V, preto GND, laranja alimentação do sensor, amarelo A0, azul A1, verde LEDs, roxo buzzer) | — | — |
| `prints/02_normal_solo_umido.jpg` | Solo úmido | `72.0, 24.8, Normal` | LED verde |
| `prints/03_moderado_solo_secando.jpg` | Solo secando | `18.9, 24.8, Moderado` | LED amarelo |
| `prints/04_alto_solo_seco.jpg` | Solo seco | `0.0, 24.8, Alto` | LED vermelho + buzzer |
| `prints/05_alto_calor.jpg` | Solo úmido, mas calor | `88.6, 54.1, Alto` | LED vermelho + buzzer |

Projeto no TinkerCad: "AgroSmart - No de Sensores" (conta do Aldrin).

## Exemplo de dados gerados

Formato que o Arduino envia (uma linha a cada 2 s):

```
sensor_id,umidade_solo_pct,temperatura_solo_c,nivel_risco
```

Trecho real do Monitor Serial (simulação de 2026-10-03; arquivo completo em `dados/brutos/serial_tinkercad.txt`):

```
SM-TKC-001,72.0,27.2,Normal      ← solo úmido: LED verde
SM-TKC-001,20.9,27.2,Moderado    ← solo abaixo de 22%: LED amarelo
SM-TKC-001,17.9,27.2,Alto        ← solo abaixo de 18%: LED vermelho + buzzer
SM-TKC-001,0.1,27.2,Alto         ← sensor fora da terra (solo seco)
SM-TKC-001,95.1,27.2,Normal      ← solo encharcado
```

O print `05_alto_calor.jpg` documenta outro cenário de calor (88,6% e 54,1 °C, risco Alto). O arquivo serial entregue contém temperatura constante de 27,2 °C; portanto a validação cruzada abaixo cobre variações de umidade. Os limites de temperatura em Python são testados separadamente em `tests/test_integracao.py`. O buzzer está implementado no sketch; capturas estáticas não comprovam áudio.

Validação cruzada: as 34 leituras foram reclassificadas pelo `src/automacao.py` e bateram 100% com a classificação feita no Arduino (0 divergências).
