import streamlit as st
import pandas as pd
import re
import plotly.express as px

st.title("🚗 Автомобілі по компаніях – Інтерактивний дашборд")

st.markdown("""
            
            
**Ласкаво просимо на дашборд автомобілів!**  
Тут ви можете детально проаналізувати автомобілі різних компаній на основі широкого набору даних 2025 року.

### 👇 Мета дашборду:
- Надати інтуїтивно зрозумілий інтерфейс для порівняння автомобілів.
- Візуалізувати ключові характеристики авто: ціни, двигуни, потужність, рейтинг.
- Сформувати аналітичну картину по компаніях та їх моделях.

### 👇 Дані, що включені:
- **Назви автомобілів**  
- **Ціни та категорії цін**  
- **Тип двигуна та потужність (HorsePower)**  
- **Рейтинг авто на основі характеристик двигуна**  

Дашборд реалізовано за допомогою **Streamlit** та **Plotly**, що дозволяє легко переглядати таблиці та інтерактивні графіки.

> Автор: Бібікова Анастасія Олександрівна
""")



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
labels = [
    'Базовий мінімум', 
    'Середній мінімум', 
    'Розкішний мінімум', 
    'Розкішний максимум', 
    'Розкішний преміум мінімум', 
    'Розкішний преміум максимум'
]

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
idx = df.groupby('Company Names')['HP Powers'].idxmax()


idx = df.groupby('Company Names')['HP Powers'].idxmax()
top_models = df.loc[idx, ['Company Names', 'Cars Names', 'HorsePower', 'HP Powers']]
top_models = top_models.sort_values(by='HP Powers', ascending=False).reset_index(drop=True)

st.subheader("Таблиця авто")
st.dataframe(df.head(50))

st.subheader("Топ моделей по HorsePower")
st.dataframe(top_models[['Company Names', 'Cars Names', 'HorsePower', 'HP Powers']])

top_models_for_chart = top_models.copy()
top_models_for_chart['Company_Car'] = top_models_for_chart['Company Names'] + " - " + top_models_for_chart['Cars Names']

fig = px.pie(
    top_models_for_chart,
    names='Company_Car',
    values='HP Powers',
    title="Розподіл потужності топ-моделей авто",
)
st.plotly_chart(fig, use_container_width=True)


st.subheader("Таблиця авто")
st.dataframe(df[['Cars Names', 'Cars Prices', 'Price Category', 'score']].head(50))


st.subheader("Кількість авто по компаніях")
st.bar_chart(df['Company Names'].value_counts())

st.subheader("Топ 10 компаній по авто")
st.bar_chart(df['Company Names'].value_counts().head(10))

st.subheader("Кількість авто по категоріях цін")
st.bar_chart(df['Price Category'].value_counts().sort_index())

st.subheader("Рейтинг авто по оцінкам")
st.bar_chart(df.groupby('Cars Names')['score'].mean().sort_values(ascending=False).head(10))

st.markdown(
    """
    Інтерактивна функція Streamlit для перегляду цін на пальне.
    fuel_df — DataFrame з колонками: operator, A95_plus, A95, A92, diesel, gas, electric
    """)

def show_fuel_prices(fuel_df):
    fuel_df.columns = fuel_df.columns.str.strip()


    if len(fuel_df.columns) == 1:
        fuel_df = fuel_df.iloc[:,0].str.split(",", expand=True)
        fuel_df.columns = ["operator","A95_plus","A95","A92","diesel","gas","electric"]

    operator_choice = st.selectbox("Оберіть оператора", fuel_df['operator'])
    fuel_type_choice = st.selectbox("Оберіть тип пального", fuel_df.columns[1:])

    price = fuel_df.loc[fuel_df['operator'] == operator_choice, fuel_type_choice].values[0]
    st.write(f"Ціна на {fuel_type_choice} на {operator_choice}: {price} грн/л")

show_fuel_prices(fuel)

merged = pd.concat([df, fuel], axis=1)

merged