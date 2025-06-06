import json
from pybars import Compiler

def render_with_pybars(template_str, context):
    compiler = Compiler()
    template = compiler.compile(template_str)
    return template(context)

def parse_prompt_template(prompt_template_file, user_input):
    # Assume user_input is a dictionary with the required key-value pairs
    
    with open(f"prompts/{prompt_template_file}.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    prompt = data.get("prompt")
    subbed_prompt = render_with_pybars(prompt, user_input)
    return subbed_prompt