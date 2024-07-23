import gradio as gr
import requests

backend_url = "http://localhost:8000/api"

def upload_document(file):
    response = requests.post(
        f"{backend_url}/upload_pdf", 
        files={"file": ("file.pdf", file, "application/pdf")}, 
        data={"chunk_size": 1536, "embedding_model": "text-embedding-3-large"}
    )
    return response.json()

def execute_query(database, query):
    response = requests.post(
        f"{backend_url}/execute_query",
        json={"database": database, "query": query},
    )
    return response.json()

def process_query(task):
    response = requests.post(
        f"{backend_url}/agents_chat",
        json={"task": task},
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
            file_output = gr.JSON()
            file_input.change(upload_document, file_input, file_output)

            query_input = gr.Textbox(lines=3, placeholder="Write your SQL query here...", label="SQL Query")
            db_input = gr.Textbox(lines=1, placeholder="Database name...", label="Database Name")

            query_button = gr.Button("Execute Query")
            query_response_output = gr.JSON(label="Query Response")
            query_button.click(execute_query, [db_input, query_input], query_response_output)

            task_input = gr.Textbox(lines=3, placeholder="Describe the task here...", label="Task Description")

            process_button = gr.Button("Process Task")
            response_output = gr.Markdown(label="Agent Responses")
            process_button.click(process_query, task_input, response_output)

        with gr.Column(scale=2):
            conversation_history = gr.Markdown(label="Conversation History", elem_id="scrollable-conversation")

demo.launch()
