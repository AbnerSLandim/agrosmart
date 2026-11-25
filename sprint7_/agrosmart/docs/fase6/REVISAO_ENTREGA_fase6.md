# Revisão técnica AgroSmart — 08/10/2026

Revisão na cópia editável `C:/_obsidian/_work/agrosmart-20261008`. Nenhuma alteração ao original `C:/dev/fiap-fase6/agrosmart`, nenhum entregável enviado ao WhatsApp, nenhuma submissão realizada. A atividade do portal já foi conferida pela coordenação desta revisão: [FIAP, atividade 641916](https://on.fiap.com.br/mod/assign/view.php?id=641916&returnto=conteudocurso), prazo 10/10/2026 às 23h59; dashboard em ferramenta equivalente aceito; vídeo de 3–5 min obrigatório, 20%.

## Matriz requisito × evidência

| Item do enunciado | Evidência presente no ZIP técnico | Verificação e estado |
|---|---|---|
| 1. Arquitetura e componentes | `docs/arquitetura.md`, `arquitetura.svg`, `arquitetura.png` | Fluxo efetivo, responsabilidades, dependências e limitações documentados. SVG/PNG atualizado e inspecionado; clima fica fora do pipeline atual. Pronto. |
| 2. IoT/TinkerCad, prints, sensores, exemplo de dados | `sensores/tinkercad/agrosmart_sensores.ino`, `sensores/descricao_sensores.md`, cinco imagens em `sensores/prints/`, serial e CSV de bancada em `dados/brutos/` | Capturas de circuito/Normal/Moderado/Alto/calor preservadas; umidade/temperatura, pinos, conversões e saída explicados. Concordância das 34 observações serial com Python: zero divergências. Sketch não foi recompilado ou nova simulação executada nesta revisão. Buzzer codificado; captura não comprova áudio. Material pronto, com esses limites explícitos. |
| 3. Processamento: código, dataset, explicação | `src/processamento.py`, `dados/brutos/`, `dados/processados/dataset_processado_agrosmart.csv`, `registros_descartados.csv`, catálogo e arquitetura | Pipeline executado: 397 entradas, 394 válidas, 3 descartes auditáveis. Testes de esquema, limites físicos, datas e identificação. Dados de campo sintéticos. Pronto. |
| 4. Automação: regras, código e saída | `src/automacao.py`, `resultado_automacao_agrosmart.csv`, `resumo_talhoes.csv`, `insights_automaticos.csv` | Estrutura de Joy adaptada: limites locais 18/22% e 30/35 °C coerentes entre Python, Arduino, docs e testes; não afirmar que parâmetros originais de Joy foram mantidos. Testes de bordas e dos dois caminhos de ação. Todos os riscos altos reais deste lote propõem Notificar produtor; Acionar irrigação é coberto por teste controlado. Saídas em CSV, sem controle físico/envio externo. Pronto. |
| 5. Dashboard: arquivo/link equivalente, indicadores e capturas | `dashboard/agrosmart_dashboard.html`, `gerar_dashboard.py`, `descricao_indicadores.md`, `prints/` e guia opcional Power BI | HTML + SVG autônomo, sem internet/JS; três SVGs parseados e figuras renderizadas/inspecionadas. KPIs de campo 360/38/46, bancada 34. Capturas existentes da versão anterior são compatíveis nos números e rotuladas; faltam screenshots da nova apresentação offline. A equipe pode produzi-los junto ao vídeo. Código/dados/painel prontos; limitação de captura declarada. |
| 6. Vídeo de 3–5 min (obrigatório, 20%) | `entrega/AgroSmart_Sprint6_video.mp4`, `VIDEO.md` e fontes em `video/` | Versão narrada sintética gerada em 09/10/2026: 4min09s, 1280×720, 24 fps, áudio presente e sete telas inspecionadas. Daniel havia assumido uma gravação humana, mas esta versão é independente e não se passa por ele. **Pronto tecnicamente; pendente aprovação de Aldrin e acesso do avaliador.** |
| Identidade/organização final | Nome confirmado: `AldrinDaSilvaRodrigues_RM551679_4ESOA_fase6_atividade.zip`; estado e autoavaliação | Empacotador valida itens, prefixo e CRC; exclui Git/caches/ZIPs aninhados. Grupo 73 observado com apenas Aldrin: integrantes dependem de conferência e aprovação. Aprovação/envio/submissão pendentes. |

## Execução e critérios verificados

Ambiente utilizado: Python 3.11.5, pandas 2.1.3. Reprodução:

```bash
python -m pip install -r requirements.txt
python pipeline.py
python -m unittest discover -s tests -v
python entrega/montar_zip.py
```

Resultado do pipeline: 394 leituras válidas (360 campo + 34 bancada), 3 descartes; Normal 289/Moderado 56/Alto 49 no total. Campo: 38 altos e 46 moderados, 84/360 = 23,33%. Umidade média 32,1%; Talhão 03 mínimo 6,1%, 18 leituras diárias críticas consecutivas. Insights e KPIs excluem bancada, barras/resumo a identificam. Saídas antigas do catálogo foram corrigidas para esses números.

**13 testes executados e aprovados** (`unittest`, 0,344 s na última execução): dados entregues/descartes; coluna ausente; datas/identificação; limites físicos; reprodução dos CSVs pela semente; limites de risco e dados parciais (também comparando constantes do Arduino); dois caminhos de ação; concordância serial/Python; rejeição de serial malformado/não finito; totais/KPIs; SVG/HTML offline e correspondência do arquivo gerado; escape de conteúdo; seleção do pacote/prefixo e rejeição de item obrigatório ausente. A primeira execução revelou HTML ainda não regenerado após o ajuste final de ticks; foi regenerado antes da execução final. Tamanho/hash do ZIP informados no handoff após congelar os arquivos.

## Contribuições e preservação

Joy: base revisada anteriormente pela coordenação em [AbnerSLandim/agrosmart](https://github.com/AbnerSLandim/agrosmart), commit `0c6cbfe8a52a42c8a99b4428da243a0dbcac6665`. Estrutura de processamento/classificação/alertas/recomendações adaptada ao cenário local, com umidade crítica 18% e baixa 22%; os parâmetros originais de umidade não foram mantidos. Esta etapa confirmou a coerência dos parâmetros locais entre sketch/Python/docs/testes. Nova leitura remota falhou (cache indisponível/DNS), portanto não transcreve os parâmetros de Joy como revalidados agora. Validação física/rastreabilidade/consolidação acrescidas. Recomendação moderada de solo seco sem irrigação reconhece essa limitação. Leituras parciais sem condição observável de alerta ficam em Sem dados.

Zerlin: seis arquivos preservados em `dashboard/powerbi_versao_inicial/` (PBIX, ODT, quatro imagens); SHA256 já comparado com a cópia recebida em Downloads, sem divergências. O PBIX usa outro dataset/luminosidade; não foi atualizado nem apresentado como painel final. A nota de procedência e o guia opcional acompanham o pacote.

## Limitações e checklist restante

Horários da bancada sintéticos (passos de 1 h, Arduino a cada 2 s), ingestão manual, dados de campo sintéticos, inferência de talhão irrigado pelo lote inteiro, regras didáticas e ações apenas propostas em CSV. Comparação descritiva de talhões, sem alegar causalidade. MQTT é exemplo de payload, não um serviço implementado.

A tentativa de nova captura no navegador foi rejeitada por política de URL `file://`. Não houve contorno por servidor, outra superfície ou comando de navegador. Figuras locais SVG/PNG são alternativa de QA, identificadas como figuras; não foram chamadas de screenshots. Estrutura/conteúdo do HTML foram testados, mas layout integral no navegador atual não foi observado nesta revisão. Capturas novas devem ser feitas pelo integrante que grava.

Nossa implementação editável local está fechada; permanecem a nova captura visual, gravação/link do vídeo por Daniel, composição do grupo, aprovação final, envio e submissão. A atribuição do vídeo está resolvida; sua execução ainda não está comprovada. Detalhamento em `ESTADO_ENTREGA.md`. Não apagar ou tratar como resolvidas essas pendências para declarar entrega acadêmica completa.
