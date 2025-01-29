import networkx as nx
import streamlit as st
import pandas as pd
import openrouteservice
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, value, LpStatus
import folium
from streamlit_folium import st_folium
from openrouteservice import Client
import random
import os

st.title("Optimiized Transportation Allocation System and Route Mapping App")
st.header("1. Upload Your Datasets")

st.success("All files uploaded successfully!")

# Initialize graph
graph = nx.DiGraph()

# Define nodes
factories = ['F1', 'F2']
warehouses = ['W1', 'W2']
clients = ['C1', 'C2', 'C3']

# Define edges (factories can supply clients directly or via warehouse)
edges = [
    ("F1", "W1", {"capacity": 20, "cost": 3}),
    ("F2", "W1", {"capacity": 100, "cost": 4}),
    ("F1", "W2", {"capacity": 50, "cost": 5}),
    ("F2", "W2", {"capacity": 50, "cost": 2}),
    ("F1", "C1", {"capacity": 30, "cost": 7}),  # Direct Factory → Client
    ("F2", "C3", {"capacity": 20, "cost": 4}),  # Direct Factory → Client
    ("W1", "C1", {"capacity": 50, "cost": 2}),
    ("W1", "C2", {"capacity": 50, "cost": 3}),
    ("W1", "C3", {"capacity": 50, "cost": 5}),
    ("W2", "C1", {"capacity": 50, "cost": 6}),
    ("W2", "C2", {"capacity": 50, "cost": 5}),
    ("W2", "C3", {"capacity": 50, "cost": 2}),
]

# Coordinates
pos = {
    'F1': (40.683872441380615, 22.885431620059066), 'F2': (40.65914244328182, 22.930129674916987),
    'W1': (40.682035715304806, 22.79503301938996), 'W2': (40.66904206130231, 22.93526513852292),
    'C1': (40.67563535503701, 22.938596579347777), 'C2': (40.6780147307032, 22.900261496603854), 'C3': (40.69467636963053, 22.84927806764901)
}

# Initialize ORS client (You would use your actual API key here)
api_key = "5b3ce3597851110001cf6248767bcf5a42874bb4b85b5b5c0bfac601"  # Replace with the actual key
client = openrouteservice.Client(key=api_key)

# Function to calculate travel time
def get_travel_time(start, end):
    try:
        # Swap coordinates: OpenRouteService requires [longitude, latitude]
        start_coords = (pos[start][1], pos[start][0])  # (latitude, longitude) -> (longitude, latitude)
        end_coords = (pos[end][1], pos[end][0])  # (latitude, longitude) -> (longitude, latitude)
        
        route = client.directions(
            coordinates=[start_coords, end_coords],
            profile='driving-car',  # Mode of transportation: car
            format='geojson'
        )

        if 'features' in route and len(route['features']) > 0:
            feature = route['features'][0]  # Access the first feature
            if 'properties' in feature and 'summary' in feature['properties']:
                duration_seconds = feature['properties']['summary']['duration']
                return duration_seconds / 60  # Convert to hours
            else:
                return None
        else:
            return None
    except Exception as e:
        return None

# Add edges to the graph with travel time
for edge in edges:
    source, target, data = edge
    travel_time = get_travel_time(source, target)
    data["travel_time"] = travel_time  # Add the travel time to the edge's attributes
    graph.add_edge(source, target, **data)


# Define optimization problem
problem = LpProblem("Supply_Chain_Optimization", LpMinimize)
edge_flows = LpVariable.dicts("Flow", graph.edges(), 0, None, cat='Continuous')

# Objective: Minimize total transportation cost
problem += lpSum([edge_flows[(u, v)] * graph[u][v]['travel_time'] * graph[u][v]['cost'] for u, v in graph.edges()]), "Total_Transportation_Cost"

# Define supply (factories) and demand (clients)
supply = {'F1': 50, 'F2': 50}
demand = {'C1': 30, 'C2': 10, 'C3': 60}

# Factory supply constraints
for factory in factories:
    problem += lpSum([edge_flows[(factory, v)] for v in graph.successors(factory)]) <= supply[factory], f"Supply_{factory}"

# Warehouse flow balance constraint
for warehouse in warehouses:
    problem += lpSum([edge_flows[(f, warehouse)] for f in factories]) == lpSum([edge_flows[(warehouse, c)] for c in clients]), f"Balance_{warehouse}"

# Client demand constraints
for client in clients:
    problem += lpSum([edge_flows[(u, client)] for u in graph.predecessors(client)]) == demand[client], f"Demand_{client}"

# Edge capacity constraints
for u, v in graph.edges():
    problem += edge_flows[(u, v)] <= graph[u][v]['capacity'], f"Capacity_{u}_{v}"

# Solve problem
problem.solve()

# Display status of the optimization problem
print("Problem Status")

if LpStatus[problem.status] == "Optimal":
    st.success(f"Status: {LpStatus[problem.status]}")
    st.subheader("2. Problem Results")
    
    st.write(f"Total Cost: {value(problem.objective)}")

    for u, v in graph.edges():
        if edge_flows[(u, v)].varValue > 0:
            st.text(f"Flow from {u} to {v}: {edge_flows[(u, v)].varValue:.2f}")


# Function to generate a random color in hex format
def generate_random_color():
    return "#{:02x}{:02x}{:02x}".format(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

# Calculate the midpoint of all supply (factories, warehouses) and demand (clients) coordinates dynamically
all_locations = list(pos.values())

# Calculate the average latitude and longitude
avg_lat = sum([location[0] for location in all_locations]) / len(all_locations)
avg_lon = sum([location[1] for location in all_locations]) / len(all_locations)

# Create a folium map centered at the calculated midpoint
mymap = folium.Map(location=[avg_lat, avg_lon], zoom_start=12, tiles='CartoDB positron')

# Add supply points (factories) to the map
supply_point_num = 1
for factory in factories:
    folium.Marker(
        location=[pos[factory][0], pos[factory][1]],  # Latitude, Longitude for folium
        popup=f"Supplier {factory}",
        icon=folium.Icon(color='blue', icon='info-sign')
    ).add_to(mymap)
    supply_point_num += 1

# Add warehouse points to the map
warehouse_point_num = 1
for warehouse in warehouses:
    folium.Marker(
        location=[pos[warehouse][0], pos[warehouse][1]],  # Latitude, Longitude for folium
        popup=f"Warehouse {warehouse}",
        icon=folium.Icon(color='orange', icon='info-sign')
    ).add_to(mymap)
    warehouse_point_num += 1

# Add demand points (clients) to the map
demand_point_num = 1
for client in clients:
    folium.Marker(
        location=[pos[client][0], pos[client][1]],  # Latitude, Longitude for folium
        popup=f"Client {client}",
        icon=folium.Icon(color='green', icon='info-sign')
    ).add_to(mymap)
    demand_point_num += 1

# Initialize supply_colors dictionary
supply_colors = {}

# Fetch and draw routes between supply (factories) and demand (clients)
for u, v in graph.edges():
    # Check if the edge connects a supply point (factory or warehouse) to a demand point (client)
    if u in factories + warehouses and v in clients:
        supply_point = u
        demand_point = v
    elif v in factories + warehouses and u in clients:
        supply_point = v
        demand_point = u
    else:
        continue  # Skip if the edge doesn't connect supply to demand
    
    # Create a unique identifier for this supplier (factories or warehouses)
    if supply_point not in supply_colors:
        supply_colors[supply_point] = generate_random_color()

    # Initialize ORS client (You would use your actual API key here)
    api_key = "5b3ce3597851110001cf6248767bcf5a42874bb4b85b5b5c0bfac601"  # Replace with the actual key
    client = openrouteservice.Client(key=api_key)

    # Get route data from ORS
    try:
        # Get coordinates for the supply and demand points
        supply_coords = (pos[supply_point][1], pos[supply_point][0])  
        demand_coords = (pos[demand_point][1], pos[demand_point][0])  

        # Fetch route from OpenRouteService
        route = client.directions(
            coordinates=[supply_coords, demand_coords],
            profile='driving-car',
            format='geojson'
        )

        # Check if the response contains routes
        if 'features' in route and len(route['features']) > 0:
            # Extract coordinates of the route
            route_coords = route['features'][0]['geometry']['coordinates']

            # Convert route coordinates to (lat, lon) for folium
            route_coords = [(coord[1], coord[0]) for coord in route_coords] 

            # Prepare popup content for the route
            popup_content = f"<b>Route from {supply_point} to {demand_point}</b><br>"

            # Use the preassigned color for this supplier
            route_color = supply_colors[supply_point]

            # Add the route to the map
            folium.PolyLine(
                locations=route_coords,
                color=route_color,
                weight=3,
                opacity=0.8,
                popup=folium.Popup(popup_content, max_width=300)
            ).add_to(mymap)
        else:
            print(f"No route found for {supply_point} and {demand_point}")
    except Exception as e:
        print(f"Error processing route for {supply_point} and {demand_point}: {e}")


# Save the map to an HTML file
static_map_path = "static_map.html"
mymap.save(static_map_path)

# Get the absolute path of the saved HTML file
html_path = os.path.abspath(static_map_path)

# Open the HTML file and read its content
with open(html_path, "r") as file:
    html_content = file.read()

st.components.v1.html(html_content, width=700, height=500)
