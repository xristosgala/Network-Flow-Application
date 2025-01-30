# 🚛Network Flow Application

## Overview

This Streamlit-based web application optimizes transportation allocation and visualizes supply chain routes using network flow optimization and OpenRouteService for route mapping.

👉 **Try the app here:** [Network Flow Application](https://network-flow-application-etusnj3g5vv6xtt9txckl3.streamlit.app/)

---

## Features
- **Data Upload:** Upload Data: Supports CSV files for **edges**, **nodes**, **coordinates**, and **demand/supply**.
- **Network Flow Optimization:** Uses PuLP to minimize transportation cost while ensuring supply-demand balance.
- **Route Mapping:** Integrates **OpenRouteService API** to compute real-time travel times.
- **Interactive Map Visualization:** Displays optimized routes using **Folium**.

## Mathematical Formulation

### Index Definitions
- $i,j,k \in V = F \cup W \cup C$ -> Nodes in the Network
- $i \in F$ -> Factories (supply nodes)
- $j \in W$ -> Warehouses (warehouse nodes)
- $k \in C$ -> Store (store nodes)
- $(i,j) \in E$ -> Directed edges in the network

### Decision Variables:
Let $x_{ij}$ be the flow of goods from node $i$ to node $j$.

### Paremeters
- $c_{ij}$ = Cost per unit flow from node $i$ to node $j$.
- $t_{ij}$ = Travel time from node $i$ to node $j$.
- $s_i$ = Supply available at node $i$ ($i$ is a factory).
- $d_j$ = Demand required at node $j$ ($j$ is a store).
- $u_{ij}$ = Capacity of the edge between $i$ and $j$.

### Objective Function:
Minimize the total transportation cost, considering both travel time and cost:

$$
\min Z = \sum_{(i,j) \in E} x_{ij} \cdot c_{ij} \cdot t_{ij}
$$

### Constraints:

1. **Supply Constraint** (Factories can’t ship more than they produce):

$$
\sum_{j \in V} x_{ij} \leq S_i \quad \forall i \in F
$$

2. **Flow Conservation at Warehouses** (Total inflow = Total outflow):

$$
\sum_{i \in F} x_{ij} = \sum_{k \in C} D_{j,k} \quad \forall j \in W
$$

3. **Demand Constraint** (Clients must receive exact demand):

$$
\sum_{i \in V} x_{ik}  = D_k \quad \forall k \in C
$$

4. **Capacity Constraint** (Edges cannot exceed their max capacity):

$$
x_{ij} \leq U_ij \quad \forall (i,j) \in E
$$

5. **Non-Negativity Constraint:**

$$
x_{ij} \geq 0 \quad \forall (i,j) \in E
$$

## Technologies
- Python (NetworkX, PuLP, Pandas)
- Streamlit (Web UI)
- OpenRouteService API (Travel time estimation)
- Folium (Map visualization)

## Usage
- Upload CSV files for edges, nodes, coordinates, and demand/supply.
- View optimized transportation costs and flow allocation.
- Explore an interactive map with optimized routes.

## Sample Data Files:

### Edges Data (`edges.csv`):
| source | destination | capacity | cost |
|--------|-------------|----------|------|
| F1     | W1          | 20       | 3    |
| F2     | W1          | 100      | 4    |
| F1     | W2          | 50       | 3    |
| F2     | W2          | 50       | 4    |
| F1     | C1          | 30       | 7    |
| F2     | C3          | 20       | 4    |
| W1     | C1          | 50       | 2    |
| W1     | C2          | 50       | 3    |
| W1     | C3          | 50       | 5    |
| W1     | C1          | 50       | 6    |
| W2     | C2          | 50       | 5    |
| W3     | C3          | 50       | 2    |

### Coordinates Data (`coordinates.csv`):
| Node |     Latitude       | Longitude |
|------|--------------------|----------|
| F1   | 40.683872441380615 | 22.885431620059066 |
| F2   | 40.65914244328182  | 22.930129674916987 |
| W1   | 40.682035715304806 | 22.79503301938996  |
| W2   | 40.66904206130231  | 22.93526513852292  |
| C1   | 40.67563535503701  | 22.938596579347777 |
| C2   | 40.6780147307032   | 22.900261496603854 |
| C1   | 40.69467636963053  | 22.84927806764901  |

### Nodes Data (`nodes.csv`):
|    Type   | Node |
|-----------|------|
|  Factory  |  F1  |
|  Factory  |  F2  |
| Warehouse |  W1  |
| Warehouse |  W2  |
|   Client  |  C1  |
|   Client  |  C2  |
|   Client  |  C3  |

### Supply Demand Data (`supply_demand.csv`):
| Node |  Type  | Quantity |
|------|--------|----------|
| F1   | Supply |  50      |
| F2   | Supply |  50      |
| C1   | Demand |  30      |
| C2   | Demand |  10      |
| C3   | Demand |  60      |

