from flask import Flask, request, jsonify
import requests
import threading
import json
from datetime import datetime
import time

app = Flask(__name__)


class CalculatorWebGUI:
    def __init__(self):
        self.calculator_service_url = "http://calculator-service:5000"
        self.metrics_url = "http://load-simulator-service:8080/metrics"

    def calculate(self, operation, a, b):
        try:
            response = requests.post(
                f"{self.calculator_service_url}/{operation}",
                json={"a": float(a), "b": float(b)},
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}


calculator_gui = CalculatorWebGUI()


@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Distributed Calculator - Real-time Metrics</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1400px; margin: 0 auto; }
            .section { margin: 20px 0; padding: 20px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .calculator-form { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; max-width: 400px; margin-bottom: 20px; }
            button { padding: 10px; margin: 5px; cursor: pointer; background: #007cba; color: white; border: none; border-radius: 4px; }
            button:hover { background: #005a87; }
            input[type="number"] { padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            .metrics-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            .chart-container { position: relative; height: 300px; }
            .current-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px; }
            .stat-card { background: #f8f9fa; padding: 15px; border-radius: 6px; text-align: center; }
            .stat-value { font-size: 24px; font-weight: bold; color: #007cba; }
            .stat-label { font-size: 12px; color: #666; text-transform: uppercase; }
            .debug-info { background: #fff3cd; padding: 10px; border-radius: 4px; margin: 10px 0; font-family: monospace; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Distributed Calculator - Real-time Metrics Dashboard</h1>

            <!-- Debug Information -->
            <div class="section">
                <h3>🔧 Debug Information</h3>
                <div class="debug-info">
                    <div>Service Status:</div>
                    <div id="serviceStatus">Checking...</div>
                </div>
            </div>

            <div class="section">
                <h2>🧮 Calculator</h2>
                <div class="calculator-form">
                    <input type="number" id="numA" placeholder="Number A" step="any" value="10">
                    <input type="number" id="numB" placeholder="Number B" step="any" value="5">
                    <button onclick="calculate('add')">➕ Add</button>
                    <button onclick="calculate('subtract')">➖ Subtract</button>
                    <button onclick="calculate('multiply')">✖️ Multiply</button>
                    <button onclick="calculate('divide')">➗ Divide</button>
                </div>
                <div id="result" style="margin-top: 10px; font-weight: bold; font-size: 16px;"></div>
            </div>

            <div class="section">
                <h2>🎛️ Load Simulator Control</h2>
                <div style="display: flex; align-items: center; gap: 15px;">
                    <label><strong>Number of Users:</strong> <span id="userCount" style="font-weight: bold; color: #007cba;">10</span></label>
                    <input type="range" id="userSlider" min="1" max="100" value="10" oninput="updateUserCount(this.value)" style="flex: 1;">
                    <button onclick="updateLoad()" style="padding: 10px 20px;">Update Load</button>
                </div>
            </div>

            <div class="section">
                <h2>📊 Current Statistics</h2>
                <div class="current-stats" id="currentStats">
                    <div class="stat-card">
                        <div class="stat-value">0</div>
                        <div class="stat-label">Active Users</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">0</div>
                        <div class="stat-label">Total Requests</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">0</div>
                        <div class="stat-label">Errors</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">0</div>
                        <div class="stat-label">Avg Response Time (ms)</div>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>📈 Real-time Operation Metrics</h2>
                <div class="metrics-grid">
                    <div>
                        <div class="chart-container">
                            <canvas id="operationsChart"></canvas>
                        </div>
                    </div>
                    <div>
                        <div class="chart-container">
                            <canvas id="usersChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let operationsChart, usersChart;
            let chartData = {
                timestamps: [],
                operations: { add: [], subtract: [], multiply: [], divide: [] },
                users: []
            };

            // Test service connectivity
            async function testServices() {
                const statusDiv = document.getElementById('serviceStatus');
                try {
                    const response = await fetch('/metrics');
                    const data = await response.json();
                    statusDiv.innerHTML = '✅ Services are connected and responding';
                } catch (error) {
                    statusDiv.innerHTML = '❌ Service connection error: ' + error.message;
                }
            }

            function calculate(operation) {
                const a = document.getElementById('numA').value;
                const b = document.getElementById('numB').value;

                if (!a || !b) {
                    showResult('Please enter both numbers', 'red');
                    return;
                }

                fetch('/calculate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({operation, a: parseFloat(a), b: parseFloat(b)})
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.error) {
                        showResult(`Error: ${data.error}`, 'red');
                    } else {
                        showResult(`Result: ${data.result}`, 'green');
                    }
                })
                .catch(error => {
                    showResult(`Error: ${error.message}`, 'red');
                    console.error('Calculation error:', error);
                });
            }

            function showResult(message, color) {
                const resultDiv = document.getElementById('result');
                resultDiv.innerHTML = message;
                resultDiv.style.color = color;
            }

            function updateUserCount(value) {
                document.getElementById('userCount').textContent = value;
            }

            function updateLoad() {
                const userCount = document.getElementById('userSlider').value;
                fetch('/update_load', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({user_count: parseInt(userCount)})
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Failed to update load');
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Load updated:', data);
                })
                .catch(error => {
                    console.error('Error updating load:', error);
                    alert('Failed to update load: ' + error.message);
                });
            }

            function initializeCharts() {
                const ctx1 = document.getElementById('operationsChart').getContext('2d');
                operationsChart = new Chart(ctx1, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [
                            { 
                                label: 'Add', 
                                data: [], 
                                borderColor: '#4CAF50', 
                                backgroundColor: 'rgba(76, 175, 80, 0.1)', 
                                tension: 0.4,
                                borderWidth: 2
                            },
                            { 
                                label: 'Subtract', 
                                data: [], 
                                borderColor: '#2196F3', 
                                backgroundColor: 'rgba(33, 150, 243, 0.1)', 
                                tension: 0.4,
                                borderWidth: 2
                            },
                            { 
                                label: 'Multiply', 
                                data: [], 
                                borderColor: '#FF9800', 
                                backgroundColor: 'rgba(255, 152, 0, 0.1)', 
                                tension: 0.4,
                                borderWidth: 2
                            },
                            { 
                                label: 'Divide', 
                                data: [], 
                                borderColor: '#F44336', 
                                backgroundColor: 'rgba(244, 67, 54, 0.1)', 
                                tension: 0.4,
                                borderWidth: 2
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: true,
                                    text: 'Requests per Second'
                                }
                            }
                        },
                        plugins: {
                            title: {
                                display: true,
                                text: 'Operation Requests Over Time'
                            }
                        }
                    }
                });

                const ctx2 = document.getElementById('usersChart').getContext('2d');
                usersChart = new Chart(ctx2, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [{
                            label: 'Active Users',
                            data: [],
                            borderColor: '#9C27B0',
                            backgroundColor: 'rgba(156, 39, 176, 0.1)',
                            tension: 0.4,
                            borderWidth: 2
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: true,
                                    text: 'Number of Users'
                                }
                            }
                        },
                        plugins: {
                            title: {
                                display: true,
                                text: 'Active Users Over Time'
                            }
                        }
                    }
                });
            }

            function updateCurrentStats(metrics) {
                const current = metrics.current;
                const stats = document.getElementById('currentStats');

                if (stats) {
                    stats.innerHTML = `
                        <div class="stat-card">
                            <div class="stat-value">${current.active_users || 0}</div>
                            <div class="stat-label">Active Users</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${current.total_requests || 0}</div>
                            <div class="stat-label">Total Requests</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${current.error_count || 0}</div>
                            <div class="stat-label">Errors</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${Math.round((current.response_times && current.response_times.length ? 
                                current.response_times.reduce((a, b) => a + b, 0) / current.response_times.length * 1000 : 0))}</div>
                            <div class="stat-label">Avg Response Time (ms)</div>
                        </div>
                    `;
                }
            }

            function updateCharts(metrics) {
                const historical = metrics.historical;

                if (!historical || !historical.timestamps) {
                    console.log('No historical data available');
                    return;
                }

                // Update operations chart
                if (operationsChart && historical.operation_counts) {
                    operationsChart.data.labels = historical.timestamps;
                    operationsChart.data.datasets[0].data = historical.operation_counts.add || [];
                    operationsChart.data.datasets[1].data = historical.operation_counts.subtract || [];
                    operationsChart.data.datasets[2].data = historical.operation_counts.multiply || [];
                    operationsChart.data.datasets[3].data = historical.operation_counts.divide || [];
                    operationsChart.update();
                }

                // Update users chart
                if (usersChart && historical.active_users) {
                    usersChart.data.labels = historical.timestamps;
                    usersChart.data.datasets[0].data = historical.active_users;
                    usersChart.update();
                }
            }

            async function updateMetrics() {
                try {
                    const response = await fetch('/metrics');
                    if (!response.ok) {
                        throw new Error('Metrics fetch failed');
                    }
                    const metrics = await response.json();
                    updateCurrentStats(metrics);
                    updateCharts(metrics);
                } catch (error) {
                    console.error('Error fetching metrics:', error);
                    // Initialize with empty data if metrics fail
                    updateCharts({
                        historical: {
                            timestamps: [],
                            operation_counts: { add: [], subtract: [], multiply: [], divide: [] },
                            active_users: []
                        }
                    });
                }
            }

            // Initialize charts and start metrics updates
            document.addEventListener('DOMContentLoaded', function() {
                initializeCharts();
                testServices();
                setInterval(updateMetrics, 2000); // Update every 2 seconds
                setInterval(testServices, 30000); // Test services every 30 seconds
            });
        </script>
    </body>
    </html>
    '''


@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        result = calculator_gui.calculate(data['operation'], data['a'], data['b'])
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/update_load', methods=['POST'])
def update_load():
    try:
        data = request.get_json()
        response = requests.post(
            "http://load-simulator-service:8080/update_load",
            json={"user_count": data['user_count']},
            timeout=5
        )
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/metrics')
def get_metrics():
    try:
        response = requests.get("http://load-simulator-service:8080/metrics", timeout=5)
        return jsonify(response.json())
    except Exception as e:
        print(f"Metrics error: {e}")
        return jsonify({
            "current": {
                "request_rates": {"add": 0, "subtract": 0, "multiply": 0, "divide": 0},
                "active_users": 0,
                "total_requests": 0,
                "error_count": 0,
                "response_times": []
            },
            "historical": {
                "timestamps": [],
                "operation_counts": {"add": [], "subtract": [], "multiply": [], "divide": []},
                "active_users": [],
                "response_times": []
            }
        })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)