import csv
import datetime
import os
import requests
import streamlit as st

st.set_page_config(page_title="Ответ на отзыв за 10 секунд — бесплатно", page_icon="⭐", layout="centered")

# --- UTM ---
UTM_KEYS = ("utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content")
for _k in UTM_KEYS:
    if _k not in st.session_state:
        _v = st.query_params.get(_k, "")
        st.session_state[_k] = _v[0] if isinstance(_v, list) else _v

# --- Конфиг ---
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, "leads.csv")
API_KEY = os.environ.get("AI_API_KEY", "")

# --- Жесткий ответ для негатива ---
NEGATIVE_WORDS = ["плохо", "ужасно", "недоволен", "кошмар", "отвратительно", "грубо", "долго", "обман", "хамство"]
FIXED_NEGATIVE = "Здравствуйте! Нам очень жаль, что визит оставил неприятные впечатления. Мы уже разбираемся с вашей ситуацией. Пожалуйста, свяжитесь с нами удобным для вас способом."

def send_telegram(contact, rtype):
    # Токен вписан напрямую, чтобы обойти глюки Streamlit
    token = "8975961612:AAHT8PIpggBA-GvaanvCKIsiz15mw41ZwFo"
    chat_id = "1579504425"
    
    text = f"📩 Новая заявка!\nКонтакт: {contact}\nТип: {rtype}"
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
        return resp.status_code == 200
    except:
        return False

def get_ai_response(review):
    if not API_KEY:
        return "Спасибо за ваш отзыв! Нам важно ваше мнение."
    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "Ты вежливый администратор. Напиши короткий ответ на отзыв. Поблагодари, если отзыв хороший. Спроси, что улучшить, если нейтральный."},
                    {"role": "user", "content": review}
                ],
                "max_tokens": 100
            },
            timeout=10
        )
        return resp.json()["choices"][0]["message"]["content"].strip()
    except:
        return "Спасибо за ваш отзыв!"

def generate_response(review):
    if any(w in review.lower() for w in NEGATIVE_WORDS):
        return FIXED_NEGATIVE
    return get_ai_response(review)

def save_lead(contact, rtype):
    new = not os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["timestamp", "contact", "type"] + list(UTM_KEYS))
        w.writerow([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), contact, rtype] + [st.session_state.get(k, "") for k in UTM_KEYS])

# --- Интерфейс ---
st.title("Ответ на отзыв за 10 секунд — бесплатно")
st.caption("Для автосервисов, салонов и кафе")

if "answer" not in st.session_state:
    st.session_state.answer = ""
if "lead_sent" not in st.session_state:
    st.session_state.lead_sent = False

review = st.text_area("Вставьте текст отзыва", height=150, placeholder="Например: «Долго ждал, мастер грубил»")

if st.button("Сгенерировать ответ", type="primary", disabled=not review.strip()):
    st.session_state.answer = generate_response(review)

if st.session_state.answer:
    st.subheader("Готовый ответ")
    st.info(st.session_state.answer)

    st.markdown("---")
    st.markdown("**Хотите, чтобы ИИ отвечал на все новые отзывы автоматически?**")
    st.markdown("Оформите предзаказ за **490 ₽/мес**.")
    
    if not st.session_state.lead_sent:
        contact = st.text_input("Ваш Telegram или WhatsApp")
        if st.button("Отправить заявку", type="primary"):
            if contact.strip():
                save_lead(contact.strip(), "Заявка")
                if send_telegram(contact.strip(), "Негатив" if any(w in review.lower() for w in NEGATIVE_WORDS) else "Другой"):
                    st.session_state.lead_sent = True
                    st.rerun()
                else:
                    st.error("⚠️ Ошибка Telegram. Проверьте нажатие /start в боте.")
            else:
                st.error("Введите контакт")

    if st.session_state.lead_sent:
        st.success("✅ Заявка принята! Мы свяжемся с вами.")
