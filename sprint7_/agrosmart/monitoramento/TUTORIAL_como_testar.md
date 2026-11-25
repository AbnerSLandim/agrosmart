# Tutorial — como testar o Monitoramento e Execução Automatizada (AgroSmart, Fase 7)

Tempo: cerca de 5 minutos. Você precisa de **Python 3.10 ou mais novo**. Tudo já está no projeto: não há nada para copiar.

## Passo 1 — Preparar

1. Descompacte o zip e abra um terminal na pasta `agrosmart`.
2. Instale a dependência:
   ```
   python -m pip install -r requirements.txt
   ```
   > No Windows, se `python` não for reconhecido, use `py` no lugar.

## Passo 2 — Executar o pipeline monitorado

```
python monitoramento/executor.py --ciclos 3 --intervalo 2
```

**O que você deve ver:** 3 ciclos seguidos. Em cada um, as 4 etapas (Ingestão TinkerCad, Processamento, Automação, Dashboard) aparecem como *iniciada* e *concluída*, depois a lista de verificações e a linha final:

```
===== Ciclo 1: SAUDÁVEL em 1.2 s =====
```

Na verificação de taxa de descarte, deve aparecer `0.76%`, e na de leituras de campo em alerta, `23.33%` (são os mesmos números da Fase 6: 394 leituras válidas, 3 descartes, 84 alertas em campo). A duração varia de máquina para máquina.

O comando termina com código de saída 0.

## Passo 3 — Conferir o que foi gerado

Dentro de `monitoramento/` devem existir:

| Arquivo | O que é |
|---|---|
| `logs/agrosmart.log` | log legível de todos os ciclos |
| `logs/eventos.jsonl` | um evento JSON por etapa e por ciclo |
| `status.json` | estado do último ciclo |
| `historico_execucoes.csv` | uma linha por ciclo (deve ter 3 linhas de dados) |
| `status.html` | painel visual |

Veja o resumo no terminal:
```
python monitoramento/executor.py --status
```
Deve mostrar `Situação: SAUDÁVEL`, as 4 etapas com `OK` e as verificações.

Abra `monitoramento/status.html` no navegador (clique duas vezes no arquivo). Você verá o selo **SAUDÁVEL**, os cartões de indicadores (394 leituras válidas, 3 descartes, 84 alertas em campo), a tabela de etapas, as verificações e as últimas execuções. O print `monitoramento/evidencias/print_painel_status_saudavel.png` mostra como deve ficar.

## Passo 4 — Rodar os testes automatizados

```
python -m unittest tests.test_monitoramento -v
```

**Esperado:** `Ran 17 tests` e `OK`. Faça o Passo 2 antes, porque um dos testes confere os indicadores contra os arquivos que o pipeline gera.

## Passo 5 — Provar que o monitoramento detecta falhas (opcional)

Faça numa **cópia** da pasta `agrosmart` (copie e cole a pasta), para não estragar o projeto.

1. Abra `dados/brutos/leituras_sensores.csv` e apague a coluna `umidade_solo_pct` (a coluna inteira, incluindo o cabeçalho).
2. Rode:
   ```
   python monitoramento/executor.py
   ```

**Esperado:**
- uma linha `ERROR` em *Processamento: FALHOU* com a mensagem `colunas obrigatórias ausentes: ['umidade_solo_pct']`;
- `Pipeline interrompido em 'Processamento'`;
- verificações em `ALERTA` e a linha final `ATENÇÃO`;
- código de saída 1 (Linux/macOS: `echo $?`; Windows: `echo %errorlevel%`);
- no `status.html`, o selo vermelho **ATENÇÃO** e a etapa Processamento com **FALHA**.

O arquivo `evidencias/log_falha_simulada.txt` e o print `evidencias/print_painel_status_falha_simulada.png` mostram exatamente esse resultado.

## Passo 6 — Modo contínuo e agendamento (opcional)

- Repetir a cada 15 minutos até apertar Ctrl+C:
  ```
  python monitoramento/executor.py --continuo --intervalo 900
  ```
- Para agendar sem deixar o terminal aberto, use o cron (Linux) ou o Agendador de Tarefas (Windows); os comandos de exemplo estão no documento `MONITORAMENTO.md`, seção 5.

---

## Problemas comuns

| Sintoma | Causa provável | Solução |
|---|---|---|
| `ModuleNotFoundError: pandas` | dependência não instalada | `python -m pip install -r requirements.txt` |
| `Script não encontrado` no log | rodou fora da pasta do projeto ou o projeto não é o da Fase 6 | rode a partir da pasta `agrosmart` que tem `pipeline.py` |
| Teste `indicadores_batem_com_pipeline` falha | pipeline ainda não rodou ou os dados foram alterados | rode o Passo 2 de novo com os dados originais |
| `Ciclo não iniciado: outra execução em andamento` | sobrou o arquivo `monitoramento/.execucao.lock` de uma execução interrompida | apague esse arquivo (ou espere 10 minutos) |
| Painel não atualiza | o `status.html` é estático | rode o executor de novo e recarregue a página |
