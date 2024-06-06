import streamlit as st
import requests
from dotenv import load_dotenv
import os

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Obtener la URL de la API desde las variables de entorno
api_url = os.getenv('API_URL')

# Función para mostrar el formulario de inicio de sesión
def show_login():
    st.title('TruckGuard - Login')
    
    email = st.text_input('Email')
    password = st.text_input('Password', type='password')
    
    if st.button('Login'):
        login_data = {
            'email': email,
            'password': password
        }
        
        response = requests.post(f'{api_url}/auth/login', json=login_data)
        
        if response.status_code == 200:
            st.success('Login successful!')
            token = response.json().get('access_token')
            st.session_state['auth_token'] = token
            st.session_state['logged_in'] = True
        else:
            st.error(f'Login failed: {response.json().get("message", "Unknown error")}')

# Función para mostrar el formulario de creación de camión
def show_create_truck():
    st.title('TruckGuard - Create a New Truck')

    # Form inputs
    plate = st.text_input('Plate')
    model = st.text_input('Model')
    brand = st.text_input('Brand')
    year = st.text_input('Year')
    color = st.text_input('Color')
    mileage = st.number_input('Mileage', min_value=0)
    health_status = st.text_input('Health Status')
    fleetanalytics_id = st.text_input('Fleet Analytics ID (optional)')

    if st.button('Create Truck'):
        truck_data = {
            'plate': plate,
            'model': model,
            'brand': brand,
            'year': year,
            'color': color,
            'mileage': mileage,
            'health_status': health_status,
            'fleetanalytics_id': fleetanalytics_id if fleetanalytics_id else None
        }

        headers = {'Authorization': f'Bearer {st.session_state["auth_token"]}'}
        response = requests.post(f'{api_url}/trucks/new', json=truck_data, headers=headers)
        
        if response.status_code == 201:
            st.success('Truck created successfully!')
        else:
            try:
                st.error(f'Error creating truck: {response.json().get("message", "Unknown error")}')
            except requests.exceptions.JSONDecodeError:
                st.error('Error creating truck: Invalid response from server')

# Función para listar camiones
def show_list_trucks():
    st.title('TruckGuard - List of Trucks')

    headers = {'Authorization': f'Bearer {st.session_state["auth_token"]}'}
    response = requests.get(f'{api_url}/trucks', headers=headers)

    if response.status_code == 200:
        trucks = response.json()
        for truck in trucks:
            st.write(truck)
    else:
        try:
            st.error(f'Error fetching trucks: {response.json().get("message", "Unknown error")}')
        except requests.exceptions.JSONDecodeError:
            st.error('Error fetching trucks: Invalid response from server')

# Función para mostrar el formulario de creación de viaje
def show_create_trip():
    st.title('TruckGuard - Create a New Trip')

    # Form inputs
    date = st.date_input('Date')
    origin = st.text_input('Origin')
    destination = st.text_input('Destination')
    status = st.text_input('Status')
    truck_id = st.number_input('Truck ID', min_value=0)
    fleet_analytics_id = st.text_input('Fleet Analytics ID (optional)')

    if st.button('Create Trip'):
        trip_data = {
            'date': str(date),
            'origin': origin,
            'destination': destination,
            'status': status,
            'truck_id': truck_id,
            'fleetanalytics_id': fleet_analytics_id if fleet_analytics_id else None
        }

        headers = {'Authorization': f'Bearer {st.session_state["auth_token"]}'}
        response = requests.post(f'{api_url}/trips/new', json=trip_data, headers=headers)
        
        if response.status_code == 201:
            st.success('Trip created successfully!')
        else:
            try:
                st.error(f'Error creating trip: {response.json().get("message", "Unknown error")}')
            except requests.exceptions.JSONDecodeError:
                st.error('Error creating trip: Invalid response from server')

# Función para listar viajes
def show_list_trips():
    st.title('TruckGuard - List of Trips')

    headers = {'Authorization': f'Bearer {st.session_state["auth_token"]}'}
    pagination_data = {
        'page': 1,
        'per_page': 10  # Ajusta según sea necesario
    }

    response = requests.get(f'{api_url}/trips/all', headers=headers, json=pagination_data)

    if response.status_code == 200:
        try:
            data = response.json()
            st.write("Trips:")  # Debugging: Mostrar datos de respuesta

            # Asegúrate de que los datos de respuesta tengan la estructura esperada
            if 'trips' in data and isinstance(data['trips'], list):
                trips = data['trips']
                st.write(f"Total trips: {data['total']}")

                for trip in trips:
                    if isinstance(trip, dict):  # Asegúrate de que cada viaje es un diccionario
                        st.write(f"ID: {trip['id']}")
                        st.write(f"Date: {trip['date']}")
                        st.write(f"Origin: {trip['origin']}")
                        st.write(f"Destination: {trip['destination']}")
                        st.write(f"Status: {trip['status']}")
                        st.write(f"Driver ID: {trip['driver_id']}")
                        st.write(f"Truck ID: {trip['truck_id']}")
                        st.write(f"Created at: {trip['created_at']}")
                        st.write(f"Updated at: {trip['updated_at']}")
                        st.write("---")
                    else:
                        st.error("Unexpected trip format")
            else:
                st.error("Unexpected response format")
        except requests.exceptions.JSONDecodeError:
            st.error('Error fetching trips: Invalid response from server')
    else:
        try:
            st.error(f'Error fetching trips: {response.json().get("message", "Unknown error")}')
        except requests.exceptions.JSONDecodeError:
            st.error('Error fetching trips: Invalid response from server')

# Función para obtener un viaje específico
def show_get_trip():
    st.title('TruckGuard - Get Trip Details')

    trip_id = st.number_input('Trip ID', min_value=1)

    if st.button('Get Trip'):
        headers = {'Authorization': f'Bearer {st.session_state["auth_token"]}'}
        response = requests.get(f'{api_url}/trips/{trip_id}', headers=headers)

        if response.status_code == 200:
            trip = response.json()
            st.write("Trip Data:")  # Debugging: Mostrar datos del viaje

            trip = trip.get('trip', {})  
            try:
                st.write(f"ID: {trip['id']}")
                st.write(f"Origin: {trip['origin']}")
                st.write(f"Destination: {trip['destination']}")
                st.write(f"Status: {trip['status']}")
                st.write(f"Distance: {trip['distance']}")
                st.write(f"Duration: {trip['duration']}")
                st.write(f"Driver ID: {trip['driver_id']}")
                st.write(f"Truck ID: {trip['truck_id']}")
                st.write(f"Created at: {trip['created_at']}")
            except KeyError as e:
                st.error(f"Missing expected field in response: {e}")
        else:
            try:
                st.error(f'Error fetching trip: {response.json().get("message", "Unknown error")}')
            except requests.exceptions.JSONDecodeError:
                st.error('Error fetching trip: Invalid response from server')


# Función para actualizar un viaje
def show_update_trip():
    st.title('TruckGuard - Update Trip')

    trip_id = st.number_input('Trip ID', min_value=0)
    date = st.date_input('Date')
    origin = st.text_input('Origin')
    destination = st.text_input('Destination')
    status = st.text_input('Status')
    truck_id = st.number_input('Truck ID', min_value=0)

    if st.button('Update Trip'):
        trip_data = {
            'date': str(date),
            'origin': origin,
            'destination': destination,
            'status': status,
            'truck_id': truck_id
        }

        headers = {'Authorization': f'Bearer {st.session_state["auth_token"]}'}
        response = requests.put(f'{api_url}/trips/{trip_id}', json=trip_data, headers=headers)
        
        if response.status_code == 200:
            st.success('Trip updated successfully!')
        else:
            st.error(f'Error updating trip: {response.json().get("message", "Unknown error")}')

# Función para eliminar un viaje
def show_delete_trip():
    st.title('TruckGuard - Delete Trip')

    trip_id = st.number_input('Trip ID', min_value=0)

    if st.button('Delete Trip'):
        headers = {'Authorization': f'Bearer {st.session_state["auth_token"]}'}
        response = requests.delete(f'{api_url}/trips/{trip_id}', headers=headers)
        
        if response.status_code == 200:
            st.success('Trip deleted successfully!')
        else:
            st.error(f'Error deleting trip: {response.json().get("message", "Unknown error")}')

# Función principal
def main():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        show_login()
    else:
        st.sidebar.title("Navigation")
        choice = st.sidebar.radio("Go to", ("Create Truck", "List Trucks", "Create Trip", "List Trips", "Get Trip", "Update Trip", "Delete Trip"))

        if choice == "Create Truck":
            show_create_truck()
        elif choice == "List Trucks":
            show_list_trucks()
        elif choice == "Create Trip":
            show_create_trip()
        elif choice == "List Trips":
            show_list_trips()
        elif choice == "Get Trip":
            show_get_trip()
        elif choice == "Update Trip":
            show_update_trip()
        elif choice == "Delete Trip":
            show_delete_trip()

if __name__ == '__main__':
    main()
