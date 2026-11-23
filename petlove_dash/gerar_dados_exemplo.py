"""
Gera dados FICTÍCIOS em ./dados/dados.json no formato que o dashboard espera.
Use para testar. Depois, substitua pelo JSON real do seu projeto (ou ajuste MAPEAMENTO no app.py).

    python gerar_dados_exemplo.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
PASTA = Path(__file__).parent / "dados"
PASTA.mkdir(exist_ok=True)

DIAS = 90
fim = pd.Timestamp.today().normalize()
ini = fim - pd.Timedelta(days=DIAS - 1)

# ----------------------------------------------------------------- produtos
produtos = pd.DataFrame(
    [
        (1, "Biscoitos Orgânicos de Osso", "Cães", 12.99, 4.9),
        (2, "Varinha com penas", "Gatos", 8.50, 4.8),
        (3, "Cama donut marshmallow", "Cães", 45.00, 4.6),
        (4, "Comedouro elevado de cerâmica", "Acessórios", 22.00, 4.7),
        (5, "Arranhador torre", "Gatos", 89.90, 4.5),
        (6, "Ração premium frango 10kg", "Cães", 139.90, 4.8),
        (7, "Alpiste premium 500g", "Aves", 14.50, 4.4),
        (8, "Ração tropical para peixes", "Peixes", 11.90, 4.3),
        (9, "Coleira refletiva", "Acessórios", 29.90, 4.6),
        (10, "Sachê para gatos (cx 12)", "Gatos", 34.90, 4.7),
    ],
    columns=["produto_id", "nome", "categoria", "preco", "avaliacao"],
)
pesos = np.array([0.22, 0.14, 0.10, 0.10, 0.06, 0.08, 0.05, 0.05, 0.08, 0.12])

# ------------------------------------------------------- eventos e pedidos
eventos, pedidos, itens = [], [], []
pedido_id = 847000
FRETE_GRATIS_ACIMA = 25.0

for i in range(DIAS):
    dia = ini + pd.Timedelta(days=i)
    n_sessoes = int(rng.integers(70, 120) * (1 + i / DIAS * 0.5))  # crescimento
    for _ in range(n_sessoes):
        uid = int(rng.integers(1, 2500))
        t = dia + pd.Timedelta(seconds=int(rng.integers(0, 86400)))

        def ev(nome, pid=None):
            eventos.append({"data": t, "usuario_id": uid, "evento": nome, "produto_id": pid})

        if rng.random() < 0.10:
            ev("cadastro")
        ev("login")
        if rng.random() < 0.07:
            ev("esqueci_senha")
        if rng.random() > 0.05:
            ev("ver_home")
            if rng.random() < 0.15:
                ev("clique_banner")
        else:
            continue
        if rng.random() > 0.60:
            continue
        vistos = rng.choice(produtos.produto_id, size=int(rng.integers(1, 4)), replace=False, p=pesos)
        for p in vistos:
            ev("ver_produto", int(p))
            if rng.random() < 0.18:
                ev("favoritar", int(p))
        if rng.random() > 0.35:
            continue
        for p in vistos:
            ev("add_carrinho", int(p))
        if rng.random() > 0.60:
            continue
        ev("iniciar_checkout")
        if rng.random() > 0.75:
            continue

        # ---- pedido confirmado
        pedido_id += 1
        ev("pedido_confirmado")
        sub = 0.0
        for p in vistos:
            qtd = int(rng.integers(1, 3))
            preco = float(produtos.loc[produtos.produto_id == p, "preco"].iloc[0])
            itens.append({"pedido_id": pedido_id, "produto_id": int(p), "qtd": qtd, "preco_unit": preco})
            sub += qtd * preco
        frete = 0.0 if sub >= FRETE_GRATIS_ACIMA else 9.90
        previsao = (t + pd.Timedelta(days=int(rng.integers(0, 3)))).normalize()
        antigo = (fim - t.normalize()).days > 3
        if antigo:
            status = rng.choice(["Entregue", "Cancelado", "Em rota"], p=[0.93, 0.04, 0.03])
        else:
            status = rng.choice(["Em andamento", "Em rota", "Entregue", "Cancelado"], p=[0.45, 0.35, 0.18, 0.02])
        entrega = pd.NaT
        if status == "Entregue":
            atraso = 1 if rng.random() < 0.12 else 0
            entrega = previsao + pd.Timedelta(days=atraso)
        pedidos.append(
            {
                "pedido_id": pedido_id,
                "data_pedido": t,
                "usuario_id": uid,
                "status": status,
                "subtotal": round(sub, 2),
                "frete": frete,
                "total": round(sub + frete, 2),
                "previsao_entrega": previsao,
                "data_entrega": entrega,
                "assinatura": bool(rng.random() < 0.18),
            }
        )
        if rng.random() < 0.08:
            ev("abrir_ajuda")

import json

def recs(df):
    return json.loads(df.to_json(orient="records", date_format="iso", force_ascii=False))

NOMES = ["Sarah","Marcos","Roberta","Thiago","Ana","Bruno","Carla","Diego","Elisa","Fábio","Gabi","Hugo","Iara","João","Lívia","Mateus"]
SOBRENOMES = ["Santos","Lima","Alves","Souza","Pereira","Costa","Rocha","Ribeiro","Martins","Nunes"]
PETS = ["Buddy","Luna","Pipoca","Thor","Mel","Bob","Nina","Fred","Lola","Zeca"]
ids = sorted({e["usuario_id"] for e in eventos})
cad = {}
for e in eventos:
    if e["evento"] == "cadastro" and e["usuario_id"] not in cad:
        cad[e["usuario_id"]] = e["data"]
usuarios = pd.DataFrame({
    "usuario_id": ids,
    "nome": [f"{rng.choice(NOMES)} {rng.choice(SOBRENOMES)}" for _ in ids],
    "pet": [rng.choice(PETS) for _ in ids],
    "data_cadastro": [cad.get(i, ini - pd.Timedelta(days=int(rng.integers(1, 200)))) for i in ids],
})
quantidades = {1: 5, 2: 2, 3: 1, 4: 28, 5: 12, 6: 6, 7: 40, 8: 55, 9: 33, 10: 9}
estoque = pd.DataFrame({
    "produto_id": list(quantidades),
    "quantidade": list(quantidades.values()),
    "minimo": [20, 15, 10, 15, 8, 12, 15, 15, 12, 15],
})

saida = {
    "eventos": recs(pd.DataFrame(eventos)),
    "pedidos": recs(pd.DataFrame(pedidos)),
    "itens_pedido": recs(pd.DataFrame(itens)),
    "produtos": recs(produtos),
    "usuarios": recs(usuarios),
    "estoque": recs(estoque),
}
(PASTA / "dados.json").write_text(json.dumps(saida, ensure_ascii=False), encoding="utf-8")
print(f"OK: {len(eventos)} eventos, {len(pedidos)} pedidos, {len(itens)} itens -> {PASTA / 'dados.json'}")
