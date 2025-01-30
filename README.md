# 🚛Network Flow Application

## Overview

This Streamlit-based web application optimizes transportation allocation and visualizes supply chain routes using network flow optimization and OpenRouteService for route mapping.

👉 **Try the app here:** https://network-optimization-s9asz9csh3tlxpucyz7rp4.streamlit.app/

---

## Features
- **Data Upload:** Upload Data: Supports CSV files for **edges**, **nodes**, **coordinates**, and **demand/supply**.
- **Network Flow Optimization:** Uses PuLP to minimize transportation cost while ensuring supply-demand balance.
- **Route Mapping:** Integrates **OpenRouteService API** to compute real-time travel times.
- **Interactive Map Visualization:** Displays optimized routes using **Folium**.

## Mathematical Formulation

### Index Definitions
- $i$,$j$,$k$ -> Nodes in the Network
- $i \in F$ -> Factories (supply nodes)
- $j$ \in W -> Warehouses (warehouse nodes)
- $k$ \in C -> Store (store nodes)
- $(i,j)$ \in Directed edges in the network
### Decision Variables:
Let $x_{ij}$ be the flow of goods from node $i$ to node $j$.

### Paremeters
- $c_{ij}$ = Cost per unit flow from node $i$ to node $j$.
- $t_{ij}$ = Travel time from node $i$ to node $j$.
- $s_i$ = Supply available at node $i$ ($i$ is a factory).
- $d_j$ = Demand required at node $j$ ($j$ is a store).
- $u_{ij}$ = Capacity of the edge between $i$ and $j$.
- 
### Objective Function:
Minimize the total transportation cost, considering both travel time and cost:

$$
\min Z = \sum_{(i,j)} x_{ij} \cdot c_{ij} \cdot t_{ij}
$$

### Constraints:

1. **Supply Constraint** (Factories can’t ship more than they produce):

$$
\sum_{j \in V} x_{ij} \leq S_i \quad \forall i \in F
$$

2. **Flow Conservation at Warehouses** (Total inflow = Total outflow):

$$
\sum_{i=1}^{m} \sum_{k=1}^{p} x_{ijk} = D_j \quad \forall j
$$

3. **Driver Working Hours:**
   Ensure that the total time spent by each driver does not exceed their available working hours:

$$
\sum_{i=1}^{m} \sum_{j=1}^{n} y_{ijk} \cdot T_{ij} \leq H_k \quad \forall k
$$

4. **Driver Capacity:**
   Ensure that the total quantity delivered by each driver does not exceed their load capacity:

$$
x_{ijk} \leq Q_k \quad \forall i, j, k
$$

5. **Link between $x_{ijk}$ and $y_{ijk}$:**
   Ensure that $x_{ijk} > 0$ only if driver $k$ is assigned to the route from supply point $i$ to demand point $j$:

$$
x_{ijk} \leq y_{ijk} \cdot D_j \quad \forall i, j, k
$$

### Solving the Model:
The problem is solved using **PuLP**'s **LpProblem** method, which uses available solvers (e.g., CBC) to find the optimal solution.

### Map Visualization:
The application utilizes **Folium** to plot supply and demand points on a map, with routes between them drawn dynamically based on the optimized allocations. The **OpenRouteService API** is used to fetch travel times and distances between points.

## How to Use:

1. **Upload Your Data:** Upload the CSV files containing your **supply**, **demand**, **driver**, and **cost** data. The system expects data to include location coordinates (for mapping) and relevant values for optimization.
   
2. **View Results:** Once the model is solved, the application displays:
   - The allocation of drivers to supply-demand pairs.
   - The total transportation cost.
   - Dual values and slack values for constraints.
   - An interactive map showing the optimized routes.

3. **Download Map:** You can view the generated map, which visually represents the transportation routes between supply and demand locations.

## Requirements:
- **Python 3.x**
- **Streamlit**
- **Pandas**
- **OpenRouteService**
- **PuLP**
- **Folium**
- **OpenRouteService API Key**

## Example Data Format:

### Supply Data (`supply_data.csv`):
| Location | Latitude  | Longitude | Supply |
|----------|-----------|-----------|--------|
| Supply1  | 34.0522   | -118.2437 | 50     |
| Supply2  | 36.7783   | -119.4179 | 60     |

### Demand Data (`demand_data.csv`):
| Location | Latitude  | Longitude | Demand |
|----------|-----------|-----------|--------|
| client1  | 34.0522   | -118.2437 | 40     |
| client2  | 36.7783   | -119.4179 | 50     |

### Driver Data (`driver_data.csv`):
| DriverID | Working Hours  | Max Load (units) |
|----------|----------------|------------------|
| Driver1  | 10             | 8                |
| Driver2  | 15             | 10               |

### Cost Data (`cost_data.csv`):
| Client1 | Client2 | Client3 |
|---------|---------|---------|
| 200     | 100     | 150     |
| 300     | 120     | 140     |


## Acknowledgments
- **PuLP** for Linear Programming formulation.
- **OpenRouteService** for travel time and distance calculation.
- **Folium** for map visualization.
- **Stramlit** for web app deployment.

