import streamlit as st

st.set_page_config(page_title="Вход и регистрация")

st.html("""
<style>
.st-key-auth_area {
    min-height: 75vh;
}

.st-key-auth_card {
    border-radius: 20px;
    padding: 24px;
}
</style>
""")

if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "register"


def switch_mode():
    if st.session_state.auth_mode == "register":
        st.session_state.auth_mode = "login"
    else:
        st.session_state.auth_mode = "register"


is_register = st.session_state.auth_mode == "register"

title = "Регистрация" if is_register else "Вход в аккаунт"
submit_label = "Зарегистрироваться" if is_register else "Войти"
switch_label = (
    "Уже есть аккаунт? Войти"
    if is_register
    else "Нет аккаунта? Зарегистрироваться"
)

with st.container(
    key="auth_area",
    horizontal=True,
    horizontal_alignment="center",
    vertical_alignment="center",
):
    with st.container(key="auth_card", width=380, border=True):
        st.header(title)

        with st.form(key=f"auth_{st.session_state.auth_mode}", border=False):
            email = st.text_input(
                "Электронная почта",
                placeholder="name@example.com",
                autocomplete="email",
            )
            password = st.text_input(
                "Пароль",
                type="password",
                autocomplete="new-password" if is_register else "current-password",
            )
            submitted = st.form_submit_button(
                submit_label,
                type="primary",
                width="stretch",
            )

        if submitted:
            if not email.strip() or not password:
                st.error("Введи почту и пароль.")
            elif "@" not in email:
                st.error("Проверь адрес электронной почты.")
            else:
                st.info("Форма отправлена. Здесь можно подключить обработку аккаунта.")

        st.button(
            switch_label,
            type="tertiary",
            width="stretch",
            on_click=switch_mode,
        )