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

# --- ИИ для позитива/нейтрала ---
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
    print(f"Отзыв: {review}")
    if any(w in review.lower() for w in NEGATIVE_WORDS):
        print(f"Ответ: {FIXED_NEGATIVE}")
        return FIXED_NEGATIVE
    answer = get_ai_response(review)
    print(f"Ответ: {answer}")
    return answer

# --- Сохранение заявок ---
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

review = st.text_area("Вставьте текст отзыва", height=150, placeholder="Например: «Долго ждал, мастер грубил»")

if st.button("Сгенерировать ответ", type="primary", disabled=not review.strip()):
    st.session_state.answer = generate_response(review)

if st.session_state.answer:
    st.subheader("Готовый ответ")
    st.info(st.session_state.answer)

    st.markdown("---")
    st.markdown("**Хотите, чтобы ИИ отвечал на все новые отзывы автоматически?**")
    st.markdown("Оформите предзаказ за **490 ₽/мес**. Первые 10 человек получат 2 месяца бесплатно.")
    
    contact = st.text_input("Ваш Telegram или WhatsApp")
    if st.button("Отправить заявку"):
        if contact.strip():
            save_lead(contact.strip(), "Негативный" if any(w in review.lower() for w in NEGATIVE_WORDS) else "Другой")
            st.success("✅ Заявка сохранена!")
        else:
            st.error("Введите контакт")