import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import plotly.express as px
from sklearn.linear_model import LinearRegression

# Заглавие
st.title('Анализ погоды')
st.write('Интерактивное приложение')


# Шаг 1
st.header('Шаг 1: Загрузка данных')

## Загрузка данных
file = st.file_uploader('Выберите csv файл', type=['csv'])
if file is not None:
    data = pd.read_csv(file)
    st.dataframe(data.head())
else:
    st.write('выберите csv файл')

## Обработка
### скользящее среднее температуры
def rol_temp(data):
    data['rol_temp'] = data['temperature'].rolling(30, center=True, min_periods=1).mean()
    return data
### СКО для города, сезона
def season_city_stat(data):
    city_seas_stat = data.groupby(['city', 'season'], as_index=False) \
                         .agg(mean_temp = ('temperature', 'mean'),
                              std_temp = ('temperature', 'std'))
    data = data.merge(city_seas_stat,
                        on=['city', 'season'])
    return data
def stat_calc(df):
    df_1 = rol_temp(df)
    df_2 = season_city_stat(df_1)
    return df_2
### аномалии
def is_outlier(row):
        '''
        проверка, выбросное ли значение
        '''
        outlier_mark = row['temperature'] > row['mean_temp'] + 2 * row['std_temp'] or row['temperature'] < row['mean_temp'] - 2 * row['std_temp']
        return outlier_mark

## полный дф
data = stat_calc(data)
data['is_outlier'] = data.apply(is_outlier, axis=1)


# Шаг 2
st.header('Шаг 2: Выбор города')

## Выпадающий список с городами
options = data['city'].unique()
selected_city = st.selectbox('Выберите город:', options)


# Шаг 3
st.header('Шаг 3: Статистика по городу')

## опис стат для города
city_data = data.query('city == @selected_city')
st.dataframe(city_data['temperature'].describe())
## сезонные профили (среднее, СКО)
season_stat = city_data.groupby('season', as_index=False) \
                       .agg({'mean_temp': 'first',
                             'std_temp': 'first'})
st.dataframe(season_stat)
## временной ряд с аномалиями
# Установка цвета на основе столбца 'is_outlier'
city_data['color'] = city_data['is_outlier'].apply(lambda x: 'red' if x else 'green')
# Создание графика
fig = px.scatter(city_data, x='timestamp', y='temperature', color='color', color_discrete_sequence = ['green', 'red'], title='Временной ряд с подсветкой выбросов', )
# Добавление линий между точками
fig.add_scatter(x=city_data['timestamp'], y=city_data['temperature'], mode='lines', line=dict(color='black'))
# Переменная, содержащая цвет точек
fig.for_each_trace(lambda t: t.update(marker=dict(size=10)))
# Показываем график
st.plotly_chart(fig)


# Шаг 4
st.header('Шаг 4: Актуальная температура в выбранном городе')

def get_current_temperature(city, api_key):
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': city,
        'appid': api_key,
        'units': 'metric'  # Используем метрическую систему (Цельсий)
    }
    # Выполняем GET-запрос
    response = requests.get(base_url, params=params)

    # Проверяем, успешен ли запрос
    if response.status_code == 200:
        resp = response.json()
        # Извлекаем температуру
        resp_temp = resp['main']['temp']
        return resp_temp
    else:
        return f"Ошибка при получении данных: {response.status_code}, {response.text}"

## Ввод API
api_input = st.text_input("Введите API ключ:")

## Получение и обработка информации
### получение данных
temperature = get_current_temperature(selected_city, api_input)
### сравнение с историческими данными
def get_season(month):
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    elif month in [9, 10, 11]:
        return "autumn"

current_month = datetime.now().month
season = get_season(current_month)

seas_info = season_stat.query('season == @season')
if (temperature > seas_info['mean_temp'].values + 2 * seas_info['std_temp'].values) or (temperature < seas_info['mean_temp'].values - 2 * seas_info['std_temp'].values):
    outlier_info = 'Температура аномальна'
else:
    outlier_info = 'Температура адекватна'

## Отображение
st.write(f'Температура в {selected_city}: ' + str(temperature) + ' по Цельсию')
st.write(outlier_info)



