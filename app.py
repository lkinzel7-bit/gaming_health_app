import os
import altair as alt
import streamlit as st
import pandas as pd

st.set_page_config(page_title='Gaming & Mentale Gesundheit Dashboard', page_icon='🎮', layout='wide')

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(APP_DIR, 'GamingStudy_data_Cleaned.csv')

MOTIVATION_MAP = {
    'having fun': 'Having fun',
    'improving': 'Improving',
    'winning': 'Winning',
    'relaxing': 'Relaxing',
    'all of the above': 'All of the above',
    'All of the above': 'All of the above',
}

PLAYSTYLE_MAP = {
    'all of the above': 'All of the above',
    'All of the above': 'All of the above',
}


@st.cache_data
def load_data():
    if not os.path.exists(DATA_PATH):
        st.error(
            f'CSV-Datei nicht gefunden unter:\n\n`{DATA_PATH}`\n\n'
            'Bitte `GamingStudy_data_Cleaned.csv` in denselben Ordner wie `app.py` legen.'
        )
        st.stop()

    df = pd.read_csv(DATA_PATH)
    df['whyplay_clean'] = df['whyplay'].apply(lambda x: MOTIVATION_MAP.get(x, 'Other / mixed'))
    df['Playstyle_clean'] = df['Playstyle'].apply(lambda x: PLAYSTYLE_MAP.get(x, x))
    return df


NUMERIC_VARS = {
    'Hours': 'Spielstunden pro Woche',
    'GAD_T': 'GAD-7 Angst-Score',
}


def main():
    st.title('Gaming & Mentale Gesundheit Dashboard 🎮🧠')
    st.write(
        'Explorative Analyse zur Korrelation zwischen Gaming-Verhalten '
        '(Spielzeit, Motivation, Spielstil) und dem Angst-Score (GAD-7).'
    )

    with st.expander('ℹ️ Was ist der GAD-7 (Angst-Score)?', expanded=False):
        st.write(
            'Der **GAD-7** (Generalized Anxiety Disorder 7-item scale, Spitzer et al. '
            '2006) ist ein etablierter klinischer Fragebogen zur Erfassung generalisierter '
            'Angst. Er fragt, wie oft man in den **letzten 2 Wochen** durch die folgenden '
            '7 Beschwerden beeinträchtigt war (0 = überhaupt nicht, 1 = an einzelnen Tagen, '
            '2 = an mehr als der Hälfte der Tage, 3 = beinahe jeden Tag):'
        )
        st.markdown(
            '1. Nervosität, Ängstlichkeit oder Anspannung\n'
            '2. Unfähigkeit, Sorgen zu stoppen oder zu kontrollieren\n'
            '3. Übermäßige Sorgen über verschiedene Dinge\n'
            '4. Schwierigkeiten zu entspannen\n'
            '5. Rastlosigkeit, sodass Stillsitzen schwerfällt\n'
            '6. Leichte Reizbarkeit\n'
            '7. Angst, dass etwas Schreckliches passieren könnte'
        )
        st.write(
            'Der Summenscore **GAD_T** ergibt sich aus den 7 Antworten und reicht von '
            '**0 bis 21** – je höher, desto stärker die Angstsymptomatik. Übliche '
            'Einordnung: 0–4 = minimale, 5–9 = leichte, 10–14 = mittelgradige, '
            '15–21 = schwere Angst.'
        )

    df = load_data()

    st.sidebar.title('Filter ⚙️')

    age_range = st.sidebar.slider(
        'Alter:',
        int(df['Age'].min()),
        int(df['Age'].max()),
        (18, 63)
    )

    hours_range = st.sidebar.slider(
        'Spielstunden pro Woche:',
        int(df['Hours'].min()),
        int(df['Hours'].max()),
        (int(df['Hours'].min()), int(df['Hours'].max()))
    )

    gender_options = ['Alle'] + sorted(df['Gender'].unique().tolist())
    gender_choice = st.sidebar.selectbox('Geschlecht:', gender_options)

    platform_options = ['Alle'] + sorted(df['Platform'].unique().tolist())
    platform_choice = st.sidebar.selectbox('Plattform:', platform_options)

    motivation_options = ['Alle'] + sorted(df['whyplay_clean'].unique().tolist())
    motivation_choice = st.sidebar.selectbox('Spielmotivation:', motivation_options)

    filtered_df = df[
        (df['Age'] >= age_range[0]) & (df['Age'] <= age_range[1]) &
        (df['Hours'] >= hours_range[0]) & (df['Hours'] <= hours_range[1])
    ]

    if gender_choice != 'Alle':
        filtered_df = filtered_df[filtered_df['Gender'] == gender_choice]
    if platform_choice != 'Alle':
        filtered_df = filtered_df[filtered_df['Platform'] == platform_choice]
    if motivation_choice != 'Alle':
        filtered_df = filtered_df[filtered_df['whyplay_clean'] == motivation_choice]

    st.subheader('Gefilterte Daten')
    st.write(f'Zeige **{len(filtered_df)}** von {len(df)} Teilnehmer:innen')

    if len(filtered_df) == 0:
        st.warning('Keine Datensätze für die aktuelle Filterauswahl. Bitte Filter anpassen.')
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric('Teilnehmer:innen', len(filtered_df))
    col2.metric('Ø Spielstunden/Woche', f"{filtered_df['Hours'].mean():.1f}")
    col3.metric('Ø GAD-7 (Angst)', f"{filtered_df['GAD_T'].mean():.1f}")
    col4.metric('Ø Lebenszufriedenheit', f"{filtered_df['SWL_T'].mean():.1f}")

    if st.checkbox('Rohdaten anzeigen'):
        st.dataframe(filtered_df)

    st.markdown('---')

    st.subheader('Verteilung einzelner Merkmale')
    feature = st.selectbox(
        'Merkmal auswählen:',
        list(NUMERIC_VARS.keys()),
        format_func=lambda k: NUMERIC_VARS[k]
    )

    bins = pd.cut(filtered_df[feature], bins=20)
    hist_counts = bins.value_counts().sort_index()
    true_min = filtered_df[feature].min()

    bin_labels = []
    for interval in hist_counts.index:
        left = max(interval.left, true_min)
        bin_labels.append(f'{left:.1f}–{interval.right:.1f}')

    hist_df = pd.DataFrame({'Bereich': bin_labels, 'Häufigkeit': hist_counts.values})

 
    hist_chart = alt.Chart(hist_df).mark_bar(color='#2A78D6').encode(
        x=alt.X('Bereich:N', sort=bin_labels, title=NUMERIC_VARS[feature]),
        y=alt.Y('Häufigkeit:Q', title='Häufigkeit'),
        tooltip=['Bereich', 'Häufigkeit'],
    )
    st.altair_chart(hist_chart, width='stretch')

    st.markdown('---')

    st.subheader('Zusammenhang: Spielstunden vs. Angst-Score (GAD-7)')

    x_var, y_var = 'Hours', 'GAD_T'
    plot_df = pd.DataFrame({
        'x': filtered_df[x_var].values,
        'y': filtered_df[y_var].values,
    }).dropna()

    scatter = alt.Chart(plot_df).mark_circle(size=40, opacity=0.35, color='#2A78D6').encode(
        x=alt.X('x:Q', title=NUMERIC_VARS[x_var], scale=alt.Scale(zero=False)),
        y=alt.Y('y:Q', title=NUMERIC_VARS[y_var], scale=alt.Scale(zero=False)),
        tooltip=[alt.Tooltip('x:Q', title=NUMERIC_VARS[x_var]), alt.Tooltip('y:Q', title=NUMERIC_VARS[y_var])],
    )

    chart = scatter
    if plot_df['x'].nunique() > 1:
        bin_df = plot_df.copy()
        bin_df['bin'] = pd.qcut(bin_df['x'], q=10, duplicates='drop')
        trend = bin_df.groupby('bin', observed=True)[['x', 'y']].mean().reset_index(drop=True)
        trend_line = alt.Chart(trend).mark_line(color='#E34948', size=3).encode(
            x=alt.X('x:Q', scale=alt.Scale(zero=False)),
            y=alt.Y('y:Q', scale=alt.Scale(zero=False)),
        )
        chart = scatter + trend_line
        st.caption(f'Rote Linie: mittlerer {NUMERIC_VARS[y_var]}-Wert je {NUMERIC_VARS[x_var]}-Dezil (Trend)')

    st.altair_chart(chart, width='stretch')

    r = plot_df[['x', 'y']].corr().iloc[0, 1]
    st.write(f'Pearson-Korrelationskoeffizient: **r = {r:.3f}**')

    st.markdown('---')

    # Gruppenvergleich des Angst-Scores nach Motivation, Spielstil, etc.
    st.subheader('Gruppenvergleich: Angst-Score (GAD-7) nach Spielmotivation')

    group_labels = {
        'whyplay_clean': 'Spielmotivation',
        'Playstyle_clean': 'Spielstil',
        'Gender': 'Geschlecht',
        'Platform': 'Plattform',
    }
    group_var = st.selectbox(
        'Gruppierung nach:',
        list(group_labels.keys()),
        format_func=lambda k: group_labels[k]
    )

    group_counts = filtered_df[group_var].value_counts()
    valid_groups = group_counts[group_counts >= 5].index.tolist()
    plot_df = filtered_df[filtered_df[group_var].isin(valid_groups)]

    if len(valid_groups) >= 2:
        group_stats = plot_df.groupby(group_var, observed=True)['GAD_T'].agg(
            ['mean', 'median', 'std', 'count']
        ).round(2)
        group_stats = group_stats.reindex(valid_groups)
        group_stats.columns = ['Mittelwert', 'Median', 'Std.-Abw.', 'N']

        
        group_plot_df = group_stats.reset_index().rename(columns={group_var: 'Gruppe'})
        group_chart = alt.Chart(group_plot_df).mark_bar(color='#2A78D6').encode(
            x=alt.X('Mittelwert:Q', title='Ø GAD-7 Score'),
            y=alt.Y('Gruppe:N', title=None, sort='-x'),
            tooltip=['Gruppe', 'Mittelwert', 'Median', 'Std.-Abw.', 'N'],
        )
        st.altair_chart(group_chart, width='stretch')
        st.dataframe(group_stats, width='stretch')
    else:
        st.info('Zu wenige Gruppen mit ausreichend Datenpunkten für die aktuelle Filterauswahl.')

    st.markdown('---')

    st.write(
        'Datenquelle: [Online Gaming Anxiety Data (Kaggle)]'
        '(https://www.kaggle.com/datasets/divyansh22/online-gaming-anxiety-data/data)'
    )
    st.caption('Modul Data Science · Selcan Ipek-Ugay, Felix Bießmann · Lukas Kinzel')


if __name__ == '__main__':
    main()
