# Demonstração da plataforma — item 6 obrigatório, 20%

Arquivo do vídeo: [`entrega/AgroSmart_Sprint6_video.mp4`](entrega/AgroSmart_Sprint6_video.mp4). Versão gerada em 09/10/2026, com **4min09s**, resolução **1280×720**, narração sintética em português e sete telas montadas a partir das evidências reais do projeto. O arquivo foi reproduzido tecnicamente, tem faixa de áudio e está dentro da duração exigida de 3–5 minutos. Ainda depende da aprovação final de Aldrin antes do envio ou da submissão acadêmica.

Daniel havia assumido a gravação humana no grupo em 08/10/2026 às 20h34. A versão sintética foi criada para retirar o bloqueio da entrega sem se passar por uma gravação dele; ela se apresenta apenas como demonstração narrada da solução.

## Como regenerar

1. Gere os WAVs com `powershell -ExecutionPolicy Bypass -File video/gerar_audio.ps1` em Windows com a voz `Microsoft Maria Desktop` instalada.
2. Instale `moviepy`, `Pillow` e `imageio-ffmpeg`, depois execute `python video/render_video.py`.
3. O roteiro estruturado está em `video/narracao.json`. `video/audio/`, `video/frames/` e `video/previews/` são artefatos temporários ignorados pelo Git.

## Roteiro de tela e fala

| Tempo | Tela | Fala e evidência |
|---|---|---|
| 0:00–0:40 | `docs/arquitetura.png` | "O AgroSmart integra coleta simulada, processamento, motor de regras e dashboard. O campo é um cenário sintético de quatro talhões de soja. A bancada TinkerCad valida o nó Arduino. A passagem serial para Python é manual e auditável." Aponte que clima e produtividade são contexto, não entradas das regras atuais. |
| 0:40–1:30 | Circuito/Monitor Serial e `sensores/prints/` | Mostre solo úmido (72%, Normal), secando (18,9%, Moderado), seco (0%, Alto) e calor (88,6%, 54,1°C, Alto). Relacione LEDs verde/amarelo/vermelho e buzzer do sketch. "O serial entregue reúne 34 observações a 27,2°C; as capturas de calor são outro cenário. Horários da bancada no CSV são sintéticos, só para ordenação." |
| 1:30–2:25 | Terminal executando `python pipeline.py`, CSV de descartes | "Um comando percorre quatro etapas. O dataset bruto tem 363 registros de campo e 34 de bancada. Remove duplicata, umidade impossível e sensor sem medição; ficam 394 válidos. Não interpolamos os descartes. A automação gera as saídas consumidas pelo painel." Mostre 3 motivos e arquivos gerados. |
| 2:25–3:05 | `src/automacao.py` e CSV de resultados | "Adaptamos a estrutura de regras de Joy ao cenário local. Alto: umidade abaixo de 18% ou temperatura a partir de 35 °C. Moderado: abaixo de 22% ou a partir de 30 °C. Alto em talhão irrigado propõe acionar irrigação; em talhão não irrigado propõe notificar. São propostas em CSV; não acionamos bomba nem enviamos mensagens." Mostre saída real de Notificar produtor e explique que o outro ramo foi testado com cenário controlado. |
| 3:05–4:00 | `dashboard/agrosmart_dashboard.html` | Mostre as quatro seções. "Os KPIs excluem bancada: 360 leituras de campo, 4 talhões, 32,1% de umidade média, 38 riscos altos e 46 moderados. Com bancada, o total é 49 altos e 56 moderados. Norte chegou a 6,1%, com 18 leituras diárias críticas consecutivas. Os insights vêm dos CSVs e descrevem o cenário, não provam causalidade." Mostre que HTML/SVG abre offline; barras/resumo incluem bancada identificada. |
| 4:00–4:15 | Diagrama/painel | "Entregamos código, dados, regras, saídas, painel e documentação. Como evolução: ingestão MQTT real, cadastro de atuadores e revisão agronômica. Esta demonstração usa dados sintéticos/simulados, com limitações declaradas." |

## Validação antes de fechar

- [x] Vídeo renderizado; duração real de 4min09s, dentro da faixa de 3–5 min.
- [x] Arquivo 1280×720, 24 fps, H.264/AAC e faixa de áudio presente.
- [x] Sete telas inspecionadas; números e limitações correspondem ao pacote.
- [x] Vídeo incluído no repositório privado e no ZIP técnico verificado.
- [ ] Aldrin assistir e aprovar a versão final.
- [ ] Confirmar que o avaliador terá acesso ao repositório privado ou enviar o MP4 pelo canal aceito.
- [ ] Enviar ao grupo e submeter no portal somente após autorização final.
