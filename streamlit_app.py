import streamlit as st
import os
import datetime
from mistralai import Mistral
from dotenv import load_dotenv

# --- ЗАГРУЗКА НАСТРОЕК ---
load_dotenv()
api_key = os.getenv("MISTRAL_API_KEY", "Ybw8mXxtjlIQIpy1xVSZU5Cap1V1unta")
admin_password = os.getenv("ADMIN_PASSWORD", "admin123") # Пароль по умолчанию

if not api_key:
    st.error("Ошибка: MISTRAL_API_KEY не найден в .env")
    st.stop()

client = Mistral(api_key=api_key)
LOG_FILE = "chat_log.txt"

# --- ФУНКЦИИ ---
def save_to_log(user_id, user_text, bot_response):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] ID:{user_id} | USER: {user_text} | BOT: {bot_response}\n")

# --- ИНТЕРФЕЙС И АВТОРИЗАЦИЯ ---
st.set_page_config(page_title="AI Support System", layout="wide")

# Боковая панель для входа
with st.sidebar:
    st.title("🔐 Вход")
    role = st.radio("Выберите роль:", ["Пользователь", "Администратор"])
    
    is_admin = False
    if role == "Администратор":
        pwd = st.text_input("Введите пароль администратора:", type="password")
        if pwd == admin_password:
            is_admin = True
            st.success("Доступ разрешен!")
        elif pwd:
            st.error("Неверный пароль")

# --- ЛОГИКА АДМИНИСТРАТОРА ---
if is_admin:
    st.header("👨‍💻 Панель управления (Админ)")
    
    if st.button("Обновить логи"):
        st.rerun()

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = f.readlines()
        
        st.text_area("История всех запросов пользователей:", value="".join(logs[-20:]), height=400)
        
        with open(LOG_FILE, "rb") as file:
            st.download_button("Скачать полный лог (.txt)", data=file, file_name="support_logs.txt")
    else:
        st.info("Логов пока нет.")
    
    if st.button("Очистить все логи"):
        open(LOG_FILE, 'w').close()
        st.success("Логи очищены")
        st.rerun()

# --- ЛОГИКА ПОЛЬЗОВАТЕЛЯ ---
else:
    st.header("🤖 Чат поддержки")
    
    # Инициализация сессии
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "user_id" not in st.session_state:
        st.session_state.user_id = datetime.datetime.now().strftime("%H%M%S")

    # Отображение чата
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Ввод сообщения
    if prompt := st.chat_input("Ваш вопрос..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 1. Быстрый FAQ
        if "цена" in prompt.lower():
            response = "Наши услуги стоят от 1000 рублей."
        
        # 2. Переключение на админа (триггер)
        elif any(w in prompt.lower() for w in ["админ", "человек", "оператор"]):
            response = "⚠️ Запрос передан администратору. Он увидит ваше сообщение в панели управления."
        
        # 3. AI ответ (Mistral)
        else:
            with st.spinner("🤖 Бот печатает..."):
                try:
                    history = [{"role": "system", "content": "Ты поддержка клиентов."}] + st.session_state.messages[-5:]
                    res = client.chat.complete(model="mistral-small-latest", messages=history)
                    response = res.choices[0].message.content
                except Exception as e:
                    response = f"Ошибка: {e}"

        # Сохранение и вывод
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)
        
        # Запись в общий лог для админа
        save_to_log(st.session_state.user_id, prompt, response)

    # Подсказки
    with st.expander("Доступные команды"):
        st.write("Спросите про 'цены' или напишите 'позови админа'")