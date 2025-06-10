from flask import Flask, request, jsonify
from openai import OpenAI
from helper import parse_prompt_template, parse_regen_system_prompt_template
from output_formats import Quiz_V1

app = Flask(__name__)

KEY = "your-key-here"
client = OpenAI(api_key = KEY)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Flask API is running."})

current_temp_asset = None

@app.route("/generate", methods=["POST"])
def generate():
    global current_temp_asset
    try:
        data = request.get_json()
        building_block = data.get("building_block")
        user_inputs = data.get("variables")

        if not building_block or not user_inputs:
            return jsonify({"error": "Missing 'building_block' or 'variables'"}), 400

        # Generate the full prompt using your helper
        full_prompt = parse_prompt_template(building_block, user_inputs)

        # Send to OpenAI
        response = client.responses.create(
            model="gpt-4.1",
            input=[
                {"role": "user", "content": full_prompt},
            ]
        )
        ai_reply = response.output_text
        current_temp_asset = ai_reply
        return ai_reply

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/regenerate", methods=["POST"])
def regenerate():
    global current_temp_asset
    try:
        data = request.get_json()
        building_block = data.get("building_block")
        temp_asset = current_temp_asset
        query = data.get("query")

        if not building_block or not temp_asset or not query:
            return jsonify({"error": "Missing 'building_block' or 'temp_asset' or 'query'"}), 400

        # Generate the full prompt using your helper
        system_prompt = parse_regen_system_prompt_template(building_block, temp_asset)

        # Send to OpenAI
        response = client.responses.create(
            model="gpt-4.1",
            input=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": query
                },
            ]
        )
        ai_reply = response.output_text
        current_temp_asset = ai_reply
        return ai_reply

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)