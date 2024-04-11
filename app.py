import os
import datetime
from dataclasses import dataclass

import streamlit as st
import psycopg2
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Prompt:
    title: str
    prompt: str
    is_favorite: bool
    created_at: datetime.datetime = None
    updated_at: datetime.datetime = None

def setup_database():
    con = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS prompts (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            prompt TEXT NOT NULL,
            is_favorite BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    con.commit()
    return con, cur

def prompt_form(prompt=None):
    default = Prompt("", "", False) if prompt is None else prompt
    with st.form(key="prompt_form"):
        title = st.text_input("Title", value=default.title)
        prompt_content = st.text_area("Prompt", height=200, value=default.prompt)
        is_favorite = st.checkbox("Favorite", value=default.is_favorite)
        submitted = st.form_submit_button("Submit")
        if submitted:
            if not title or not prompt_content:
                st.error('Please fill in both the title and prompt fields.')
                return None
            return Prompt(title, prompt_content, is_favorite)

def display_prompts(cur, con):
    prompts = search_prompt_form(cur)
    for p in prompts:
        with st.expander(p[1]):
            st.code(p[2])
            fav_status = "Unfavorite" if p[3] else "Favorite"
            if st.button(fav_status, key=f"f{p[0]}"):
                cur.execute("UPDATE prompts SET is_favorite = NOT is_favorite WHERE id = %s", (p[0],))
                con.commit()
                st.experimental_rerun()
            if st.button("Edit", key=f"e{p[0]}"):
                prompt_data = Prompt(p[1], p[2], p[3], p[4], p[5])
                edited_prompt = prompt_form(prompt_data)
                if edited_prompt:
                    cur.execute(
                        "UPDATE prompts SET title = %s, prompt = %s, is_favorite = %s WHERE id = %s",
                        (edited_prompt.title, edited_prompt.prompt, edited_prompt.is_favorite, p[0])
                    )
                    con.commit()
                    st.experimental_rerun()
            if st.button("Delete", key=f"d{p[0]}"):
                cur.execute("DELETE FROM prompts WHERE id = %s", (p[0],))
                con.commit()
                st.experimental_rerun()

def search_prompt_form(cur):
    search_query = st.sidebar.text_input("Search prompts")
    sort_order = st.sidebar.selectbox("Sort by", ["Newest first", "Oldest first"])
    order_sql = "DESC" if sort_order == "Newest first" else "ASC"

    if search_query:
        cur.execute(
            "SELECT * FROM prompts WHERE title ILIKE %s OR prompt ILIKE %s ORDER BY created_at " + order_sql,
            (f'%{search_query}%', f'%{search_query}%')
        )
    else:
        cur.execute(f"SELECT * FROM prompts ORDER BY created_at {order_sql}")
    return cur.fetchall()

if __name__ == "__main__":
    st.title("Promptbase")
    st.subheader("A simple app to store and retrieve prompts")

    con, cur = setup_database()
    new_prompt = prompt_form()
    if new_prompt:
        try:
            cur.execute(
                "INSERT INTO prompts (title, prompt, is_favorite) VALUES (%s, %s, %s)",
                (new_prompt.title, new_prompt.prompt, new_prompt.is_favorite)
            )
            con.commit()
            st.success("Prompt added successfully!")
        except psycopg2.Error as e:
            st.error(f"Database error: {e}")

    display_prompts(cur, con)
    con.close()
