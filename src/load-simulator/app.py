from flask import Flask, request, jsonify
import threading
import time
import random
import requests
from collections import deque
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)


class TimeSeriesMetrics:
    def __init__(self, max_points=30):  # Reduced to 30 points for stability
        self.max_points = max_points
        self.timestamps = deque(maxlen=max_points)
        self.operation_counts = {
            'add': deque(maxlen=max_points),
            'subtract': deque(maxlen=max_points),
            'multiply': deque(maxlen=max_points),
            'divide': deque(maxlen=max_points)
        }
        self.active_users = deque(maxlen=max_points)

    def add_data_point(self, operation_counts, active_users):
        current_time = time.time()
        self.timestamps.append(current_time)

        for op in self.operation_counts:
            self.operation_counts[op].append(operation_counts.get(op, 0))

        self.active_users.append(active_users)

    def get_historical_data(self):
        # Format timestamps for display
        formatted_timestamps = [time.strftime('%H:%M:%S', time.localtime(ts)) for ts in self.timestamps]

        return {
            'timestamps': formatted_timestamps,
            'operation_counts': {op: list(counts) for op, counts in self.operation_counts.items()},
            'active_users': list(self.active_users)
        }


class LoadSimulator:
    def __init__(self):
        self.active_users = 5  # Start with fewer users
        self.is_running = False
        self.threads = []
        self.metrics = {
            'current': {
                'request_rates': {'add': 0, 'subtract': 0, 'multiply': 0, 'divide': 0},
                'active_users': 0,
                'total_requests': 0,
                'error_count': 0
            },
            'historical': TimeSeriesMetrics()
        }
        self.calculator_url = "http://calculator-service:5000"
        self.request_counter = 0
        self.last_reset_time = time.time()

    def reset_counters(self):
        # Reset counters every 5 seconds for rates
        self.metrics['current']['request_rates'] = {op: 0 for op in self.metrics['current']['request_rates']}
        self.last_reset_time = time.time()

    def start_simulation(self):
        if self.is_running:
            self.stop_simulation()

        self.is_running = True
        self.threads = []

        logger.info(f"Starting simulation with {self.active_users} users")

        for i in range(self.active_users):
            thread = threading.Thread(target=self.simulate_user, args=(i,))
            thread.daemon = True
            thread.start()
            self.threads.append(thread)

        # Start metrics collection thread
        metrics_thread = threading.Thread(target=self.collect_metrics)
        metrics_thread.daemon = True
        metrics_thread.start()

        logger.info("Simulation started successfully")

    def stop_simulation(self):
        self.is_running = False
        for thread in self.threads:
            thread.join(timeout=1)
        self.threads = []
        logger.info("Simulation stopped")

    def simulate_user(self, user_id):
        operations = ['add', 'subtract', 'multiply', 'divide']

        while self.is_running:
            try:
                # Increased delay between requests to reduce load
                time.sleep(random.uniform(1.0, 3.0))

                # Choose random operation
                operation = random.choice(operations)
                a = random.randint(1, 100)
                b = random.randint(1, 100)

                # Make request to calculator service
                start_time = time.time()
                response = requests.post(
                    f"{self.calculator_url}/{operation}",
                    json={"a": a, "b": b},
                    timeout=10
                )
                end_time = time.time()

                # Update metrics
                self.metrics['current']['request_rates'][operation] += 1
                self.metrics['current']['total_requests'] += 1
                self.metrics['current']['active_users'] = self.active_users

                if response.status_code != 200:
                    self.metrics['current']['error_count'] += 1
                    logger.warning(f"User {user_id} got error response: {response.status_code}")
                else:
                    logger.debug(f"User {user_id} successful {operation}: {a}, {b}")

            except requests.exceptions.RequestException as e:
                self.metrics['current']['error_count'] += 1
                logger.warning(f"User {user_id} request error: {e}")
                time.sleep(2)  # Wait longer on errors
            except Exception as e:
                self.metrics['current']['error_count'] += 1
                logger.error(f"User {user_id} unexpected error: {e}")
                time.sleep(2)

    def collect_metrics(self):
        """Collect metrics every 2 seconds for historical data"""
        while self.is_running:
            time.sleep(2)  # Collect every 2 seconds

            # Add data point to historical metrics
            self.metrics['historical'].add_data_point(
                self.metrics['current']['request_rates'],
                self.metrics['current']['active_users']
            )

            # Reset counters for next interval
            self.reset_counters()


# Global simulator instance
simulator = LoadSimulator()


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "service": "load-simulator",
        "active_users": simulator.active_users,
        "is_running": simulator.is_running
    })


@app.route('/metrics', methods=['GET'])
def get_metrics():
    try:
        current = simulator.metrics['current'].copy()
        historical = simulator.metrics['historical'].get_historical_data()

        return jsonify({
            'current': current,
            'historical': historical
        })
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/update_load', methods=['POST'])
def update_load():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        new_user_count = data.get('user_count', 5)

        # Limit maximum users to prevent overload
        if new_user_count > 50:
            new_user_count = 50

        logger.info(f"Updating load to {new_user_count} users")

        simulator.active_users = new_user_count
        simulator.metrics['current']['active_users'] = new_user_count

        # Restart simulation with new user count
        simulator.start_simulation()

        return jsonify({
            "message": f"Load updated to {new_user_count} users",
            "user_count": new_user_count
        })
    except Exception as e:
        logger.error(f"Error updating load: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/start', methods=['POST'])
def start_simulation():
    try:
        simulator.start_simulation()
        return jsonify({"message": "Simulation started"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/stop', methods=['POST'])
def stop_simulation():
    try:
        simulator.stop_simulation()
        return jsonify({"message": "Simulation stopped"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Initialize the simulator when the app starts
@app.before_first_request
def initialize_simulator():
    logger.info("Initializing load simulator")
    # Start with a small delay to ensure other services are ready
    threading.Timer(5.0, simulator.start_simulation).start()


if __name__ == '__main__':
    logger.info("Starting Load Simulator Service")
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)