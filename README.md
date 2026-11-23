# Dashboard-pi-4
# PetLove — Dashboard de acompanhamento

## Rodar
    pip install -r requirements.txt
    python gerar_dados_exemplo.py     # só para testar com dados fictícios
    streamlit run app.py
    # se "streamlit" não for reconhecido (Windows): python -m streamlit run app.py

## Alimentar com o JSON do seu projeto
Salve o JSON em `dados/dados.json` (ou envie pela barra lateral) e recarregue a página.
O JSON é um objeto com as listas `eventos`, `pedidos`, `itens_pedido`, `produtos`
(veja o exemplo gerado por `python gerar_dados_exemplo.py`). Opcionais: `usuarios` (nome do tutor e pet) e `estoque` (produto_id, quantidade, minimo) — sem eles, somem só os nomes dos clientes e os alertas de estoque. `clientes` (nome e pet) e `estoque` são opcionais: sem eles, a lista de pedidos mostra "Cliente <id>" e a aba Estoque fica vazia.

Se os nomes dos campos do seu JSON forem diferentes, preencha `MAPEAMENTO` (e `MAPEAMENTO_VALORES`
para status/eventos) no topo do `app.py`. Também aceita um arquivo por tabela
(`dados/pedidos.json`...), itens aninhados em cada pedido (`"itens": [...]`) e CSV.

Eventos: login, cadastro, esqueci_senha, ver_home, clique_banner, ver_produto, favoritar,
add_carrinho, iniciar_checkout, pedido_confirmado, abrir_ajuda.
Status: Em andamento, Em rota, Entregue, Cancelado.

## Abrir com duplo clique
- Windows: `iniciar.bat`  (precisa de Python instalado, marcando "Add Python to PATH")
- Mac: `iniciar.command`
Na primeira vez ele instala tudo sozinho (precisa de internet); depois abre direto.
