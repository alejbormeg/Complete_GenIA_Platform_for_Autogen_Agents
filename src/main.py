import gradio as gr
import requests
import pandas as pd
import sqlparse
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

backend_url = "http://localhost:8000/api"

def extract_column_names(query):
    parsed = sqlparse.parse(query)[0]
    tokens = parsed.tokens
    columns = []
    select_found = False
    for token in tokens:
        if token.ttype is sqlparse.tokens.DML and token.value.upper() == "SELECT":
            select_found = True
        if select_found and token.ttype is sqlparse.tokens.Wildcard:
            columns.append(token.value)
        elif select_found and isinstance(token, sqlparse.sql.IdentifierList):
            for identifier in token.get_identifiers():
                columns.append(identifier.get_real_name())
    return columns

def upload_document(file, database, new_database):
    db_name = database if not new_database else new_database
    response = requests.post(
        f"{backend_url}/upload_pdf", 
        files={"file": ("file.pdf", file, "application/pdf")}, 
        data={"chunk_size": "1536", "embedding_model": "text-embedding-3-large", "database": db_name}
    )
    return response.json()

def execute_query(database, query):
    response = requests.post(
        f"{backend_url}/execute_query",
        json={"database": database, "query": query},
    )
    result = response.json()
    print("Query Result:", result)
    columns = extract_column_names(query)
    if not columns:
        columns = ["Column1", "Column2"]
    if isinstance(result, list):
        df = pd.DataFrame(result, columns=columns)
        return df
    return result

def process_query(task, database):
    response = requests.post(
        f"{backend_url}/agents_chat",
        json={"task": task, "database": database},
    )
    messages = response.json()
    formatted_messages = ""
    for message in messages:
        if "content" in message:
            formatted_messages += f"**{message['name']}** ({message['role']}): <span style='color:blue'>{message['content']}</span>\n\n"
        elif "function_call" in message:
            formatted_messages += f"**{message['name']}** ({message['role']}): <span style='color:green'>Function Call - {message['function_call']['name']} with arguments {message['function_call']['arguments']}</span>\n\n"
    return formatted_messages.strip()

def fetch_databases():
    conn = psycopg2.connect(
        host=os.getenv("POSTGRESQL_HOST"),
        port=os.getenv("POSTGRESQL_PORT"),
        database=os.getenv("POSTGRESQL_DATABASE"),
        user=os.getenv("POSTGRESQL_USER"),
        password=os.getenv("POSTGRESQL_PASSWORD")
    )
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT database FROM vector_embeddings_1536 WHERE database IS NOT NULL ORDER BY database")
    databases = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    databases.insert(0, "All")  # 'All' option is added at the beginning after sorting
    return databases

def refresh_dropdown(input_val):
    return gr.update(choices=fetch_databases())

# Define the main Blocks interface
with gr.Blocks() as demo:
    gr.Markdown("# NL2SQL Conversation Agent")
    gr.Markdown("This interface allows you to upload documents, execute SQL queries, and process tasks using a conversational agent.")

    with gr.Tabs():
        with gr.Tab("Upload Document"):
            with gr.Row():
                with gr.Column(scale=1):
                    file_input = gr.File(label="Upload PDF/DOC", type="binary")
                    db_dropdown_pdf = gr.Dropdown(choices=fetch_databases(), label="Select Database for PDF Upload")
                    new_db_input = gr.Textbox(placeholder="Or enter a new database name", label="New Database Name")
                    file_output = gr.JSON()
                    file_input.change(upload_document, [file_input, db_dropdown_pdf, new_db_input], file_output)
                    refresh_button_pdf = gr.Button("Refresh Databases")
                    refresh_button_pdf.click(refresh_dropdown, [], outputs=[db_dropdown_pdf])

        with gr.Tab("Execute SQL Query"):
            with gr.Column(scale=1):
                db_dropdown_query = gr.Dropdown(choices=fetch_databases(), label="Select Database for SQL Query")
                query_input = gr.Textbox(lines=3, placeholder="Write your SQL query here...", label="SQL Query")
                query_button = gr.Button("Execute Query")
                query_response_output = gr.DataFrame(label="Query Response")
                query_button.click(execute_query, [db_dropdown_query, query_input], query_response_output)
                refresh_button_query = gr.Button("Refresh Databases")
                refresh_button_query.click(refresh_dropdown, [], outputs=[db_dropdown_query])

        with gr.Tab("Process Task"):
            with gr.Column(scale=1):
                db_dropdown_task = gr.Dropdown(choices=fetch_databases(), label="Select Database for Task Processing")
                task_input = gr.Textbox(lines=3, placeholder="Describe the task here...", label="Task Description")
                process_button = gr.Button("Process Task")
                response_output = gr.Markdown(label="Agent Responses")
                process_button.click(process_query, [task_input, db_dropdown_task], response_output)
                refresh_button_task = gr.Button("Refresh Databases")
                refresh_button_task.click(refresh_dropdown, [], outputs=[db_dropdown_task])

# Launch the application
demo.launch()