import os
from dataclasses import dataclass
import datetime

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

def prompt_form(con, cur, prompt_id=None):
    if prompt_id:
        cur.execute("SELECT * FROM prompts WHERE id = %s", (prompt_id,))
        p = cur.fetchone()
        default = Prompt(p[1], p[2], p[3], p[4], p[5])
    else:
        default = Prompt("", "", False)

    with st.form(key="prompt_form"):
        title = st.text_input("Title", value=default.title)
        prompt_content = st.text_area("Prompt", height=200, value=default.prompt)
        is_favorite = st.checkbox("Favorite", value=default.is_favorite)

        submitted = st.form_submit_button("Submit")
        if submitted:
            if not title or not prompt_content:
                st.error('Please fill in both the title and prompt fields.')
                return
            if prompt_id:
                cur.execute(
                    "UPDATE prompts SET title = %s, prompt = %s, is_favorite = %s WHERE id = %s",
                    (title, prompt_content, is_favorite, prompt_id)
                )
            else:
                cur.execute(
                    "INSERT INTO prompts (title, prompt, is_favorite) VALUES (%s, %s, %s)",
                    (title, prompt_content, is_favorite)
                )
            con.commit()
            st.success("Prompt saved successfully!")
            st.experimental_rerun()

def display_prompts(cur, search_query, sort_order):
    query = "SELECT * FROM prompts"
    if search_query:
        query += " WHERE title ILIKE %s OR prompt ILIKE %s"
    query += " ORDER BY " + ("is_favorite DESC," if sort_order == "Favorites" else "") + "created_at DESC"
    cur.execute(query, (f'%{search_query}%', f'%{search_query}%') if search_query else None)
    prompts = cur.fetchall()
    for p in prompts:
        with st.expander(p[1]):
            st.code(p[2])
            if st.button("Edit", key=f'edit-{p[0]}'):
                prompt_form(con, cur, p[0])
            if st.button("Delete", key=f'delete-{p[0]}'):
                cur.execute("DELETE FROM prompts WHERE id = %s", (p[0],))
                con.commit()
                st.experimental_rerun()
            if st.button("Toggle Favorite", key=f'fav-{p[0]}'):
                cur.execute("UPDATE prompts SET is_favorite = NOT is_favorite WHERE id = %s", (p[0],))
                con.commit()
                st.experimental_rerun()

if __name__ == "__main__":
    st.title("Promptbase")
    st.subheader("A simple app to store and retrieve prompts")

    con, cur = setup_database()

    search_query = st.text_input("Search Prompts")
    sort_order = st.radio("Sort by", ["Date", "Favorites"])

    if st.button("Add New Prompt"):
        prompt_form(con, cur)

    display_prompts(cur, search_query, sort_order)
    con.close()

