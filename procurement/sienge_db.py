"""
Reference data from Sienge for PO form dropdowns.
IDs confirmed from Sienge PostgreSQL replica on 2026-07-28.
"""


def get_departments() -> dict:
    """Returns {department_id: department_name} — IDS-relevant departments only."""
    return {
        11: "PRODUTOS",
        12: "IDS SERVICE",
    }


def get_payment_categories() -> dict:
    """
    Returns {category_id: category_name} for 2.01.01.01 — COMPRAS MERCADORIAS
    (parent_id='2010101' in Sienge, categories at level 4).
    """
    return {
        "201010101": "Geradores",
        "201010102": "UPS e Baterias",
        "201010103": "Climatizacao (CRAH, CRAC, outros)",
        "201010104": "Powerpods",
        "201010105": "Fitout - Equipamentos",
        "201010106": "Materiais Manutencao Preventiva",
        "201010107": "Materiais Manutencao Corretiva",
        "201010108": "Empreitada Global - Materiais",
        "201010109": "Materiais e Insumos Aplicados na Obra",
        "201010110": "Aquisicao de Terreno",
        "201010111": "I/C Vendas Mercadorias - partes relacionadas",
        "201010112": "Outras mercadorias vendidas",
    }
