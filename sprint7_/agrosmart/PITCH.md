# AgroSmart — Pitch (item 6, Fase 7)

Duração sugerida: 3 minutos. Cada bloco tem a fala e o que aparece na tela. Todos os números são do cenário sintético da Fazenda Pedralva e foram conferidos nos CSVs e nos logs do pacote.

## Roteiro

**1. O problema (0:00–0:25)** · tela: título
"Um produtor com vários talhões descobre que o solo secou quando a planta já sofre. As leituras existem, mas ninguém olha todas, todos os dias, e não há uma regra clara para decidir. O AgroSmart transforma leitura de sensor em decisão registrada."

**2. A solução (0:25–1:00)** · tela: `docs/arquitetura.png`
"Do sensor ao painel num fluxo só. O nó Arduino simulado no TinkerCad e os sensores de campo alimentam o processamento, que descarta o que é impossível. Um motor de regras classifica o risco e propõe a ação. O painel mostra tudo, funciona offline e é refeito a cada execução."

**3. Resultado real (1:00–1:35)** · tela: dashboard
"Foram 397 leituras. 394 válidas e 3 descartadas, 0,76%, cada uma registrada com o motivo. No campo, 84 de 360 leituras ficaram em alerta: 38 de risco alto e 46 moderados. O Talhão 03, sem irrigação, chegou a 6,1% de umidade e passou 18 leituras seguidas abaixo do limite crítico. Os talhões irrigados ficaram com mínimas entre 20,3% e 21,7%. É um cenário sintético: descreve, não prova causa."

**4. Execução automatizada e monitoramento (1:35–2:15)** · tela: `status.html`
"Ninguém precisa rodar script na mão. O executor roda as quatro etapas, mede cada uma, grava log e decide se o ciclo está saudável por seis verificações: etapas, saídas atualizadas, descarte, leituras sem dados, alertas e duração. Em três ciclos seguidos, tudo SAUDÁVEL, em cerca de um segundo cada. E provamos a falha: removemos uma coluna do dado bruto, e o sistema parou na etapa certa, emitiu alerta e devolveu código 1."

**5. DevSecOps (2:15–2:40)** · tela: `ci.yml`
"A cada push, o GitHub Actions roda Ruff para qualidade, Bandit para segurança, o executor e 30 testes, e guarda os logs como artefato. Depois constrói a imagem Docker e executa o container sem privilégios de administrador."

**6. Limites e próximo passo (2:40–3:00)** · tela: arquitetura
"Somos honestos sobre os limites: dados sintéticos, ações só propostas em CSV, monitoramento em lote, sem notificação externa. O próximo passo é MQTT real, cadastro de atuadores, notificação de falhas e revisão agronômica das regras antes de qualquer comando real. Obrigado."

## Slides sugeridos (6)

1. AgroSmart: da leitura do sensor à decisão (título e equipe)
2. O problema e a ideia
3. Arquitetura final (`docs/arquitetura.png`)
4. Resultados: 394 válidas, 3 descartes, 84 alertas em campo, Talhão 03
5. Execução monitorada e DevSecOps (print do painel `status.html` e do workflow)
6. Limites e próximos passos

## Perguntas prováveis

| Pergunta | Resposta apoiada no pacote |
|---|---|
| Os dados são reais? | Não. Campo sintético (balanço hídrico simples) e bancada simulada no TinkerCad. Está declarado em todos os documentos |
| O sistema aciona a irrigação? | Não. A ação é uma proposta registrada em CSV. Nenhum comando de bomba ou mensagem é executado |
| Como sabem que o monitoramento funciona? | Três ciclos saudáveis registrados e uma falha provocada de propósito que gerou ALERTA e código 1 |
| De onde vêm os limites 18% e 22%? | São adaptações didáticas do cenário local, iguais no Arduino e no Python. Não são parâmetros agronômicos validados |
| O que o CI não cobre? | Dependências e imagem não são varridas e não há deploy. A análise de segurança cobre o código-fonte (Bandit) |
| Isso é monitoramento em tempo real? | Não. É em lote: cada ciclo reprocessa os CSVs. Em tempo real exigiria MQTT e um processo residente |
