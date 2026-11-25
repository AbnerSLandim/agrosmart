/*
  AgroSmart - nó de sensores (simulação no TinkerCad)

  Componentes:
    - Arduino Uno R3
    - Sensor de umidade do solo  -> SIG em A0 (VCC no pino 7, ligado só na hora da leitura)
    - Sensor de temperatura TMP36 -> Vout em A1
    - LED verde (situação normal)    -> pino 12 (resistor 220 ohm)
    - LED amarelo (risco moderado)   -> pino 11 (resistor 220 ohm)
    - LED vermelho (risco alto)      -> pino 10 (resistor 220 ohm)
    - Buzzer piezo (alerta sonoro)   -> pino 9

  A cada leitura o Arduino envia uma linha CSV pela serial:
    sensor_id,umidade_solo_pct,temperatura_solo_c,nivel_risco
  Essas linhas são copiadas do Monitor Serial para
  dados/brutos/serial_tinkercad.txt e entram no pipeline Python
  por sensores/ingestao_tinkercad.py.

  As regras são as mesmas da automação em Python (src/automacao.py):
    umidade < 18%  ou temperatura >= 35 C -> ALTO
    umidade < 22%  ou temperatura >= 30 C -> MODERADO
*/

const char* SENSOR_ID = "SM-TKC-001";

const int PINO_UMIDADE = A0;
const int PINO_ALIMENTACAO_UMIDADE = 7;
const int PINO_TEMPERATURA = A1;
const int LED_VERDE = 12;
const int LED_AMARELO = 11;
const int LED_VERMELHO = 10;
const int BUZZER = 9;

// O sensor de umidade do TinkerCad vai de 0 (seco) a ~876 (encharcado) com 5 V
const int LEITURA_MAXIMA_UMIDADE = 876;

const float UMIDADE_CRITICA = 18.0;
const float UMIDADE_BAIXA = 22.0;
const float TEMPERATURA_ALTA = 35.0;
const float TEMPERATURA_ATENCAO = 30.0;

const unsigned long INTERVALO_MS = 2000;

float lerUmidade() {
  // Alimenta o sensor só durante a leitura (reduz corrosão no sensor real)
  digitalWrite(PINO_ALIMENTACAO_UMIDADE, HIGH);
  delay(10);
  int bruto = analogRead(PINO_UMIDADE);
  digitalWrite(PINO_ALIMENTACAO_UMIDADE, LOW);
  return constrain(bruto * 100.0 / LEITURA_MAXIMA_UMIDADE, 0.0, 100.0);
}

float lerTemperatura() {
  // TMP36: 10 mV por grau, com 500 mV de offset
  int bruto = analogRead(PINO_TEMPERATURA);
  float tensao = bruto * 5.0 / 1023.0;
  return (tensao - 0.5) * 100.0;
}

const char* classificarRisco(float umidade, float temperatura) {
  if (umidade < UMIDADE_CRITICA || temperatura >= TEMPERATURA_ALTA) return "Alto";
  if (umidade < UMIDADE_BAIXA || temperatura >= TEMPERATURA_ATENCAO) return "Moderado";
  return "Normal";
}

void sinalizar(const char* risco) {
  bool alto = strcmp(risco, "Alto") == 0;
  bool moderado = strcmp(risco, "Moderado") == 0;
  digitalWrite(LED_VERMELHO, alto);
  digitalWrite(LED_AMARELO, moderado);
  digitalWrite(LED_VERDE, !alto && !moderado);
  if (alto) {
    tone(BUZZER, 1000, 300);
  }
}

void setup() {
  Serial.begin(9600);
  pinMode(PINO_ALIMENTACAO_UMIDADE, OUTPUT);
  pinMode(LED_VERDE, OUTPUT);
  pinMode(LED_AMARELO, OUTPUT);
  pinMode(LED_VERMELHO, OUTPUT);
  pinMode(BUZZER, OUTPUT);
  Serial.println("sensor_id,umidade_solo_pct,temperatura_solo_c,nivel_risco");
}

void loop() {
  float umidade = lerUmidade();
  float temperatura = lerTemperatura();
  const char* risco = classificarRisco(umidade, temperatura);

  sinalizar(risco);

  Serial.print(SENSOR_ID);
  Serial.print(",");
  Serial.print(umidade, 1);
  Serial.print(",");
  Serial.print(temperatura, 1);
  Serial.print(",");
  Serial.println(risco);

  delay(INTERVALO_MS);
}
