# Autoavaliação — Fase 7, DevSecOps, monitoramento e entrega final

Data: 24/11/2026. Voto de Aldrin (1–5): **pendente**. Não atribuo nota em nome de ninguém.

## Entrega e evidência

Os seis itens da Fase 7 estão documentados e ligados ao código: arquitetura final, execução da plataforma com saídas reais, pipeline DevSecOps, monitoramento com evidências de sucesso e de falha provocada, análise de processo e pitch. A suíte de 30 testes passa, o Ruff não aponta nada e o Bandit não encontra achados médios ou altos. O fluxo de dados da Fase 6 foi preservado: os CSVs e o dashboard saem idênticos. Matriz por requisito em `REVISAO_ENTREGA.md`.

## Limites e trabalho restante

O workflow do GitHub Actions e o container Docker ainda não têm evidência de execução real: o que existe é uma simulação local das etapas do CI, declarada como tal. O pitch e a demonstração têm roteiro, mas não foram gravados. As capturas do dashboard são da versão anterior. Dados de campo sintéticos, bancada simulada, regras didáticas, ações só propostas em CSV, monitoramento em lote e limites de saúde não calibrados com dados reais. Aprovação final, envio e submissão pendentes.

## Melhoria realizada

Reorganizei a Fase 7 no formato do pacote da Fase 6 (README com itens, estado, revisão, autoavaliação, empacotador e testes). Troquei exemplos e log de execução que não correspondiam aos dados reais por linhas e saída reais do pipeline. Atualizei o diagrama de arquitetura com as faixas de monitoramento e CI/CD, e o empacotador passou a incluir o `.dockerignore`, que o filtro antigo descartaria por começar com ponto. O teste do empacotador deixou de depender do vídeo da Fase 6. Na revisão achei e corrigi uma citação de versão do pandas fora do intervalo do `requirements.txt`.

## Sugestão proativa NÃO executada

Adicionar `pip-audit` (dependências) e uma varredura de imagem Docker (por exemplo Trivy) ao CI, e notificação de falhas do executor. Exige decisão de escopo e acesso ao repositório; não foi implementado nem usado para ampliar esta entrega.
