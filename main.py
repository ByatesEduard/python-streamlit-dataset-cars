import streamlit as st
import pandas as pd
import re
import plotly.express as px

st.set_page_config(layout="wide")  # Широкий формат для дашборду

st.title("🚗 Автомобілі по компаніях – Інтерактивний дашборд")

st.markdown("""
**Ласкаво просимо на дашборд автомобілів!**  
Тут ви можете детально проаналізувати автомобілі різних компаній на основі широкого набору даних 2025 року.
""")

# --- Зчитування даних ---
df = pd.read_csv("Cars Datasets 2025.csv", encoding='cp1251')
fuel = pd.read_csv("fuel_dataset.csv", encoding='cp1251', sep=",")
df.columns = df.columns.str.strip()
df['Company Names'] = df['Company Names'].str.strip()

# --- Обробка цін ---
def extract_price(price_str):
    if pd.isna(price_str):
        return None
    price_str = price_str.replace('$','').replace(',','').strip()
    if '-' in price_str:
        price_str = price_str.split('-')[0].strip()
    elif '/' in price_str:
        price_str = price_str.split('/')[0].strip()
    try:
        return int(price_str)
    except:
        return None

bins = [0, 20000, 50000, 100000, 150000, 400000, float('inf')]
labels = ['Базовий', 'Середній', 'Розкішний мінімум', 'Розкішний максимум', 'Преміум мінімум', 'Преміум максимум']
df['Price Category'] = pd.cut(df['Cars Prices'].apply(extract_price), bins=bins, labels=labels, include_lowest=True)

# --- Рейтинг авто ---
df['score'] = 10
def adjust_score(engine, score):
    if engine in ['1.2L Petrol', '1.4L Petrol', '2.0L Gas', '2.0L Hybrid', '2.0L Gas / 2.0L Hybrid']:
        score -= 2
    elif engine in ['2.5L Hybrid', '2.5L Hybrid / Plug-in Hybrid']:
        score -= 1
    elif engine.startswith('2.4L Turbo') or engine in ['I4', 'BOXER-4', 'BOXER-6']:
        score += 0.5
    elif engine.startswith('V6') or engine.startswith('V8') or engine.startswith('V10') or engine.startswith('V12'):
        score += 1
    return score

df['score'] = df.apply(lambda row: adjust_score(row['Engines'], row['score']), axis=1)

def extract_hp_first(hp_str):
    if pd.isna(hp_str):
        return None
    match = re.search(r'\d+', str(hp_str))
    if match:
        return int(match.group())
    return None

df['HP Powers'] = df['HorsePower'].map(extract_hp_first)

# --- Топ моделі ---
idx = df.groupby('Company Names')['HP Powers'].idxmax()
top_models = df.loc[idx, ['Company Names', 'Cars Names', 'HorsePower', 'HP Powers']].sort_values(by='HP Powers', ascending=False).reset_index(drop=True)

# --- Перший рядок ---
st.subheader("Топ моделей по HorsePower та їх потужність")
col1, col2 = st.columns([1,1.2])
with col1:
    st.dataframe(top_models[['Company Names', 'Cars Names', 'HorsePower', 'HP Powers']], height=500)
with col2:
    top_models['Company_Car'] = top_models['Company Names'] + " - " + top_models['Cars Names']
    fig = px.pie(top_models, names='Company_Car', values='HP Powers', 
                 title="Розподіл потужності топ-моделей авто", width=700, height=700)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig, use_container_width=True)

# --- Другий рядок: компанія та її авто ---
st.subheader("Вибір компанії та її автомобілів")
col3, col4 = st.columns([1,1])
with col3:
    company_choice = st.selectbox("Оберіть компанію", sorted(df['Company Names'].unique()))
    company_cars = df[df['Company Names'] == company_choice]
    st.dataframe(company_cars[['Cars Names', 'Cars Prices', 'Engines', 'HorsePower', 'HP Powers', 'score']], height=500)
with col4:
    company_cars['Car_Model'] = company_cars['Cars Names']
    fig2 = px.pie(company_cars, names='Car_Model', values='HP Powers',
                  title=f"Розподіл потужності моделей {company_choice}", width=700, height=700)
    fig2.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig2, use_container_width=True)

# --- Третій рядок: пальне ---
st.subheader("Ціни на пальне та їх розподіл")
fuel.columns = fuel.columns.str.strip()
if len(fuel.columns) == 1:
    fuel = fuel.iloc[:,0].str.split(",", expand=True)
    fuel.columns = ["operator","A95_plus","A95","A92","diesel","gas","electric"]

col5, col6 = st.columns([1,1])
with col5:
    operator_choice = st.selectbox("Оберіть оператора", fuel['operator'])
    fuel_type_choice = st.selectbox("Оберіть тип пального", fuel.columns[1:])
    price = fuel.loc[fuel['operator'] == operator_choice, fuel_type_choice].values[0]
    st.write(f"Ціна на {fuel_type_choice} на {operator_choice}: {price} грн/л")
with col6:
    fig3 = px.pie(fuel, names='operator', values='diesel', 
                  title="Розподіл цін Diesel по операторах", width=700, height=700)
    fig3.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig3, use_container_width=True)

# --- Четвертий рядок: інші графіки ---
st.subheader("Інші статистики")
col7, col8, col9 = st.columns([1,1,1])
with col7:
    st.bar_chart(df['Company Names'].value_counts(), height=350)
with col8:
    st.bar_chart(df['Price Category'].value_counts().sort_index(), height=350)
with col9:
    st.bar_chart(df.groupby('Cars Names')['score'].mean().sort_values(ascending=False).head(10), height=350)

# --- Об'єднані дані ---
merged = pd.concat([df, fuel], axis=1)
st.subheader("Об'єднані дані авто та цін на пальне")
st.dataframe(merged.head(50), height=400)
