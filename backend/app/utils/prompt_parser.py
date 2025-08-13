from ast import parse
import json
from jinja2 import Template
import os


class PromptParser:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # points to backend/app

    def _load_template_json(self, template_file_path):
        print(f"Trying to load prompt template: {template_file_path}")  # Add this line
        # Given a file path, loads the prompt template from the JSON file.
        if not os.path.exists(template_file_path):
            raise FileNotFoundError(f"Prompt template file not found: {template_file_path}")
        with open(template_file_path, 'r', encoding='utf-8') as file:
            return json.load(file)

    def _get_prompt_path(self, relative_path):
        return os.path.join(self.base_dir, relative_path)

    def render_prompt(self, template_file_path, input_variables):
        # Given a file path and a dict of input variables, substitutes the variables in the prompt and returns the rendered prompt.
        data = self._load_template_json(template_file_path)
        prompt_template = data.get('prompt')
        required_vars = data.get('required_input_variables', [])
        optional_vars = data.get('optional_input_variables', [])

        # Validate required variables
        missing = [var for var in required_vars if var not in input_variables]
        if missing:
            raise ValueError(f"Missing required input variables for prompt: {missing}")

        # Only retrieve the required & optional variables for this prompt from the input_variables dict
        context = {
            variable_name: variable_value
            for variable_name, variable_value in input_variables.items()
            if variable_name in required_vars or variable_name in optional_vars
        }
        template = Template(prompt_template)
        return template.render(**context)
    
    def get_asset_prompt(self, asset_name: str, input_variables: dict):
        # Combines the required system prompts with the asset-specific prompt to get the full asset prompt.
        # TODO: Here the logic for combining prompts is hard-coded. Needs to be implemented based on pre-defined rules.
        # NOTE: An assumption being made is that system prompt names are unique and will never appear in asset prompts.
        full_asset_prompt = self.render_prompt(
            self._get_prompt_path("prompts/system/settings.json"), input_variables
        ) + "\n\n" + self.render_prompt(
            self._get_prompt_path(f"prompts/asset/{asset_name}.json"), input_variables
        )
        return full_asset_prompt