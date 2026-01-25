# =========================
# CHARGES RÉELLES (ROBUSTE)
# =========================

# 1. Toutes les dépenses
df_dep = pd.DataFrame(dep_resp.data)

# 2. Toutes les répartitions
df_rep = pd.DataFrame(rep_resp.data)

# 3. Si une dépense n'a pas de répartition → on la répartit sur tous les lots
dep_sans_rep = df_dep[~df_dep["id"].isin(df_rep["depense_id"].unique())]

auto_rep = dep_sans_rep.assign(key=1).merge(
    df_lots.assign(key=1),
    on="key"
).drop("key", axis=1)

auto_rep["quote_part"] = auto_rep["tantiemes"] / BASE_TANTIEMES
auto_rep["charge_reelle"] = auto_rep["montant_ttc"] * auto_rep["quote_part"]

# 4. Dépenses avec répartition existante
df_rep["quote_part"] = df_rep["quote_part"] / BASE_TANTIEMES

rep_calc = (
    df_rep
    .merge(df_dep, left_on="depense_id", right_on="id")
    .merge(df_lots, on="lot_id")
)

rep_calc["charge_reelle"] = rep_calc["montant_ttc"] * rep_calc["quote_part"]

# 5. Charges réelles finales
df_charges = pd.concat([rep_calc, auto_rep], ignore_index=True)