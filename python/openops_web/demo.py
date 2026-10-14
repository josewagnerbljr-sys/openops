# AI assistance (CS50 final-project policy): this file was written or modified with the AI assistant Claude (Anthropic). See README.md, section 6.
"""
openops_web.demo
=================

Dados de demonstração (idempotentes): povoam um banco vazio com produtos,
movimentações e clientes de exemplo, para o avaliador ou o novo usuário
ver o sistema "vivo" em segundos. Não faz nada se já existem produtos —
nunca mistura dados de exemplo com dados reais.
"""

from __future__ import annotations

from datetime import date, timedelta

from .app import WebApp

_PRODUCTS = [
    # (nome, preço, categoria, estoque inicial)
    ("Caneca de cerâmica 300 ml", 24.90, "Casa", 42),
    ("Caderno A5 pautado", 18.50, "Papelaria", 60),
    ("Caneta esferográfica azul", 2.80, "Papelaria", 3),
    ("Garrafa térmica 500 ml", 79.90, "Casa", 12),
    ("Mochila urbana 20 L", 189.00, "Acessórios", 0),
    ("Carregador USB-C 20 W", 69.90, "Eletrônicos", 8),
    ("Álcool em gel 500 ml", 12.90, "Higiene", 30),
    ("Pilhas AA (cartela com 4)", 15.00, "Eletrônicos", 25),
]


def seed_demo(app: WebApp) -> bool:
    """Devolve ``True`` se criou os dados, ``False`` se já havia produtos."""
    if app.products.list_products():
        return False

    today = date.today()
    for name, price, category, stock in _PRODUCTS:
        product = app.products.create_product(name=name, price=price, category=category)
        if stock:
            expiry = None
            batch = ""
            if name.startswith("Álcool"):
                expiry, batch = today + timedelta(days=21), "L2410-A"
            elif name.startswith("Pilhas"):
                expiry, batch = today + timedelta(days=400), "P-0925"
            app.inventory.register_movement(
                product_id=product.id, movement_type="in", quantity=stock,
                reason="Estoque inicial (demonstração)", batch_number=batch, expiry_date=expiry,
            )

    by_name = {p.name: p.id for p in app.products.list_products()}
    app.inventory.register_movement(product_id=by_name["Caderno A5 pautado"], movement_type="out", quantity=7, reason="Venda balcão")
    app.inventory.register_movement(product_id=by_name["Caneca de cerâmica 300 ml"], movement_type="out", quantity=5, reason="Pedido online #1042")

    for name, email, phone in [
        ("Ana Souza", "ana.souza@example.com", "(44) 99999-0001"),
        ("Mercado Boa Compra", "compras@example.com", "(44) 3333-0002"),
        ("Carlos Lima", None, "(44) 99999-0003"),
    ]:
        app.customers.create_customer(name=name, email=email, phone=phone)
    return True
