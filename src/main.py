import gradio as gr
import requests
import pandas as pd
import sqlparse

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

def upload_document(file, database):
    response = requests.post(
        f"{backend_url}/upload_pdf", 
        files={"file": ("file.pdf", file, "application/pdf")}, 
        data={"chunk_size": "1536", "embedding_model": "text-embedding-3-large", "database": database}
    )
    return response.json()

def execute_query(database, query):
    response = requests.post(
        f"{backend_url}/execute_query",
        json={"database": database, "query": query},
    )
    result = response.json()
    
    # Print the result for debugging
    print("Query Result:", result)
    
    # Extract column names from the query
    columns = extract_column_names(query)
    if not columns:
        columns = ["Column1", "Column2"]  # Default column names if extraction fails
    
    # Assuming result is a list of lists
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

with gr.Blocks(css=".scrollable-conversation {max-height: 600px; overflow-y: auto;}") as demo:
    gr.Markdown("# NL2SQL Conversation Agent")

    with gr.Row():
        with gr.Column(scale=1):
            file_input = gr.File(label="Upload PDF/DOC", type="binary")
            file_db_input = gr.Textbox(lines=1, placeholder="Database name...", label="Database Name for File")
            file_output = gr.JSON()
            file_input.change(upload_document, [file_input, file_db_input], file_output)

            query_input = gr.Textbox(lines=3, placeholder="Write your SQL query here...", label="SQL Query")
            db_input = gr.Textbox(lines=1, placeholder="Database name...", label="Database Name")

            query_button = gr.Button("Execute Query")
            query_response_output = gr.DataFrame(label="Query Response")
            query_button.click(execute_query, [db_input, query_input], query_response_output)

            task_input = gr.Textbox(lines=3, placeholder="Describe the task here...", label="Task Description")
            task_db_input = gr.Textbox(lines=1, placeholder="Database name...", label="Database Name for Task")

            process_button = gr.Button("Process Task")
            response_output = gr.Markdown(label="Agent Responses")
            process_button.click(process_query, [task_input, task_db_input], response_output)
            conversation_history = gr.Markdown(label="Conversation History", elem_id="scrollable-conversation")

demo.launch()
