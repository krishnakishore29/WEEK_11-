import csv
import html
import io
import os

import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st


st.set_page_config(page_title="Titanic Explorer", page_icon="🚢", layout="wide")
st.title("🚢 Titanic Passenger Explorer")
st.write("Explore the passenger data stored in your PostgreSQL database.")
database_password = st.sidebar.text_input("PostgreSQL password", type="password")


def get_connection():
    return psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "titanic_db"),
        user=os.getenv("PGUSER", "postgres"),
        password=database_password or os.getenv("PGPASSWORD", ""),
    )


def fetch_rows(query, parameters=None):
    with get_connection() as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, parameters or ())
            return [dict(row) for row in cursor.fetchall()]


def format_value(value):
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def show_table(rows, max_rows=100):
    if not rows:
        st.info("There are no rows to show.")
        return
    columns = list(rows[0].keys())
    header = "| " + " | ".join(html.escape(str(name)) for name in columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    lines = [header, divider]
    for row in rows[:max_rows]:
        values = [html.escape(format_value(row.get(name))).replace("|", "&#124;") for name in columns]
        lines.append("| " + " | ".join(values) + " |")
    st.markdown("\n".join(lines))
    if len(rows) > max_rows:
        st.caption(f"Showing the first {max_rows} of {len(rows):,} rows.")


def show_text_bar(label, value, maximum, color="#4c9be8"):
    if maximum <= 0:
        width = 0
    else:
        width = min(100, max(0, round(value / maximum * 100)))
    safe_label = html.escape(str(label))
    st.markdown(
        f"<div style='margin:8px 0'><strong>{safe_label}</strong> "
        f"<span style='float:right'>{value:,}</span>"
        f"<div style='background:#ddd;border-radius:5px;height:12px'>"
        f"<div style='background:{color};width:{width}%;height:12px;border-radius:5px'></div>"
        f"</div></div>",
        unsafe_allow_html=True,
    )


def make_csv(rows):
    if not rows:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


try:
    data = fetch_rows(
        "SELECT * FROM titanic_project.passengers ORDER BY passenger_id"
    )
except Exception as error:
    st.error(
        "I could not connect to the database. Check that PostgreSQL is running "
        "and that the password in the sidebar is correct."
    )
    st.caption(f"Details: {error}")
    st.stop()

if not data:
    st.warning("The passenger table is empty. Load the Titanic CSV first.")
    st.stop()

survived_total = sum(int(row.get("survived") or 0) for row in data)
passenger_total = len(data)
survival_rate = survived_total / passenger_total if passenger_total else 0


tab_dashboard, tab_explorer, tab_sql, tab_quiz = st.tabs(
    ["Dashboard", "Data Explorer", "SQL Lab", "Quick Quiz"]
)

with tab_dashboard:
    st.subheader("At a glance")
    first, second, third = st.columns(3)
    first.metric("Passengers", f"{passenger_total:,}")
    second.metric("Survived", f"{survived_total:,}")
    third.metric("Survival rate", f"{survival_rate:.1%}")

    class_counts = {}
    survival_by_class = {}
    for row in data:
        passenger_class = row.get("pclass")
        class_counts[passenger_class] = class_counts.get(passenger_class, 0) + 1
        key = (passenger_class, row.get("survived"))
        survival_by_class[key] = survival_by_class.get(key, 0) + 1

    st.subheader("Passengers in each class")
    class_maximum = max(class_counts.values(), default=0)
    for passenger_class in sorted(class_counts):
        show_text_bar(f"Class {passenger_class}", class_counts[passenger_class], class_maximum)

    st.subheader("Survival counts by class")
    survival_rows = []
    for passenger_class in sorted(class_counts):
        survival_rows.append(
            {
                "class": passenger_class,
                "survived": survival_by_class.get((passenger_class, 1), 0),
                "did not survive": survival_by_class.get((passenger_class, 0), 0),
            }
        )
    show_table(survival_rows)

with tab_explorer:
    st.subheader("Find passengers")
    classes = sorted({row.get("pclass") for row in data if row.get("pclass") is not None})
    sexes = sorted({row.get("sex") for row in data if row.get("sex")})
    class_choices = st.multiselect("Passenger class", classes, default=classes)
    sex_choices = st.multiselect("Sex", sexes, default=sexes)
    name_search = st.text_input("Name contains", "").strip().lower()
    filtered = [
        row for row in data
        if row.get("pclass") in class_choices
        and row.get("sex") in sex_choices
        and name_search in str(row.get("name", "")).lower()
    ]
    st.write(f"Showing {len(filtered):,} passenger(s)")
    show_table(filtered, max_rows=100)
    st.download_button(
        "Download these rows as CSV",
        data=make_csv(filtered),
        file_name="titanic_passengers.csv",
        mime="text/csv",
        disabled=not filtered,
    )

with tab_sql:
    st.subheader("Try a read-only SQL question")
    examples = {
        "Passenger counts by class": (
            "SELECT pclass, COUNT(*) AS passengers "
            "FROM titanic_project.passengers GROUP BY pclass ORDER BY pclass"
        ),
        "Survival counts by sex": (
            "SELECT sex, survived, COUNT(*) AS passengers "
            "FROM titanic_project.passengers "
            "GROUP BY sex, survived ORDER BY sex, survived"
        ),
        "Average age by class": (
            "SELECT pclass, ROUND(AVG(age)::numeric, 1) AS average_age "
            "FROM titanic_project.passengers GROUP BY pclass ORDER BY pclass"
        ),
        "Fare statistics by class": (
            "SELECT pclass, ROUND(AVG(fare)::numeric, 2) AS average_fare, "
            "MIN(fare) AS lowest_fare, MAX(fare) AS highest_fare "
            "FROM titanic_project.passengers GROUP BY pclass ORDER BY pclass"
        ),
    }
    choice = st.selectbox("Choose a question", list(examples))
    st.code(examples[choice], language="sql")
    try:
        show_table(fetch_rows(examples[choice]))
    except Exception as error:
        st.error("That database question did not work.")
        st.caption(f"Details: {error}")

with tab_quiz:
    st.subheader("Quick quiz")
    answer = st.radio(
        "How many passenger classes are in this dataset?",
        ["2", "3", "4"],
    )
    if st.button("Check my answer"):
        if answer == "3":
            st.success("Correct! The classes are 1, 2, and 3.")
        else:
            st.info("Try again: the passenger classes are 1, 2, and 3.")

