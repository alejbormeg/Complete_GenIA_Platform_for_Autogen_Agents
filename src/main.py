import gradio as gr
import requests

backend_url = "http://localhost:8000"

def upload_document(file):
    with open(file.name, "rb") as f:
        response = requests.post(f"{backend_url}/uploadfile/", files={"file": f})
    return response.json()

def process_query(query_text, sql_sentence):
    response = requests.post(
        f"{backend_url}/processquery/",
        json={"query_text": query_text, "sql_sentence": sql_sentence},
    )
    return response.json()["agent_responses"]

with gr.Blocks() as demo:
    gr.Markdown("# NL2SQL Conversation Agent")

    with gr.Row():
        with gr.Column(scale=1):
            file_input = gr.File(label="Upload PDF/DOC", type="filepath")
            file_output = gr.JSON()
            file_input.change(upload_document, file_input, file_output)

            query_input = gr.Textbox(lines=3, placeholder="Write your query here...", label="Query")
            sql_input = gr.Textbox(lines=3, placeholder="Write your SQL sentence here...", label="SQL Sentence")

            process_button = gr.Button("Process")
            response_output = gr.Textbox(label="Agent Responses", lines=10, interactive=False, placeholder="Agent responses will appear here...")
            process_button.click(process_query, [query_input, sql_input], response_output)

        with gr.Column(scale=2):
            conversation_history = gr.Textbox(label="Conversation History", lines=20, interactive=False, placeholder="Full conversation will appear here...", elem_id="scrollable-conversation")

demo.launch()
