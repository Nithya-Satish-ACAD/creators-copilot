from flask import Flask, request, jsonify
from openai import OpenAI
from helper import parse_prompt_template
from output_formats import Quiz_V1

app = Flask(__name__)

KEY = "your-key-here"
client = OpenAI(api_key = KEY)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Flask API is running."})

@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json()
        building_block = data.get("building_block")
        user_inputs = data.get("variables")

        if not building_block or not user_inputs:
            return jsonify({"error": "Missing 'building_block' or 'variables'"}), 400

        # Generate the full prompt using your helper
        full_prompt = parse_prompt_template(building_block, user_inputs)

        # Send to OpenAI
        response = client.responses.parse(
            model="gpt-4o-2024-08-06",
            input=[
                {"role": "user", "content": full_prompt},
            ],
            text_format = Quiz_V1
        )

        ai_reply = response.output_parsed
        return jsonify({
            "prompt": full_prompt,
            "response": ai_reply
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)