import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Outil d'analyse de portefeuille immobilier", layout="wide")

# Style CSS Institutionnel / Exécutif
st.markdown("""
<style>
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        padding: 14px 18px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        color: #475569 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
        font-weight: 700 !important;
        color: #0F172A !important;
    }
    section[data-testid="stSidebar"] {
        border-right: 1px solid #E2E8F0;
    }
    [data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #E2E8F0;
    }
    hr {
        margin: 1.2rem 0 !important;
        border-color: #E2E8F0 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏢 Outil d'analyse de portefeuille immobilier")
st.markdown("Plateforme de simulation axée **exclusivement sur le portefeuille immobilier** (Analyse de la valeur, DSCR, LTV et capacité de liquidité).")

# --- AIDE-MÉMOIRE ET GLOSSAIRE INTÉGRÉ ---
with st.expander("📚 Aide-mémoire financier & Formules de calcul", expanded=False):
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("**1. LTV (Loan-to-Value / Ratio Prêt-Valeur)**")
        st.caption("Mesure la proportion de dette par rapport à la valeur marchande de l'immeuble.")
        st.latex(r"\text{LTV} = \frac{\text{Dette Actuelle}}{\text{Valeur de l'immeuble}} \times 100")
        st.markdown("* **Risque :** Si la valeur de l'immeuble chute, le LTV augmente. S'il dépasse le **LTV Max** toléré par la banque, un appel de marge est déclenché.")
        
        st.markdown("---")
        
        st.markdown("**2. DSCR (Debt Service Coverage Ratio / Ratio de Couverture de la Dette)**")
        st.caption("Mesure la capacité des revenus de l'immeuble à payer ses intérêts et sa dette.")
        st.latex(r"\text{DSCR} = \frac{\text{Revenu Net Opérationnel (NOI)}}{\text{Service de la Dette (Intérêts)}}")
        st.markdown("* **Risque :** Si les taux d'intérêt montent ou si les loyers chutent, le DSCR baisse. S'il passe sous le **DSCR Min** exigé (ex: 1.15x), la banque exige un remboursement partiel.")

    with col_b:
        st.markdown("**3. NOI (Net Operating Income / Revenu Net Opérationnel)**")
        st.caption("Revenu net généré par l'immeuble avant le paiement de l'hypothèque.")
        st.latex(r"\text{NOI} = \text{Revenus Locatifs Bruts} - \text{Dépenses d'Exploitation}")
        st.markdown("* **Formule alternative :** $\text{NOI} = \text{Valeur} \times \text{Cap Rate}$")
        
        st.markdown("---")
        
        st.markdown("**4. Cap Rate & Détention**")
        st.caption("Taux de rendement brut du marché et part de propriété de l'investisseur.")
        st.latex(r"\text{Valeur de l'immeuble} = \frac{\text{NOI}}{\text{Cap Rate}}")
        st.markdown("* **% Détention :** Pourcentage de participation nette détenu par l'investisseur dans la structure (ex: 33.3%, 50%, 100%).")
        st.markdown("* **Appel de Marge (Margin Call) :** Montant d'équité en argent frais à réinjecter d'urgence pour rétablir les ratios LTV ou DSCR exigés par le prêteur.")

st.markdown("---")

# --- MENU DE NAVIGATION (SIDEBAR) ---
st.sidebar.header("⚙️ Configuration du Choc")
scenario = st.sidebar.selectbox(
    "Scénario à simuler", 
    [
        "0. Situation Actuelle (Sans choc / Statu quo)",
        "1. Choc des Taux (2022-2023)", 
        "2. Crise Financière (2008)", 
        "3. Crise Immobilière Qc (1990)",
        "4. Scénario Personnalisé"
    ]
)

if "Situation Actuelle" in scenario:
    choc_taux = st.sidebar.slider("Hausse des Taux d'emprunt (%)", 0.0, 10.0, 0.0, 0.1) / 100
    choc_cap_rate = st.sidebar.slider("Hausse des Cap Rates (%)", 0.0, 5.0, 0.0, 0.1) / 100
    choc_noi = st.sidebar.slider("Impact sur Revenus (NOI) (%)", -50.0, 10.0, 0.0, 1.0) / 100
elif "Taux" in scenario:
    choc_taux = st.sidebar.slider("Hausse des Taux d'emprunt (%)", 0.0, 10.0, 4.0, 0.1) / 100
    choc_cap_rate = st.sidebar.slider("Hausse des Cap Rates (%)", 0.0, 5.0, 0.5, 0.1) / 100
    choc_noi = st.sidebar.slider("Impact sur Revenus (NOI) (%)", -50.0, 10.0, 0.0, 1.0) / 100
elif "Financière" in scenario:
    choc_taux = st.sidebar.slider("Hausse des Taux d'emprunt (%)", 0.0, 10.0, 1.0, 0.1) / 100
    choc_cap_rate = st.sidebar.slider("Hausse des Cap Rates (%)", 0.0, 5.0, 1.5, 0.1) / 100
    choc_noi = st.sidebar.slider("Impact sur Revenus (NOI) (%)", -50.0, 10.0, -10.0, 1.0) / 100
elif "Immobilière" in scenario:
    choc_taux = st.sidebar.slider("Hausse des Taux d'emprunt (%)", 0.0, 10.0, 6.0, 0.1) / 100
    choc_cap_rate = st.sidebar.slider("Hausse des Cap Rates (%)", 0.0, 5.0, 2.5, 0.1) / 100
    choc_noi = st.sidebar.slider("Impact sur Revenus (NOI) (%)", -50.0, 10.0, -25.0, 1.0) / 100
else: # Personnalisé
    choc_taux = st.sidebar.slider("Hausse des Taux d'emprunt (%)", 0.0, 10.0, 2.0, 0.1) / 100
    choc_cap_rate = st.sidebar.slider("Hausse des Cap Rates (%)", 0.0, 5.0, 1.0, 0.1) / 100
    choc_noi = st.sidebar.slider("Impact sur Revenus (NOI) (%)", -50.0, 10.0, -5.0, 1.0) / 100

st.sidebar.markdown("---")

uploaded_file = st.sidebar.file_uploader("Importer le fichier Excel", type=['xlsx'])

if uploaded_file is not None:
    immo = pd.read_excel(uploaded_file, sheet_name='Immobilier')
    try:
        treso = pd.read_excel(uploaded_file, sheet_name='Tresorerie')
    except:
        treso = pd.DataFrame({'Type': ['Cash par défaut'], 'Montant': [0]})
    st.sidebar.success(f"{len(immo)} immeubles chargés avec succès !")
else:
    st.warning("👈 Veuillez importer votre fichier Excel pour commencer.")
    st.stop()

# --- NETTOYAGE ET CONSOLIDATION DES DONNÉES ---
# Gestion dynamique de la colonne % Détention / Participation
col_detention = None
for col in ['Pct_Detention', '%_Detention', '% de détention', 'Pct_Participation', '%_Participation', 'Participation']:
    if col in immo.columns:
        col_detention = col
        break

if col_detention is not None:
    immo['Pct_Detention'] = immo[col_detention].fillna(1.0)
    # Convert string percentage if needed
    if immo['Pct_Detention'].dtype == object:
        immo['Pct_Detention'] = immo['Pct_Detention'].astype(str).str.replace('%', '').str.replace(',', '.').astype(float)
        immo['Pct_Detention'] = np.where(immo['Pct_Detention'] > 1.0, immo['Pct_Detention'] / 100.0, immo['Pct_Detention'])
else:
    immo['Pct_Detention'] = 1.0 # 100% par défaut

if 'NOI' not in immo.columns or immo['NOI'].isna().all() or (immo['NOI'] == 0).all():
    immo['NOI'] = immo['Valeur_Actuelle'] * immo['Cap_Rate_Actuel']
else:
    immo['NOI'] = np.where(immo['NOI'].isna() | (immo['NOI'] == 0), immo['Valeur_Actuelle'] * immo['Cap_Rate_Actuel'], immo['NOI'])

if 'Taux_Actuel' not in immo.columns:
    immo['Taux_Actuel'] = 0.045

taux_effectif = np.where((immo['Taux_Actuel'].isna()) | (immo['Taux_Actuel'] == 0), 0.045, immo['Taux_Actuel'])

if 'Type_Taux' not in immo.columns:
    immo['Type_Taux'] = 'Variable'
else:
    immo['Type_Taux'] = immo['Type_Taux'].fillna('Variable')

if 'Date_Echeance' not in immo.columns:
    immo['Date_Echeance'] = '2026'
else:
    immo['Date_Echeance'] = immo['Date_Echeance'].astype(str).replace('nan', 'Indéterminée')

if 'LTV_Max' not in immo.columns:
    immo['LTV_Max'] = 0.75

if 'DSCR_Min' not in immo.columns:
    immo['DSCR_Min'] = 1.15

# --- SÉLECTION ET PROTECTION DES TAUX PAR ÉCHÉANCE ---
st.sidebar.subheader("🎯 Cible du Choc de Taux")

def extraire_annee(d):
    d_str = str(d)
    for y in range(2023, 2036):
        if str(y) in d_str:
            return y
    return 2026

immo['Annee_Echeance'] = immo['Date_Echeance'].apply(extraire_annee)

ciblage_mode = st.sidebar.radio(
    "Dettes soumises au choc de taux :",
    [
        "1. Taux Variable OU Échéance imminente (<= 2027)",
        "2. Sélection personnalisée par échéance",
        "3. Toutes les dettes (Pire scénario / Refinancement global)"
    ]
)

annee_seuil = 2027

if "1. Taux Variable" in ciblage_mode:
    mask_choc = immo['Type_Taux'].astype(str).str.contains('variable|var', case=False, na=False) | (immo['Annee_Echeance'] <= annee_seuil)
elif "3. Toutes les dettes" in ciblage_mode:
    mask_choc = pd.Series([True] * len(immo), index=immo.index)
else:
    annees_disponibles = sorted(immo['Annee_Echeance'].unique().tolist())
    annees_choisies = st.sidebar.multiselect(
        "Sélectionnez les années d'échéance subissant le choc :",
        options=annees_disponibles,
        default=[y for y in annees_disponibles if y <= 2027]
    )
    mask_choc = immo['Type_Taux'].astype(str).str.contains('variable|var', case=False, na=False) | immo['Annee_Echeance'].isin(annees_choisies)

# --- CALCULS FINANCIERS DE STRESS TEST ---
immo['NOI_Stress'] = immo['NOI'] * (1 + choc_noi)
immo['Cap_Rate_Stress'] = immo['Cap_Rate_Actuel'] + choc_cap_rate
immo['Valeur_Stress'] = np.where(immo['Cap_Rate_Stress'] > 0, immo['NOI_Stress'] / immo['Cap_Rate_Stress'], immo['Valeur_Actuelle'])

immo['Choc_Appliqué'] = np.where(choc_taux == 0, "Non (Sans choc)", 
                         np.where(mask_choc, "Oui (+{:.1f}%)".format(choc_taux*100), "Non (Taux Fixe protégé)"))
immo['Taux_Stress'] = np.where(mask_choc, taux_effectif + choc_taux, taux_effectif)

immo['Interet_Actuel'] = immo['Dette_Actuelle'] * taux_effectif
immo['Interet_Stress'] = immo['Dette_Actuelle'] * immo['Taux_Stress']

immo['DSCR_Actuel'] = np.where(immo['Interet_Actuel'] > 0, immo['NOI'] / immo['Interet_Actuel'], np.nan)
immo['DSCR_Stress'] = np.where(immo['Interet_Stress'] > 0, immo['NOI_Stress'] / immo['Interet_Stress'], np.nan)

immo['LTV_Actuel'] = np.where(immo['Valeur_Actuelle'] > 0, immo['Dette_Actuelle'] / immo['Valeur_Actuelle'], 0)
immo['LTV_Stress'] = np.where(immo['Valeur_Stress'] > 0, immo['Dette_Actuelle'] / immo['Valeur_Stress'], 0)

# Appels de marge LTV et DSCR
immo['Appel_Marge_LTV'] = np.where(
    immo['LTV_Stress'] > immo['LTV_Max'],
    immo['Dette_Actuelle'] - (immo['Valeur_Stress'] * immo['LTV_Max']),
    0
)

immo['Dette_Cible_DSCR'] = np.where(immo['Taux_Stress'] > 0, immo['NOI_Stress'] / (immo['DSCR_Min'] * immo['Taux_Stress']), 0)
immo['Appel_Marge_DSCR'] = np.where(
    (immo['DSCR_Stress'] < immo['DSCR_Min']) & (immo['DSCR_Stress'] > 0),
    immo['Dette_Actuelle'] - immo['Dette_Cible_DSCR'],
    0
)

immo['Appel_Marge_Total'] = immo[['Appel_Marge_LTV', 'Appel_Marge_DSCR']].max(axis=1)

# Remplacement de "Covenant" par "Source du risque"
immo['Source_du_Risque'] = np.where(immo['Appel_Marge_LTV'] > immo['Appel_Marge_DSCR'], 'LTV (Prêt/Valeur)', 
                                    np.where(immo['Appel_Marge_DSCR'] > 0, 'DSCR (Couverture Dette)', 'Aucun'))

# Trésorerie Immobilière Uniquement
if 'Entite' in treso.columns:
    treso_immo = treso[~treso['Entite'].astype(str).str.contains('Venture|VC', case=False, na=False)]
else:
    treso_immo = treso

cash_dispo = treso_immo['Montant'].sum()
appels_marge_totaux = immo['Appel_Marge_Total'].sum()
gap_liquidite = cash_dispo - appels_marge_totaux

# --- INDICATEURS CLÉS (METRICS) ---
if choc_taux == 0 and choc_cap_rate == 0 and choc_noi == 0:
    st.info("🟢 **Mode Situation Actuelle (Sans choc) :** Aucune modification de taux, de valeur ou d'appels de capitaux n'est appliquée.")

valeur_totale_actuelle = immo['Valeur_Actuelle'].sum()
valeur_totale_stress = immo['Valeur_Stress'].sum()
dette_totale = immo['Dette_Actuelle'].sum()

ltv_global_actuel = dette_totale / valeur_totale_actuelle if valeur_totale_actuelle > 0 else 0
ltv_global_stress = dette_totale / valeur_totale_stress if valeur_totale_stress > 0 else 0

row1_1, row1_2, row1_3, row1_4 = st.columns(4)
row1_1.metric("Valeur Immobilière Totale", f"{valeur_totale_stress:,.0f} $", f"{((valeur_totale_stress/valeur_totale_actuelle)-1)*100:+.1f} % vs Actuel")
row1_2.metric("LTV Global du Portefeuille", f"{ltv_global_stress:.1%}", f"Actuel : {ltv_global_actuel:.1%}")
row1_3.metric("Appels de Marge Totaux", f"{appels_marge_totaux:,.0f} $", "Besoins d'équité", delta_color="off")
row1_4.metric("Trésorerie / Gap Liquidité", f"{gap_liquidite:,.0f} $", "Surplus" if gap_liquidite >= 0 else "Déficit Cash", delta_color="normal")

st.markdown("---")

# --- GRAPHIQUES DE SYNTHÈSE ---
c_chart1, c_chart2 = st.columns([1, 1])

with c_chart1:
    st.subheader("💧 Bilan Trésorerie vs Appels de Marge")
    fig_liq = go.Figure(data=[
        go.Bar(name='Trésorerie Immobilière Disponible', x=['Analyse'], y=[cash_dispo], marker_color='#2A9D8F'),
        go.Bar(name='Appels de Marge Requis (LTV + DSCR)', x=['Analyse'], y=[appels_marge_totaux], marker_color='#E76F51')
    ])
    fig_liq.update_layout(barmode='group', template="plotly_white", margin=dict(l=20, r=20, t=30, b=20), height=320)
    st.plotly_chart(fig_liq, use_container_width=True)

with c_chart2:
    st.subheader("⚠️ Origine de la Source du Risque")
    appels_ltv_pur = immo['Appel_Marge_LTV'].sum()
    appels_dscr_pur = immo['Appel_Marge_DSCR'].sum()
    
    if appels_marge_totaux > 0:
        fig_pie = px.pie(
            names=['Risque LTV (Baisse de valeur)', 'Risque DSCR (Hausse taux / Chute revenus)'],
            values=[appels_ltv_pur, appels_dscr_pur],
            color_discrete_sequence=['#E76F51', '#F4A261'],
            hole=0.4
        )
        fig_pie.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=320)
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.success("✅ Aucun risque de liquidité ou appel de marge déclenché dans ce scénario.")

st.markdown("---")

# --- TABLEAU DÉTAILLÉ IMMOBILIER ---
st.subheader(f"📋 Tableau Détaillé des {len(immo)} Immeubles")

df_display = immo[['Propriete', 'Pct_Detention', 'Type_Taux', 'Date_Echeance', 'Choc_Appliqué', 'Valeur_Actuelle', 'Valeur_Stress', 'Taux_Actuel', 'Taux_Stress', 'DSCR_Actuel', 'DSCR_Stress', 'LTV_Actuel', 'LTV_Stress', 'Source_du_Risque', 'Appel_Marge_Total']].copy()

# Renommer la colonne Pct_Detention pour un affichage parfait
df_display = df_display.rename(columns={'Pct_Detention': '% Détention'})

def highlight_risque(val):
    if 'LTV' in str(val) or 'DSCR' in str(val): 
        return 'background-color: #fee2e2; color: #991b1b; font-weight: bold;'
    return ''

styler = df_display.style.format({
    '% Détention': '{:.1%}',
    'Valeur_Actuelle': '{:,.0f} $', 'Valeur_Stress': '{:,.0f} $',
    'Taux_Actuel': '{:.2%}', 'Taux_Stress': '{:.2%}', 
    'DSCR_Actuel': '{:.2f}x', 'DSCR_Stress': '{:.2f}x', 
    'LTV_Actuel': '{:.1%}', 'LTV_Stress': '{:.1%}', 
    'Appel_Marge_Total': '{:,.0f} $'
})

if hasattr(styler, 'map'):
    st_styled = styler.map(highlight_risque, subset=['Source_du_Risque'])
else:
    st_styled = styler.applymap(highlight_risque, subset=['Source_du_Risque'])

st.dataframe(st_styled, use_container_width=True, height=500)
