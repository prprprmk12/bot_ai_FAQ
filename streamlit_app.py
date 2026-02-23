import streamlit as st
import os
from mistralai import Mistral
from dotenv import load_dotenv

# --- ЗАГРУЗКА ОКРУЖЕНИЯ ---
load_dotenv()  # Загружает переменные из файла .env
api_key = os.getenv("MISTRAL_API_KEY")

# Проверка наличия ключа
if not api_key:
    st.error("Ошибка: API-ключ не найден в .env файле!")
    st.stop()

# Инициализация клиента
client = Mistral(api_key=api_key)

# --- КОНФИГУРАЦИЯ И FAQ ---
st.set_page_config(page_title="AI Support Bot", page_icon="🤖")

FAQ_DATA = {
    "как вернуть товар?": "Возврат возможен в течение 14 дней.",
    "сроки доставки": "Доставка занимает 2-5 рабочих дней.",
}

# --- СОСТОЯНИЕ (История и Админ) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "is_admin_needed" not in st.session_state:
    st.session_state.is_admin_needed = False

# --- ИНТЕРФЕЙС ---
st.title("🤖 AI Support (Mistral + ENV)")

# Сайдбар
with st.sidebar:
    st.info(f"API Ключ загружен: {api_key[:4]}***")
    if st.button("Очистить чат"):
        st.session_state.messages = []
        st.session_state.is_admin_needed = False
        st.rerun()

# Отображение чата
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- ЛОГИКА ---
if prompt := st.chat_input("Напишите нам..."):
    # Добавляем сообщение пользователя
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 1. Проверка на админа
    if any(word in prompt.lower() for word in ["админ", "оператор", "человек"]):
        st.session_state.is_admin_needed = True
        response = "🔔 Запрос передан администратору. Ожидайте ответа."
    
    # 2. Проверка FAQ
    elif any(q in prompt.lower() for q in FAQ_DATA):
        for q, a in FAQ_DATA.items():
            if q in prompt.lower():
                response = f"🤖 (FAQ): {a}"
                break
                
    # 3. Запрос к Mistral
    else:
        with st.spinner("Думаю..."):
            # Формируем контекст (последние 5 сообщений для экономии)
            context = [{"role": "system", "content": "Ты поддержка. Отвечай кратко."}]
            context += st.session_state.messages[-5:]
            
            try:
                chat_res = client.chat.complete(
                    model="mistral-small-latest",
                    messages=context
                )
                response = chat_res.choices[0].message.content
            except Exception as e:
                response = f"Ошибка Mistral: {e}"

    # Сохраняем и выводим ответ бота
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)

if st.session_state.is_admin_needed:
    st.warning("⚠️ Соединяем с оператором...")