import os
import subprocess
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/run_benchmark", methods=["POST"])
def run_benchmark():
    user_prompt = request.json.get("prompt", "")

    try:
        cmd = ["python3", "mcp_client.py"]
        if user_prompt:
            cmd.extend(["--prompt", user_prompt])
            
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        return jsonify({"stdout": result.stdout, "stderr": result.stderr})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5001)
