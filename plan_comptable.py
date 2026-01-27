import streamlit as st
import pandas as pd
from supabase import create_client

# =========================
# CONFIG SUPABASE
# =========================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# LOAD PLAN COMPTABLE
# =========================
@st.cache_data
def load_plan():
    res = supabase.table("plan_comptable").select("*").order("groupe_compte, compte_8").execute()
    return pd.DataFrame(res.data)

# =========================
# UI
# =========================
st.subheader("📘 Plan comptable")

df_plan = load_plan()

if df_plan.empty:
    st.warning("Aucun compte enregistré")
else:
    st.dataframe(df_plan, use_container_width=True)

# =========================
# 1️⃣ MODIFIER LIBELLÉ DE GROUPE
# =========================
st.markdown("## ✏️ Modifier un libellé de groupe")

groupes = sorted(df_plan["groupe_compte"].unique())

groupe_sel = st.selectbox("Groupe de compte", groupes)

libelle_actuel = (
    df_plan[df_plan["groupe_compte"] == groupe_sel]["libelle_groupe"]
    .iloc[0]
)

new_libelle = st.text_input(
    "Libellé du groupe",
    value=libelle_actuel
)

if st.button("💾 Mettre à jour le libellé du groupe"):
    supabase.table("plan_comptable") \
        .update({"libelle_groupe": new_libelle}) \
        .eq("groupe_compte", groupe_sel) \
        .execute()

    st.success(f"Groupe {groupe_sel} mis à jour")
    st.cache_data.clear()
    st.rerun()

# =========================
# 2️⃣ AJOUTER / MODIFIER UN COMPTE
# =========================
st.markdown("## ➕ Ajouter ou modifier un compte")

compte_8 = st.text_input("Compte (8 chiffres)", max_chars=8)
libelle_compte = st.text_input("Libellé du compte")
groupe_compte = st.text_input("Groupe (ex: 601)", max_chars=3)
libelle_groupe = st.text_input("Libellé du groupe associé")

if st.button("💾 Enregistrer le compte"):
    supabase.table("plan_comptable").upsert({
        "compte_8": compte_8,
        "libelle": libelle_compte,
        "groupe_compte": groupe_compte,
        "libelle_groupe": libelle_groupe
    }).execute()

    st.success("Compte enregistré")
    st.cache_data.clear()
    st.rerun()

# =========================
# 3️⃣ SUPPRIMER UN COMPTE
# =========================
st.markdown("## ❌ Supprimer un compte")

compte_del = st.selectbox(
    "Compte à supprimer",
    df_plan["compte_8"].unique()
)

if st.button("🗑 Supprimer le compte"):
    supabase.table("plan_comptable") \
        .delete() \
        .eq("compte_8", compte_del) \
        .execute()

    st.success("Compte supprimé")
    st.cache_data.clear()
    st.rerun()