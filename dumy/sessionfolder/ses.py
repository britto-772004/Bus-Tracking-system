from flask import Flask, request, render_template
import time

app = Flask(__name__)

# Store countdown timers for each driver (in seconds)
timers = {
    'driver1': None,
    'driver2': None
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/student')
def student():
    return render_template('student.html')

@app.route('/start_countdown', methods=['POST'])
def start_countdown():
    data = request.json
    driver_id = data['driver_id']
    duration = data['duration']  # duration in seconds

    # Start the countdown
    timers[driver_id] = duration
    return {'success': True, 'duration': duration}

@app.route('/get_countdown/<driver_id>')
def get_countdown(driver_id):
    remaining_time = timers.get(driver_id, 0)
    if remaining_time > 0:
        timers[driver_id] -= 1  # Decrease time by 1 second
        return {'remaining_time': remaining_time}
    return {'remaining_time': 0}

if __name__ == '__main__':
    app.run(debug=True)
