# AgroSmart Sprint 7 — estado da entrega em 24/11/2026

Pacote técnico da Fase 7 montado sobre a base integrada da Fase 6. O prazo e o enunciado da atividade da Fase 7 não foram conferidos no portal durante esta montagem: confirmar antes de submeter.

## Nossa implementação técnica

- [x] **Item 1, arquitetura final:** SVG/PNG e descrição com sete faixas (fontes, ingestão, processamento, automação, visualização, execução e monitoramento, CI/CD), coerentes com o fluxo efetivo e com os limites declarados.
- [x] **Item 2, execução da plataforma:** `pipeline.py` executado; log real, exemplos reais de entrada e saída e totais em `docs/execucao_plataforma.md` e `docs/evidencias_execucao/`.
- [x] **Item 3, pipeline DevSecOps:** workflow, Dockerfile (usuário sem privilégios), `.dockerignore`, `ruff.toml` e dependências separadas. Ruff e Bandit passam localmente.
- [x] **Item 4, monitoramento e execução automatizada:** executor com logs, eventos JSON, status, histórico, painel HTML, trava de execução e código de saída; 3 ciclos saudáveis e uma falha provocada, com prints.
- [x] **Item 5, análise de processo e demonstração final:** `docs/analise_processo.md`, com problemas, resultados medidos, aprendizados e roteiro da demonstração ao vivo.
- [x] **Item 6, pitch:** `PITCH.md`, com roteiro de 3 minutos, seis slides sugeridos e perguntas prováveis.
- [x] 30 testes aprovados (13 da Fase 6, 17 do monitoramento), em Python 3.12.3 com pandas 2.3.3.
- [x] Dados processados e dashboard idênticos aos da Fase 6 (comparação byte a byte, sem contar quebra de linha): o fluxo de dados não foi alterado.
- [x] Contribuições de Joy e Zerlin preservadas e atribuídas; documentos da Fase 6 mantidos em `docs/fase6/`.

## O que ainda não está comprovado

- [ ] **GitHub Actions:** não há print da aba *Actions* com o workflow verde. A evidência atual é uma simulação local das mesmas etapas (`docs/evidencias_execucao/simulacao_local_ci.txt`), declarada como tal.
- [ ] **Docker:** `docker build` e `docker run` não foram executados na verificação (sem Docker disponível). O Dockerfile foi revisado, mas não testado aqui.
- [ ] **Painel do dashboard:** as capturas de `dashboard/prints/` são da versão anterior (Chart.js), rotuladas em `dashboard/prints/LEIA_ME.md`. Uma captura nova do HTML offline ainda não existe.
- [ ] **Gravação:** o pitch e a demonstração final têm roteiro, mas não foram gravados nem ensaiados. O vídeo narrado da Fase 6 não faz parte deste pacote.

## Etapa final: equipe, aprovação e submissão

- [ ] Confirmar responsáveis de cada item da Fase 7 (a tabela do README só nomeia quem consta nos documentos originais).
- [ ] Conferir a composição do grupo no portal (a Fase 6 mostrava apenas Aldrin no Grupo 73).
- [ ] Anexar print do workflow verde e a saída de `docker build`/`docker run` a `docs/evidencias_execucao/`.
- [ ] Preencher o voto de `AUTOAVALIACAO.md`.
- [ ] Rodar pipeline, executor e testes uma última vez, remontar o ZIP (`python entrega/montar_zip.py`) e conferir o prazo.
- [ ] Enviar ao grupo e submeter no portal somente após aprovação; guardar o recibo.

ZIP técnico local: `entrega/AldrinDaSilvaRodrigues_RM551679_4ESOA_fase7_atividade.zip`. Tamanho e hash dependem do estado final dos arquivos e devem ser conferidos após a última montagem.
