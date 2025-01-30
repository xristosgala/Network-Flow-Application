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

st.title("Network Flow Application")
st.header("1. Upload Your Datasets")

# Upload the three CSV files
edges_data = st.file_uploader("Choose the Edges Data CSV file", type=["csv"])
nodes_data = st.file_uploader("Choose the Nodes Data CSV file", type=["csv"])
coordinates_data = st.file_uploader("Choose the Coordinates Data CSV file", type=["csv"])
demand_supply_data = st.file_uploader("Choose the Demand/Supply Data CSV file", type=["csv"])

if edges_data is not None and nodes_data is not None and coordinates_data is not None and demand_supply_data is not None:
    # Load the datasets
    edges_df = pd.read_csv(edges_data)
    nodes_df = pd.read_csv(nodes_data)
    coordinates_df = pd.read_csv(coordinates_data)
    demand_supply_df = pd.read_csv(demand_supply_data)

    #Transform the dataframes into meaningful structures
    edges = [(row['source'], row['destination'], {"capacity": row['capacity'], "cost": row['cost']}) for _, row in edges_df.iterrows()]
    factories = nodes_df[nodes_df["Type"] == "Factory"]["Node"].tolist()
    warehouses = nodes_df[nodes_df["Type"] == "Warehouse"]["Node"].tolist()
    stores = nodes_df[nodes_df["Type"] == "Store"]["Node"].tolist()
    pos = {row["Node"]: (row["Latitude"], row["Longitude"]) for _, row in coordinates_df.iterrows()}
    supply = {row["Node"]: row["Quantity"] for _, row in demand_supply_df[demand_supply_df["Type"] == "Supply"].iterrows()}
    demand = {row["Node"]: row["Quantity"] for _, row in demand_supply_df[demand_supply_df["Type"] == "Demand"].iterrows()}

    st.success("All files uploaded successfully!")
    
    # Initialize graph
    graph = nx.DiGraph()
    
    # Initialize ORS client (You would use your actual API key here)
    # Access the API key securely from Streamlit secrets
    api_key = st.secrets["api_key"]
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
    
    # Factory supply constraints
    for factory in factories:
        problem += lpSum([edge_flows[(factory, v)] for v in graph.successors(factory)]) <= supply[factory], f"Supply_{factory}"
    
    # Warehouse flow balance constraint
    for warehouse in warehouses:
        problem += lpSum([edge_flows[(f, warehouse)] for f in factories]) == lpSum([edge_flows[(warehouse, c)] for c in stores]), f"Balance_{warehouse}"
    
    # Client demand constraints
    for store in stores:
        problem += lpSum([edge_flows[(u, store)] for u in graph.predecessors(store)]) == demand[store], f"Demand_{store}"
    
    # Edge capacity constraints
    for u, v in graph.edges():
        problem += edge_flows[(u, v)] <= graph[u][v]['capacity'], f"Capacity_{u}_{v}"
    
    # Solve problem
    problem.solve()
    
    # Display status of the optimization problem
    
    if LpStatus[problem.status] == "Optimal":
        st.success(f"Status: {LpStatus[problem.status]}")
        
        st.header("2. Problem Results")
        
        st.write(f"Total Cost: {value(problem.objective)}")
    
        for u, v in graph.edges():
            if edge_flows[(u, v)].varValue > 0:
                st.text(f"Flow from {u} to {v}: {edge_flows[(u, v)].varValue:.2f}")
    
    
        # Function to generate a random color in hex format
        def generate_random_color():
            return "#{:02x}{:02x}{:02x}".format(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        
        # Calculate the midpoint of all supply (factories, warehouses) and demand (stores) coordinates dynamically
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
                popup=f"Factory {factory}",
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
        
        # Add demand points (stores) to the map
        demand_point_num = 1
        for store in stores:
            folium.Marker(
                location=[pos[store][0], pos[store][1]],  # Latitude, Longitude for folium
                popup=f"Store {store}",
                icon=folium.Icon(color='green', icon='info-sign')
            ).add_to(mymap)
            demand_point_num += 1
            
        # Define colors for different route types
        route_colors = {
            "factory_to_warehouse": "blue",
            "warehouse_to_store": "green",
            "factory_to_store": "orange",
        }
        
        # Normalize flow values for line thickness
        max_flow = max(edge_flows[(u, v)].varValue for u, v in graph.edges() if edge_flows[(u, v)].varValue > 0)
        min_thickness = 2
        max_thickness = 6
        
        # Iterate over each edge in the graph
        for u, v in graph.edges():
            flow_value = edge_flows[(u, v)].varValue
        
            if flow_value > 0:  # Only show active routes
                # Determine route type
                if u in factories and v in warehouses:
                    route_type = "factory_to_warehouse"
                elif u in warehouses and v in stores:
                    route_type = "warehouse_to_store"
                elif u in factories and v in stores:
                    route_type = "factory_to_store"
                else:
                    continue  # Skip unexpected cases
        
                route_color = route_colors[route_type]
        
                # Normalize line thickness based on flow
                line_thickness = min_thickness + (flow_value / max_flow) * (max_thickness - min_thickness)
        
                # Fetch route and draw on map
                try:
                    supply_coords = (pos[u][1], pos[u][0])  
                    demand_coords = (pos[v][1], pos[v][0])  
        
                    route = client.directions(
                        coordinates=[supply_coords, demand_coords],
                        profile='driving-car',
                        format='geojson'
                    )
        
                    if 'features' in route and len(route['features']) > 0:
                        route_coords = route['features'][0]['geometry']['coordinates']
                        route_coords = [(coord[1], coord[0]) for coord in route_coords]
        
                        # Prepare popup with flow quantity
                        popup_content = f"<b>Route {u} → {v}</b><br>Flow: {flow_value:.2f}"
        
                        # Draw the route with dynamic thickness
                        folium.PolyLine(
                            locations=route_coords,
                            color=route_color,
                            weight=line_thickness,
                            opacity=0.8,
                            popup=folium.Popup(popup_content, max_width=300)
                        ).add_to(mymap)
                except Exception as e:
                    print(f"Error processing route for {u} and {v}: {e}")


        
        
        # Save the map to an HTML file
        static_map_path = "static_map.html"
        mymap.save(static_map_path)
        
        # Get the absolute path of the saved HTML file
        html_path = os.path.abspath(static_map_path)
        
        # Open the HTML file and read its content
        with open(html_path, "r") as file:
            html_content = file.read()

        st.header("3. Map Visualization")
        
        st.components.v1.html(html_content, width=700, height=500)
    else:
        st.error(f"Status: {LpStatus[problem.status]}")
else:
    st.error("Not all files are valid")
