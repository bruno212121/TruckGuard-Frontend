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
        components = response.json().get('components', []) # Depuración: Mostrar datos de componentes
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
        component_stats = df_components.groupby('component')['health_value'].mean().reset_index()
        component_stats.columns = ['theta', 'metrics']
        return component_stats
    else:
        st.error("'status' field is missing in the components data")
        return pd.DataFrame(columns=['theta', 'metrics'])  # Devolver DataFrame vacío en caso de error

# Función para obtener detalles de un camión específico
def fetch_truck_details(truck_id):
    headers = {'Authorization': f'Bearer {st.session_state["auth_token"]}'}
    response = requests.get(f'{api_url}/trucks/{truck_id}', headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error('Error fetching truck details: {}'.format(response.text))
        return None

# Función modificada para mostrar el gráfico radar de los componentes con información adicional del camión
def show_component_radar_chart(truck_id):
    truck_details = fetch_truck_details(truck_id)
    title = "Analisis de camion"
    st.title(title)

    if truck_details:
        truck = truck_details.get('truck', {})
        truck_brand = truck.get('brand', 'Unknown')
        truck_milage = truck.get('mileage', 'Unknown')
        
        if truck['driver']:
            truck_driver = truck['driver']['name']

        st.write("Truck Details:")

        col1, col2, col3 = st.columns(3)
        col1.metric('Brand', truck_brand)
        col2.metric('Driver', truck_driver)
        col3.metric('Mileage', truck_milage)


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
            bar_fig = px.bar(df_components, x='theta', y='metrics', color='metrics', 
                             labels={'theta': 'Component', 'metrics': 'Health Metric'},
                             title='Component Health Metrics')
            st.plotly_chart(bar_fig)
            st.write('Component Health Metrics:')
            st.dataframe(df_components)
        else:
            st.error('No components data found')
    else:
        st.error('No truck details found')



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
    truck_id = st.number_input('Truck ID', min_value=1)
    driver_id = st.number_input('Driver ID', min_value=1)

    if st.button('Create Trip'):
        trip_data = {
            'origin': origin,
            'destination': destination,
            'status': 'pending',
            'truck_id': truck_id,
            'driver_id': driver_id
        }

        headers = {'Authorization': f'Bearer {st.session_state["auth_token"]}'}
        response = requests.post(f'{api_url}/trips/new', json=trip_data, headers=headers)
        
        if response.status_code == 201:
            st.success('Trip created successfully!')
            trip_details = response.json().get('trip', {})
            st.write('Trip Details:')
            st.write(f"Origin: {trip_details['origin']}")
            st.write(f"Destination: {trip_details['destination']}")
            st.write(f"Status: {trip_details['status']}")
            st.write(f"distance: {trip_details['distance']}")
            st.write(f"duration: {trip_details['duration']}")
            st.write(f"Driver: {trip_details['driver']['name']} (ID: {trip_details['driver']['id']})")
            st.write(f"Truck: {trip_details['truck']['brand']} {trip_details['truck']['model']} ({trip_details['truck']['plate']})")
            
        else:
            try:
                st.error(f'Error creating trip: {response.json().get("message", "Unknown error")}')
            except requests.exceptions.JSONDecodeError:
                st.error('Error creating trip: Invalid response from server')

def show_list_trips():
    st.title('TruckGuard - List of Trips')

    
    page = st.number_input('Page number', min_value=1, value=1) 
    per_page = st.number_input('Trips per page', min_value=1, value=10)

    if st.button('Fetch Trips'):
        
        headers = {
            'Authorization': f'Bearer {st.session_state["auth_token"]}',
            'Content-Type': 'application/json'
        }

        params = {
            'page': page,
            'per_page': per_page
        }
        response = requests.get(f'{api_url}/trips/all', headers=headers, params=params)

        if response.status_code == 200:
            try:
                data = response.json()
                trips = data.get('trips', [])
                
                # Mostrar información sobre la paginación
                st.write(f"Total trips: {data.get('total')}")
                # Mostrar los viajes en una tabla
                if trips:
                    for trip in trips:
                        st.write(f"Trip ID: {trip['id']}, Origin: {trip['origin']}, Destination: {trip['destination']}, Status: {trip['status']}")
                else:
                    st.write("No trips found on this page.")
            except ValueError:
                st.error("Received non-JSON response from the server.")
                st.text(response.text)
        else:
            st.error(f'Error fetching trips: {response.status_code}')
    else:
        st.info("Use the controls above to fetch trips.")



def show_get_trip():
    st.title('TruckGuard - Get Trip Details')
    trip_id = st.number_input('Trip ID', min_value=1)

    if st.button('Get Trip'):
        headers = {'Authorization': f'Bearer {st.session_state["auth_token"]}'}
        response = requests.get(f'{api_url}/trips/{trip_id}', headers=headers)

        if response.status_code == 200:
            trip = response.json().get('trip', {})
            st.write("Trip Data:")
            st.write(f"ID: {trip.get('id')}")
            st.write(f"Origin: {trip.get('origin')}")
            st.write(f"Destination: {trip.get('destination')}")
            st.write(f"Status: {trip.get('status')}")
            st.write(f"Updated At: {trip.get('updated_at')}")
            st.write("Driver Data:")
            st.write(f"Name: {trip.get('driver')}")
            st.write("Truck Data:")
            st.write(f"{trip.get('truck_details')}")

        else:
            st.error(f'Error fetching trip: {response.status_code}')
            st.text(response.text)


def change_trip_status_to_in_course_or_complete(trip_id):
    headers = {'Authorization': f'Bearer {st.session_state["auth_token"]}'}

    # Obtener detalles del viaje actual
    response = requests.get(f'{api_url}/trips/{trip_id}', headers=headers)
    if response.status_code == 200:
        trip = response.json().get('trip', {})
        current_status = trip.get('status')
        
        if current_status == 'In Course':
            # Cambiar el estado a 'Completed'
            try:
                update_response = requests.patch(
                    f'{api_url}/trips/{trip_id}/complete',
                    headers=headers
                )
                if update_response.status_code == 200:
                    st.success('Trip status updated to Completed')
                else:
                    st.error(f'Failed to update trip status: {update_response.text}')
            except requests.exceptions.RequestException as e:
                st.error(f'Request failed: {e}')
        elif current_status == 'Completed':
            st.warning('The trip is already completed.')
        else:
            # Cambiar el estado a 'In Course'
            try:
                update_response = requests.patch(
                    f'{api_url}/trips/{trip_id}/update',
                    headers=headers,
                    json={"status": "In Course"}
                )
                if update_response.status_code == 200:
                    st.success('Trip status updated to In Course')
                else:
                    st.error(f'Failed to update trip status: {update_response.text}')
            except requests.exceptions.RequestException as e:
                st.error(f'Request failed: {e}')
    else:
        st.error(f'Error fetching trip: {response.status_code}')
        st.text(response.text)
            

def complete_trip_directly(trip_id):
    headers = {'Authorization': f'Bearer {st.session_state["auth_token"]}'}

    # Obtener detalles del viaje actual
    response = requests.get(f'{api_url}/trips/{trip_id}', headers=headers)
    if response.status_code == 200:
        trip = response.json().get('trip', {})
        current_status = trip.get('status')
        
        if current_status == 'Completed':
            st.warning('The trip is already completed.')
        elif current_status == 'Pending':
            st.warning('The trip is still pending. Please change the status to "In Course" first.')
        else:
            try:
                # Realizar la solicitud PATCH para actualizar el estado del viaje
                update_response = requests.patch(
                    f'{api_url}/trips/{trip_id}/complete',
                    headers=headers
                )
                if update_response.status_code == 200:
                    st.success('Trip status updated to Completed')
                    st.write('Trip completed successfully!')
                    completed_trip = update_response.json()
                    st.write(f"Origin: {completed_trip['origin']}")
                    st.write(f"Destination: {completed_trip['destination']}")
                    st.write(f"distance: {completed_trip['distance']}")
                    st.write(f"duration: {completed_trip['duration']}")
                    #informacion del camion
                    st.write('Truck Details:')
                    st.write(f"Plate: {completed_trip['brand']}")
                    st.write(f"Model: {completed_trip['plate']}")
                else:
                    st.error(f'Failed to update trip status: {update_response.text}')
            except requests.exceptions.RequestException as e:
                st.error(f'Request failed: {e}')
    else:
        st.error(f'Error fetching trip: {response.status_code}')
        st.text(response.text)


  
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


def show_add_component_to_truck():
    st.title('Add New Component to Truck')

    # Form inputs
    truck_id = st.number_input('Truck ID', min_value=1)
    component = st.text_input('Component')
    description = st.text_input('Description')
    cost = st.number_input('Cost', min_value=0.0)
    driver_id = st.number_input('Driver ID', min_value=1)  # Si el camión siempre tiene un conductor asignado, puedes hacer esto opcional
    mileage_interval = st.number_input('Mileage Interval', min_value=0, value=10000)
    next_maintenance_mileage = st.number_input('Next Maintenance Mileage', min_value=0, value=10000)
    maintenance_interval = st.number_input('Maintenance Interval', min_value=0, value=10000)

    if st.button('Add Component'):
        component_data = {
            'truck_id': truck_id,
            'component': component,
            'description': description,
            'cost': cost,
            'driver_id': driver_id,
            'mileage_interval': mileage_interval,
            'next_maintenance_mileage': next_maintenance_mileage,
            'maintenance_interval': maintenance_interval
        }

        headers = {'Authorization': f'Bearer {st.session_state["auth_token"]}'}
        response = requests.post(f'{api_url}/maintenance/new', json=component_data, headers=headers)
        
        if response.status_code == 201:
            st.success('Component added successfully!')
        else:
            try:
                error_message = response.json().get("message", "Unknown error")
                st.error(f'Error adding component: {error_message}')
                st.text(response.json().get("error", ""))
            except requests.exceptions.JSONDecodeError:
                st.error('Error adding component: Invalid response from server')



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
        
        st.sidebar.title('TruckGuard')
        trip_options = st.sidebar.multiselect(
            "Trip Operations",
            ["Create Trip", "List Trips", "Get Trip", "Update Trip", "Delete Trip"]
        )

        driver_options = st.sidebar.multiselect(
            "Driver Operations",
            ["Change Trip Status to In Course or Complete", "Complete Trip Directly", "Add Component to Truck"]
        )

        truck_options = st.sidebar.multiselect(
            "Truck Operations",
            ["Create Truck", "assign truck to driver"]
        )

        analytics_options = st.sidebar.multiselect(
            "Analytics Operations",
            ["Component Radar Chart","List Trucks fleet"]
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

        if "Change Trip Status to In Course or Complete" in driver_options:
            trip_id = st.sidebar.number_input('Trip ID to change status', min_value=1)
            if st.sidebar.button('Change Status to In Course or Complete'):
                change_trip_status_to_in_course_or_complete(trip_id)
        if "Complete Trip Directly" in driver_options:
            trip_id = st.sidebar.number_input('Trip ID to complete directly', min_value=1)
            if st.sidebar.button('Complete Trip Directly'):
                complete_trip_directly(trip_id)
        if "Add Component to Truck" in driver_options:
            show_add_component_to_truck()




        if "Create Truck" in truck_options:
            show_create_truck()


        if "List Trucks fleet" in analytics_options:
            show_list_trucks()
        if "Component Radar Chart" in analytics_options:
            truck_id = st.sidebar.number_input('Truck ID', min_value=1, value=1)
            show_component_radar_chart(truck_id)

if __name__ == '__main__':
    main()
