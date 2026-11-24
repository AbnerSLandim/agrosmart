# Procedência das imagens do dashboard

`01_visao_geral_monitoramento.png` e `dashboard_completo.png` são capturas já existentes da versão anterior, com Chart.js. Preservam os números revalidados em 08/10/2026: 360 leituras de campo, 34 de bancada, 38 alertas altos, 46 moderados, umidade média de 32,1%, mínimo do Norte de 6,1% e sequência crítica de 18 leituras. Não são capturas da nova versão HTML + SVG offline. O título antigo "Efeito da irrigação" foi corrigido no painel atual para "Comparação entre talhões", sem mudar os números.

`figura_umidade_20261008.png`, `figura_temperatura_20261008.png` e `figura_riscos_20261008.png` são **figuras renderizadas diretamente dos SVGs do HTML atual**, não screenshots de navegador. Foram inspecionadas em 08/10/2026. O gráfico atual de temperatura inclui também a linha de risco alto de 35 °C; legendas e tabelas estão no HTML offline.

Não foi possível produzir nova captura de navegador nesta revisão: o controle de navegador bloqueou a navegação para `file://` por política de segurança. A restrição não foi contornada. QA realizado por comparação com CSVs, parsing do HTML/SVG, testes e inspeção visual das figuras. A equipe deve capturar a nova versão ao gravar o vídeo para alinhar a evidência visual ao arquivo final.
