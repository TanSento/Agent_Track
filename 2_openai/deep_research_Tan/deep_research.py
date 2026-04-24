import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)


async def get_questions(query: str):
    if not query.strip():
        return gr.update(), gr.update(), gr.update()
    questions = await ResearchManager().get_clarifications(query)
    formatted = "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))
    return (
        gr.update(value=formatted, visible=True),
        gr.update(visible=True),
        gr.update(visible=True),
    )


async def run(query: str, answers: str):
    async for chunk in ResearchManager().run(query, answers):
        yield chunk


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research")

    query_textbox = gr.Textbox(label="What topic would you like to research?")
    clarify_button = gr.Button("Start", variant="secondary")

    questions_display = gr.Markdown(visible=False)
    answers_textbox = gr.Textbox(
        label="Your answers (optional — leave blank to skip)",
        lines=5,
        visible=False,
    )
    run_button = gr.Button("Run Research", variant="primary", visible=False)
    report = gr.Markdown(label="Report")

    clarify_button.click(
        fn=get_questions,
        inputs=query_textbox,
        outputs=[questions_display, answers_textbox, run_button],
    )
    query_textbox.submit(
        fn=get_questions,
        inputs=query_textbox,
        outputs=[questions_display, answers_textbox, run_button],
    )

    run_button.click(fn=run, inputs=[query_textbox, answers_textbox], outputs=report)

ui.launch(inbrowser=True)
