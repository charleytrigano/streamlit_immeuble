import streamlit as st
import pandas as pd
from supabase import create_client
import altair as alt

# =====================================================
# CONFIG STREAMLIT
# =====================================================
st.set_page_config(
    page_title="Pilotage des charges",
    layout="wide"
)

# =====================================================
# OUTILS
# =====================================================
def euro(val):
    try:
        return f"{val:,.2f} €".replace(",", " ").replace(".", ",")
    except Exception:
        return "0,00 €"

# =====================================================
# SUPABASE
# =====================================================
@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"]
    )

@st.cache_data
def load_budget_vs_reel():
    supabase = get_supabase()
    res = (
        supabase
        .table("v_budget_vs_reel_2025_groupe")
        .select("*")
        .execute()
    )
    return pd.DataFrame(res.data)

# =====================================================
# MAIN
# =====================================================
def main():
    st.title("📊 Pilotage des charges – Budget vs Réel")

    df = load_budget_vs_reel()

    if df.empty:
        st.warning("Aucune donnée disponible.")
        return

    # =================================================
    # KPI
    # =================================================
    budget_total = df["budget_total"].sum()
    reel_total   = df["reel_total"].sum()
    ecart_total  = df["ecart_total"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Budget total", euro(budget_total))
    col2.metric("💸 Charges réelles", euro(reel_total))
    col3.metric("📊 Écart global", euro(ecart_total))

    st.divider()

    # =================================================
    # TABLEAU
    # =================================================
    st.subheader("📋 Détail par groupe de comptes")

    st.dataframe(
        df.sort_values("groupe_compte").rename(columns={
            "annee": "Année",
            "groupe_compte": "Groupe de comptes",
            "budget_total": "Budget (€)",
            "reel_total": "Réel (€)",
            "ecart_total": "Écart (€)"
        }),
        use_container_width=True
    )

    st.divider()

    # =================================================
    # GRAPHIQUE
    # =================================================
    st.subheader("📈 Réel par groupe de comptes")

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("groupe_compte:N", title="Groupe de comptes"),
            y=alt.Y("reel_total:Q", title="Charges réelles (€)"),
            tooltip=[
                alt.Tooltip("groupe_compte:N", title="Groupe"),
                alt.Tooltip("budget_total:Q", title="Budget", format=",.2f"),
                alt.Tooltip("reel_total:Q", title="Réel", format=",.2f"),
                alt.Tooltip("ecart_total:Q", title="Écart", format=",.2f")
            ]
        )
    )

    st.altair_chart(chart, use_container_width=True)

# =====================================================
# RUN
# =====================================================
if __name__ == "__main__":
    main()