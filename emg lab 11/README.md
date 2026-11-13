# Titanic Database Lab

The Titanic CSV and starter files for the PostgreSQL, Python, and Streamlit lab.

## 1. Load the data into PostgreSQL

Open the VS Code terminal and start the PostgreSQL command-line tool:

```powershell
& 'C:\Program Files\PostgreSQL\18\bin\psql.exe' -h localhost -U postgres -d postgres
```

Type your PostgreSQL password when asked. The password will not appear as you type.

At the `postgres=#` prompt, run these commands one at a time:

```text
\i 'C:/Users/krish/OneDrive/Desktop/emg lab 11/01_create_database.sql'
\c titanic_db
\i 'C:/Users/krish/OneDrive/Desktop/emg lab 11/02_setup_tables.sql'
```

The CSV import should say `COPY 891`; the transfer into the final table should say `INSERT 0 891`.

## 2. Install the Python packages

In a new VS Code terminal (PowerShell), run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## 3. Open the app

```powershell
python -m streamlit run app.py
```

The browser page asks for your PostgreSQL password in its sidebar. It is used only to connect to your local database and is not saved by this app.
