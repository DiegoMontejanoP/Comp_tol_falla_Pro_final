from flask import Flask, request, jsonify
import random
import time
import os
from flask_cors import CORS  # Add CORS support

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "service": "calculator"})


@app.route('/add', methods=['POST'])
def add():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Simulate some processing time
        time.sleep(random.uniform(0.01, 0.1))
        result = float(data['a']) + float(data['b'])
        return jsonify({
            "operation": "add",
            "result": result,
            "a": data['a'],
            "b": data['b']
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/subtract', methods=['POST'])
def subtract():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        time.sleep(random.uniform(0.01, 0.1))
        result = float(data['a']) - float(data['b'])
        return jsonify({
            "operation": "subtract",
            "result": result,
            "a": data['a'],
            "b": data['b']
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/multiply', methods=['POST'])
def multiply():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        time.sleep(random.uniform(0.01, 0.1))
        result = float(data['a']) * float(data['b'])
        return jsonify({
            "operation": "multiply",
            "result": result,
            "a": data['a'],
            "b": data['b']
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/divide', methods=['POST'])
def divide():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        time.sleep(random.uniform(0.01, 0.1))
        b = float(data['b'])
        if b == 0:
            return jsonify({"error": "Division by zero"}), 400

        result = float(data['a']) / b
        return jsonify({
            "operation": "divide",
            "result": result,
            "a": data['a'],
            "b": data['b']
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)