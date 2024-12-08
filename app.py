from flask import Flask, render_template, request , jsonify, render_template_string
from flask_socketio import SocketIO, emit
import time
import threading
import folium
from opencage.geocoder import OpenCageGeocode
import math


app = Flask(__name__)
socketio = SocketIO(app)

opencage_api_key = 'd0912921b03b43ef94bf5cccb2194195'

geocoder = OpenCageGeocode(opencage_api_key)
# Static locations for Device 1 and Device 2
device_coordinates = {
    'device1': (11.0835, 76.9966),  # Static location for Device 1 KGISL
    'device2': (11.4771273, 77.147258)  # Static location for Device 2 PriyaBharathi House
}

driver_location = None  # Global variable to store the driver's location

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Radius of the Earth in km
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance
# Global timer state
timer_state = {
    'remaining_time': 300,  # Default to 5 minutes in seconds
    'is_running': False
}

# To stop the timer thread
stop_timer_thread = False

@app.route('/')
def home(): 
    return render_template('index.html')
  

@app.route('/admin')
def admin():  
    return render_template('admin.html')
  

@app.route('/driver',methods=["POST","GET"])
def driver():  
    return render_template('driver.html')


@app.route('/student',methods=["POST","GET"] )
def student(): 
    return render_template('student.html')


@app.route('/studentloged',methods=["POST","GET"])
def studentloged():  
    return render_template('studentloged.html')


@app.route('/driverloged',methods=["POST","GET"])
def driverloged():  
    return render_template('driverloged.html')



from flask import Flask, render_template, request, jsonify
import folium
from geopy.distance import geodesic


# KGISL Institute of Technology coordinates
kgisl_lat, kgisl_lng = 11.084320842094604, 76.9971686531164

# Store student locations
student_locations = {}

# student count for the geo fencing 


# @app.route('/geo_fencing')
# def geo_fencing():
#     print(student_locations)
#     students_count = 0
#     inside_bus = 0

#     # Use driver's location if available, otherwise fallback to KGISL coordinates
#     if driver_location:
#         center_lat, center_lng = driver_location
#     else:
#         # Fallback to KGISL coordinates if driver location is not set
#         center_lat, center_lng = kgisl_lat, kgisl_lng

#     # Create a Folium map centered around the driver's location or KGISL if not available
#     mymap = folium.Map(location=[center_lat, center_lng], zoom_start=45)

#     # Add a circle representing the 20-meter geofence around the driver's location
#     folium.Circle(
#         radius=20,  # 20 meters
#         location=[center_lat, center_lng],
#         color='blue',
#         fill=True,
#         fill_opacity=0.2 
#     ).add_to(mymap)

#     # Add student markers to the map
#     for key,value  in student_locations.items():
#         # Check if the student is within the geofence
#         if is_within_geofence(value[-1]['lat'], value[-1]['lng'], center_lat, center_lng):
#             key = key
#             print("key = ",key)
#             color = 'green'
#             inside_bus += 1
#         else:
#             key = key 
            
#             color = 'red'
#             students_count += 1  # Count students who are away from the bus

#         # Add student markers
#         folium.Marker(
#             location=[value[-1]['lat'], value[-1]['lng']],
#             popup = folium.Popup(key),
#             icon=folium.Icon(color=color)
#         ).add_to(mymap)

#     # Save the map to an HTML string and pass it to the template
#     map_html = mymap._repr_html_()
#     return render_template('map.html', map_html=map_html, students_count=students_count,inside_bus = inside_bus)


@app.route('/geo_fencing')
def geo_fencing():
    students_status = []
    inside_bus = 0
    outside_bus = 0

    # Use driver's location or fallback to KGISL
    center_lat, center_lng = driver_location if driver_location else (kgisl_lat, kgisl_lng)

    # Create Folium map
    mymap = folium.Map(location=[center_lat, center_lng], zoom_start=15)

    # Add geofence circle
    folium.Circle(
        radius=20,
        location=[center_lat, center_lng],
        color='blue',
        fill=True,
        fill_opacity=0.2
    ).add_to(mymap)

    # Process each student's location
    for key, value in student_locations.items():
        latest_location = value[-1]
        student_lat, student_lng = latest_location['lat'], latest_location['lng']
        within_geofence = is_within_geofence(student_lat, student_lng, center_lat, center_lng)

        # Determine marker color
        marker_color = 'green' if within_geofence else 'red'
        status = "Inside Bus" if within_geofence else "Outside Bus"

        # Update counts
        if within_geofence:
            inside_bus += 1
        else:
            outside_bus += 1

        # Add marker
        folium.Marker(
            location=[student_lat, student_lng],
            popup=folium.Popup(f"Name: {key}<br>Status: {status}"),
            icon=folium.Icon(color=marker_color)
        ).add_to(mymap)

        # Append student details to the list
        students_status.append({
            "name": key,
            "status": status
        })

    # Render the map and pass data to the template
    map_html = mymap._repr_html_()
    return render_template(
        'map.html',
        map_html=map_html,
        inside_bus=inside_bus,
        outside_bus=outside_bus,
        students_status=students_status
    )

@app.route('/studenticon')
def studenticon():
    return render_template('student_icon.html')
    

@app.route('/add_student_location', methods=["GET","POST"])
def add_student_location():
    print('agudaaaa11111')

    data = request.get_json()
    lat = data['lat']
    lng = data['lng']
    stu_name = data['stu_name']
    print("lat = > ", lat,"long =>",lng,"name =>", stu_name)
    student_locations.setdefault(stu_name, [])
    student_locations[stu_name].append({'lat': lat, 'lng': lng})
    print(student_locations)
    return jsonify({'status': 'success'})


# # New route to get the latest student location
# @app.route('/get_student_location', methods=['GET'])
# def get_student_location():
#     print('agudaaaa')
#     if student_locations:
#         # Return the most recent location
#         print(student_locations,"helelohf")
#         return jsonify(student_locations)
#     else:
#         return jsonify({'status': 'error', 'message': 'No student location found'})
    

@app.route('/count_students', methods=['GET'])
def count_students():
    count = sum(1 for key,value in student_locations.items() if is_within_geofence(value[-1]['lat'], value[-1]['lng'], kgisl_lat, kgisl_lng))
    return jsonify({'count': count})

def is_within_geofence(device_lat, device_lng, kgisl_lat, kgisl_lng, radius=20):
    distance = geodesic((kgisl_lat, kgisl_lng), (device_lat, device_lng)).meters
    return distance <= radius


@app.route('/view_map')
def view_map(): 
    return render_template('view_map.html')

@app.route('/start_tracking')
def start_tracking():
    return  render_template('start_tracking.html')

@app.route('/driver_location')
def driver_location():
    global driver_location
    lat = float(request.args.get('lat'))
    lon = float(request.args.get('lon'))
    driver_location = (lat, lon)
    print(driver_location,"hari")
    return jsonify({'driver': driver_location})
socketio.on('d',)
@app.route('/coordinates')
def coordinates():
    data = {
        'device1': device_coordinates['device1'], #insted 11.0835, 76.9966 you can give directly
        'device2': device_coordinates['device2']
    }
    if driver_location:
        data['driver'] = driver_location
        data['student'] = student_locations
        # data['student'] = student_locations[-1]
    return jsonify(data)




@app.route('/update_driver_location', methods=['POST'])
def update_driver_location():
    global driver_location
    data = request.get_json()
    lat = data['lat']
    lng = data['lng']
    driver_location = (lat, lng)
    print("suuuuuuuuu",driver_location)
    return jsonify({'status': 'success'})

@socketio.on('start_timer')
def handle_start_timer():
    global timer_state, stop_timer_thread
    if not timer_state['is_running']:
        timer_state['is_running'] = True
        stop_timer_thread = False
        thread = threading.Thread(target=countdown)
        thread.start()
    emit('timer_update', timer_state, broadcast=True)

@socketio.on('stop_timer')
def handle_stop_timer():
    global timer_state, stop_timer_thread
    timer_state['is_running'] = False
    stop_timer_thread = True
    emit('timer_update', timer_state, broadcast=True)

@socketio.on('reset_timer')
def handle_reset_timer():
    global timer_state, stop_timer_thread
    timer_state['remaining_time'] = 300  # Reset to 5 minutes
    timer_state['is_running'] = False
    stop_timer_thread = True
    emit('timer_update', timer_state, broadcast=True)

@socketio.on('set_time')
def handle_set_time(data):
    global timer_state, stop_timer_thread
    timer_state['remaining_time'] = data['new_time']
    timer_state['is_running'] = False
    stop_timer_thread = True
    emit('timer_update', timer_state, broadcast=True)

def countdown():
    global timer_state, stop_timer_thread
    while timer_state['is_running'] and timer_state['remaining_time'] > 0 and not stop_timer_thread:
        time.sleep(1)
        timer_state['remaining_time'] -= 1
        if timer_state['remaining_time'] <= 30:
            socketio.emit('beep')
        if timer_state['remaining_time'] == 0:
            timer_state['is_running'] = False
            socketio.emit('beep')
        socketio.emit('timer_update', timer_state)
 
if __name__ == '__main__':
    socketio.run(app, debug=True)
