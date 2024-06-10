import streamlit as st
import pandas as pd
import requests
from dotenv import load_dotenv
import os
import plotly.express as px

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Obtener la URL de la API desde las variables de entorno
api_url = os.getenv('API_URL')

# Función para mostrar la pantalla de bienvenida
def show_welcome():
    st.image('images/truck_icon_.png', width=100)

    st.markdown(
        """
        <style>
        .welcome-container {
            text-align: center;
            margin-top: 50px; /* Ajusta este valor según sea necesario */
        }
        .welcome-container h1 {
            color: #4CAF50;
            font-size: 3em;
        }
        .welcome-container h1 span {
            color: #FF5733;
        }
        .welcome-container h3 {
            color: #555555;
        }
        </style>
        <div class='welcome-container'>
            <h1>Welcome to <span>TruckGuard</span></h1>
            <h3>Please log in to access the system.</h3>
        </div>
        """, unsafe_allow_html=True
    )

    if st.button('Go to Login'):
        st.session_state['show_login'] = True
        st.experimental_rerun()

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
            st.experimental_rerun()
        else:
            st.error(f'Login failed: {response.json().get("message", "Unknown error")}')

# Función para obtener los datos de los componentes
def fetch_components_data(truck_id):
    headers = {'Authorization': f'Bearer {st.session_state["auth_token"]}'}
    response = requests.get(f'{api_url}/maintenance/{truck_id}/components', headers=headers)

    if response.status_code == 200:
        components = response.json().get('components', [])
        st.write("Components Data:", components)  # Depuración: Mostrar datos de componentes
        return components
    else:
        st.error('Error fetching components data: {}'.format(response.text))
        return []
    
# Función para obtener estadísticas de los componentes
def get_component_statistics(components_data):
    health_status_values = {
        'Excellent': 100,
        'Very Good': 80,
        'Good': 60,
        'Fair': 40,
        'Maintenance Required': 20
    }

    df_components = pd.DataFrame(components_data)
    
    if 'status' in df_components.columns:
        # Calcular los promedios de los estados de salud
        df_components['health_value'] = df_components['status'].map(health_status_values)
        st.write("Health Values:", df_components['health_value'])  # Depuración: Mostrar valores de salud
        component_stats = df_components.groupby('component')['health_value'].mean().reset_index()
        component_stats.columns = ['theta', 'metrics']
        st.write("Component Stats:", component_stats)  # Depuración: Mostrar estadísticas de componentes
        return component_stats
    else:
        st.error("'status' field is missing in the components data")
        return pd.DataFrame(columns=['theta', 'metrics'])  # Devolver DataFrame vacío en caso de error

# Función para mostrar el gráfico radar de los componentes
def show_component_radar_chart(truck_id):
    st.title('TruckGuard - Component Radar Chart')

    components_data = fetch_components_data(truck_id)
    
    if components_data:
        df_components = get_component_statistics(components_data)
        
        radar_fig = px.line_polar(df_components, r='metrics', theta='theta', line_close=True)
        radar_fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=False
        )
        st.plotly_chart(radar_fig)
        st.dataframe(df_components)
    else:
        st.error('No components data found')

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
    driver_id = st.text_input('Driver ID')

    if st.button('Create Truck'):
        truck_data = {
            'plate': plate,
            'model': model,
            'brand': brand,
            'year': year,
            'color': color,
            'mileage': mileage,
            'health_status': health_status,
            'fleetanalytics_id': fleetanalytics_id if fleetanalytics_id else None,
            'driver_id': driver_id
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
    response = requests.get(f'{api_url}/trucks/all', headers=headers)

    if response.status_code == 200:
        trucks = response.json().get('trucks', [])
        
        # Crear DataFrame para los camiones
        df_trucks = pd.DataFrame(trucks)
        
        # Filtrar camiones en la barra lateral
        with st.sidebar:
            selected_model = st.multiselect('Model', sorted(df_trucks['model'].unique()))
            selected_brand = st.multiselect('Brand', sorted(df_trucks['brand'].unique()))
            selected_health_status = st.multiselect('status', sorted(df_trucks['status'].unique()))
        
        # Filtrar DataFrame
        if selected_model:
            df_trucks = df_trucks[df_trucks['model'].isin(selected_model)]
        if selected_brand:
            df_trucks = df_trucks[df_trucks['brand'].isin(selected_brand)]
        if selected_health_status:
            df_trucks = df_trucks[df_trucks['status'].isin(selected_health_status)]
        
        # Mostrar métricas y gráfica
        st.write(f"Total trucks: {len(df_trucks)}")
        st.dataframe(df_trucks)
        
        if len(df_trucks) > 0:
            # Gráfica de ejemplo
            fig = px.bar(df_trucks, x='model', y='mileage', color='brand', title='Mileage by Truck Model')
            st.plotly_chart(fig)
    else:
        try:
            st.error(f'Error fetching trucks: {response.json().get("message", "Unknown error")}')
        except requests.exceptions.JSONDecodeError:
            st.error('Error fetching trucks: Invalid response from server')

# Función para mostrar el formulario de creación de viaje
def show_create_trip():
    st.title('TruckGuard - Create a New Trip')

    # Form inputs
    origin = st.text_input('Origin')
    destination = st.text_input('Destination')
    status = st.text_input('Status')
    truck_id = st.number_input('Truck ID', min_value=0)
    driver_id = st.number_input('Driver ID', min_value=0)

    if st.button('Create Trip'):
        trip_data = {
            'origin': origin,
            'destination': destination,
            'status': status,
            'truck_id': truck_id,
            'driver_id': driver_id
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
    response = requests.get(f'{api_url}/trips/all', headers=headers)

    if response.status_code == 200:
        trips = response.json().get('trips', [])
        for trip in trips:
            st.write(trip)
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
            st.write("Trip Data:")
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

def main():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'show_login' not in st.session_state:
        st.session_state['show_login'] = False

    if not st.session_state['logged_in']:
        if st.session_state['show_login']:
            show_login()
        else:
            show_welcome()
    else:
        st.sidebar.title("Navigation")
        trip_options = st.sidebar.multiselect(
            "Trip Operations",
            ["Create Trip", "List Trips", "Get Trip", "Update Trip", "Delete Trip"]
        )

        truck_options = st.sidebar.multiselect(
            "Truck Operations",
            ["Create Truck", "List Trucks", "Component Radar Chart"]
        )

        if "Create Trip" in trip_options:
            show_create_trip()
        if "List Trips" in trip_options:
            show_list_trips()
        if "Get Trip" in trip_options:
            show_get_trip()
        if "Update Trip" in trip_options:
            show_update_trip()
        if "Delete Trip" in trip_options:
            show_delete_trip()

        if "Create Truck" in truck_options:
            show_create_truck()
        if "List Trucks" in truck_options:
            show_list_trucks()
        if "Component Radar Chart" in truck_options:
            truck_id = st.sidebar.number_input('Truck ID', min_value=1, value=1)
            show_component_radar_chart(truck_id)

if __name__ == '__main__':
    main()
