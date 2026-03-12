import pandas as pd
import plotly.express as px
import plotly.io as pio
from plotly.subplots import make_subplots
import webbrowser
import os

# ------------------ DATA LOADING ------------------
def load_csvs(_paths):
    return pd.concat([pd.read_csv(
        p, sep=";", quotechar='"', decimal=",", engine="python", dtype=str
    ) for p in _paths], ignore_index=True)

# ------------------ CATEGORY MAPPING + TOP LEVEL ------------------
def map_categories(_df):
    _category_map = {
        'Utrzymanie': {
            'Zdrowie': [
                'Lekarstwa', 'Opieka medyczna'
            ],
            'Transport': [
                'Paliwo', 'Transport publiczny', 'Taxi', 'Bilety lotnicze'
            ],
            'Rachunki': [
                'Czynsz', 'Internet, TV, telefon', 'Ubezpieczenia', 'Prąd'
            ],
            'Wydatki bieżące': [
                'Artykuły spożywcze', 'Kosmetyki', 'Zwierzęta domowe',
                'Uroda, fryzjer, kosmetyczka', 'Fotografia',
                'Zakupy przez internet', 'Alkohol', 'Papierosy'
            ],
            'Podatki i opłaty': [
                'Opłaty bankowe'
            ],
            'Obciążenia wewnętrzne': [
                'Przelew wewnętrzny',
                'Założenie lokaty, zakup funduszy, akcji',
                'Spłata kredytu / pożyczki',
            ],
        },
        'Widzi-mi-się': {
            'Odzież i dodatki': [
                'Dodatki, biżuteria', 'Ubrania', 'Usługi (pralnia, krawiec, szewc,...)'
            ],
            'Dom': [
                'Artykuły dekoracyjne', 'Naprawy i remonty', 'Wyposażenie', 'Sprzęt AGD i RTV', 'Ogród', 'Sprzątanie'
            ],
            'Rozrywka i wypoczynek': [
                'Restauracje i kawiarnie', 'Multimedia', 'Sport', 'Podróże', 'Puby i kluby', 'Gazety lub czasopisma',
                'Kino i teatr', 'Hobby', 'Hotele', 'Książki'
            ],
            'Dla innych': [
                'Prezenty, upominki'
            ],
        },
        'Inne': {
            'Inne': [
                'Inne',
                'Wypłata z bankomatu',
                'Wypłata z rachunku'
            ],
        },
        'Bez kategorii': {
            'Bez kategorii': [
                'Bez kategorii'
            ]
        }
    }
    _reverse_map = {v: k for k, vals in _category_map.items() for v in vals}
    _df["Kategoria_2"] = _df["Kategoria"].map(_reverse_map).fillna("Bez kategorii")

    # Add top-level categories
    utrzymanie = ['Zdrowie', 'Transport', 'Rachunki', 'Podatki i opłaty', 'Obciążenia wewnętrzne', 'Wydatki bieżące']
    widzi_mi_sie = ['Odzież i dodatki', 'Dom', 'Rozrywka i wypoczynek', 'Dla innych']
    def map_top(x):
        if x in utrzymanie:
            return 'Utrzymanie'
        elif x in widzi_mi_sie:
            return 'Widzi-mi-się'
        else:
            return 'Pozostałe'
    _df['Kategoria_1'] = _df['Kategoria_2'].map(map_top)
    return _df

# ------------------ DATA PREPARATION ------------------
def prepare_data(_df):
    _df["Data księgowania"] = pd.to_datetime(_df["Data księgowania"], dayfirst=True)
    _df["Miesiąc"] = _df["Data księgowania"].dt.to_period("M")
    _df["Miesiąc_etykieta"] = _df["Miesiąc"].dt.strftime("%b %Y")
    _df["Kwota operacji"] = (_df["Kwota operacji"].astype(str)
                             .str.replace(" ", "", regex=False)
                             .str.replace(",", ".", regex=False)
                             .astype(float) * -1)
    _df = _df[_df["Kwota operacji"] > 0]

    month_order = (_df.sort_values("Miesiąc")[["Miesiąc", "Miesiąc_etykieta"]]
                   .drop_duplicates().sort_values("Miesiąc")["Miesiąc_etykieta"].tolist())
    _df["Miesiąc_etykieta"] = pd.Categorical(_df["Miesiąc_etykieta"], categories=month_order, ordered=True)
    return _df, month_order

# ------------------ COLORS ------------------
def build_color_maps(_df):
    palette = px.colors.qualitative.Plotly
    # consistent colors for Kategoria_2
    nad_vals = sorted(_df["Kategoria_2"].unique())
    color_map_nad = {v: palette[i % len(palette)] for i, v in enumerate(nad_vals)}

    # different colors per month
    month_vals = sorted(_df["Miesiąc_etykieta"].unique())
    color_map_month = {v: palette[i % len(palette)] for i, v in enumerate(month_vals)}

    cat_vals = sorted(_df["Kategoria"].unique())
    color_map_cat = {v: palette[i % len(palette)] for i, v in enumerate(cat_vals)}
    return color_map_nad, color_map_cat, color_map_month

# ------------------ FIGURES ------------------
def fig_monthly_nad(_df, _color_map_nad, _color_map_month):
    monthly = _df.groupby(["Miesiąc_etykieta", "Kategoria_2"], as_index=False)["Kwota operacji"].sum()
    fig = px.bar(
        monthly,
        x="Miesiąc_etykieta",
        y="Kwota operacji",
        color="Kategoria_2",
        color_discrete_map=_color_map_nad,
        hover_data={"Kwota operacji": True},
    )
    # make stacked and bigger
    fig.update_layout(barmode="stack", xaxis_title="", yaxis_title="Kwota", height=700)
    return fig

def figs_category_breakdown(_df, _color_map_cat):
    fig_list = []
    for nad in sorted(_df["Kategoria_2"].unique()):
        subset = _df[_df["Kategoria_2"] == nad]
        monthly = subset.groupby(["Miesiąc_etykieta", "Kategoria"], as_index=False)["Kwota operacji"].sum()
        fig = px.bar(
            monthly,
            x="Miesiąc_etykieta",
            y="Kwota operacji",
            color="Kategoria",
            color_discrete_map=_color_map_cat,
            title=nad
        )
        fig.update_layout(barmode="stack", xaxis_title="", yaxis_title="")
        fig_list.append(fig)
    return fig_list

def fig_sunburst(_df, _color_map_nad):
    fig = px.sunburst(
        _df,
        path=["Miesiąc_etykieta", "Kategoria_1", "Kategoria_2", "Kategoria"],
        values="Kwota operacji",
        color="Kategoria_2",
        color_discrete_map=_color_map_nad,
        title="Hierarchia wydatków"
    )
    fig.update_layout(height=1000, width=1500)  # slightly bigger
    return fig

# ------------------ DASHBOARD ------------------
def build_dashboard(_figs, _output="finance_dashboard.html"):
    n_barplots = len(_figs) - 1
    rows = n_barplots + 1
    specs = [[{"type": "domain"}]] + [[{"type": "xy"}] for _ in range(n_barplots)]
    row_heights = [0.5] + [0.5 / n_barplots] * n_barplots
    subplot_titles = [f.layout.title.text for f in _figs]

    combined = make_subplots(
        rows=rows, cols=1, specs=specs,
        subplot_titles=subplot_titles, row_heights=row_heights
    )

    # Sunburst first
    for trace in _figs[0].data:
        combined.add_trace(trace, row=1, col=1)

    # Barplots stacked
    for i, f in enumerate(_figs[1:]):
        for trace in f.data:
            combined.add_trace(trace, row=i + 2, col=1)

    combined.update_layout(height=900 + 300 * n_barplots, width=1500)
    combined.write_html(_output, include_plotlyjs="cdn")
    webbrowser.open("file://" + os.path.realpath(_output))

# ------------------ MAIN ------------------
if __name__ == "__main__":
    csv_paths = ["2025_1.csv", "2025_0.csv"]
    df = load_csvs(csv_paths)
    df = map_categories(df)
    df, month_order = prepare_data(df)
    color_map_nad, color_map_cat, color_map_month = build_color_maps(df)

    figs = [fig_sunburst(df, color_map_nad)]
    figs.append(fig_monthly_nad(df, color_map_nad, color_map_month))
    figs.extend(figs_category_breakdown(df, color_map_cat))

    build_dashboard(figs)