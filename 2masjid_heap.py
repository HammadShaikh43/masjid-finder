from function import *
from data import graph, locations, destination_cities
import tkinter as tk
from tkinter import scrolledtext, messagebox
import folium
import threading
import webview
import requests



# Create the map and save it to an HTML file

def run_search():
    try:
        # Retrieve location from the input fields
        lon = float(lon_entry.get())
        lat = float(lat_entry.get())
        current_location = (lon, lat)
        
        # Find the closest node
        closest_node, distance = find_closest_node(locations, current_location)
        output_text.delete(1.0, tk.END)
        output_text.insert(tk.END, f"The closest node to the current location is {closest_node} at a distance of {distance:.2f} km.\n")
        
        # Run Dijkstra's algorithm
        distances, previous = dijkstra_with_path(graph, closest_node, locations)

        # Determine the nearest mosque
        min_distance = float('inf')
        nearest_mosque = None
        path_to_nearest = []
        for city in destination_cities:
            if city in distances and distances[city] < min_distance:
                min_distance = distances[city]
                nearest_mosque = city
                path_to_nearest = reconstruct_path(previous, closest_node, city)
                print(f"Path to {city}: {path_to_nearest} with distance: {min_distance} km")
        
        # Display the results for the nearest mosque
        if nearest_mosque:
            output_text.insert(tk.END, "*************************************************************\n")
            output_text.insert(tk.END, f"Nearest Mosque: {nearest_mosque}\n")
            output_text.insert(tk.END, f"Distance: {min_distance:.2f} km\n")
            output_text.insert(tk.END, f"Path: {path_to_nearest}\n")
            output_text.insert(tk.END, "*************************************************************\n")
        else:
            output_text.insert(tk.END, "No path found to any mosque.\n")

    except Exception as e:
        output_text.delete(1.0, tk.END)
        output_text.insert(tk.END, f"Error: {str(e)}")

# Set up the main application window
app = tk.Tk()
app.title("Mosque Locator")

tk.Label(app, text="Latitude:").pack()
lat_entry = tk.Entry(app)
lat_entry.pack()

# Longitude and Latitude Entry
tk.Label(app, text="Longitude:").pack()
lon_entry = tk.Entry(app)
lon_entry.pack()

# Search Button
search_button = tk.Button(app, text="Find Nearest Mosque", command=run_search)
search_button.pack()

def calculate_bearing(lat1, lon1, lat2, lon2):
    # Convert degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Calculate the bearing
    d_lon = lon2 - lon1
    x = math.sin(d_lon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(d_lon))
    bearing = math.atan2(x, y)
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360  # Normalize to 0-360
    return bearing

def add_short_arrow(map_object, lat, lon, length=0.001):
    # Kaabah's coordinates
    kaabah_lat, kaabah_lon = 21.4225, 39.8262
    bearing = calculate_bearing(lat, lon, kaabah_lat, kaabah_lon)
    
    # Calculate endpoint of the arrow
    end_lat = lat + length * math.cos(math.radians(bearing))
    end_lon = lon + length * math.sin(math.radians(bearing))
    
    # Define an arrow
    arrow = folium.PolyLine([(lat, lon), (end_lat, end_lon)], color='red', weight=5, opacity=0.8)
    map_object.add_child(arrow)

    # Optionally add an arrowhead using a rotated marker
    arrow_head = folium.RegularPolygonMarker(location=(end_lat, end_lon), number_of_sides=3, radius=10, weight=10, rotation=bearing+20, color='red', fill_color='red')
    map_object.add_child(arrow_head)

    return map_object


def create_and_show_map():
    try:
        lon = float(lon_entry.get())
        lat = float(lat_entry.get())
        current_location = (lon, lat)
        
        m = folium.Map(location=[lat, lon], zoom_start=17)  # Center on current location with appropriate zoom level
        m = add_short_arrow(m, lat, lon)

        closest_node, _ = find_closest_node(locations, current_location)
        distances, previous = dijkstra_with_path(graph, closest_node, locations)

        m.add_child(folium.ClickForMarker())
        folium.Marker()
        m.add_child(folium.LatLngPopup())

        min_distance = float('inf')
        nearest_mosque = None
        path_to_nearest = []

        # Determine the nearest mosque and reconstruct path
        for city in destination_cities:
            if city in distances and distances[city] < min_distance:
                min_distance = distances[city]
                nearest_mosque = city
                path_to_nearest = reconstruct_path(previous, closest_node, city)

        # Add markers for all nodes in the path, including the nearest mosque
        if nearest_mosque:
            # Mark the current location
            folium.Marker([lat, lon], popup="Current Location", icon=folium.Icon(color='green')).add_to(m)

            # Mark the closest node
            closest_coords = locations[closest_node]['coords']
            folium.Marker([closest_coords[1], closest_coords[0]], popup=f"Closest Node: {closest_node}", icon=folium.Icon(color='blue')).add_to(m)

            # Draw path from current location to the closest node
            folium.PolyLine([
                [lat, lon],
                [closest_coords[1], closest_coords[0]]
            ], color="blue", weight=2.5, opacity=0.5).add_to(m)

            # Iterate over the path to the nearest mosque and add markers and paths
            last_coords = closest_coords
            for node in path_to_nearest:
                node_coords = locations[node]['coords']
                if node in destination_cities:  # Check if it's a mosque
                    icon_color = 'red'
                else:
                    icon_color = 'blue'
                folium.Marker([node_coords[1], node_coords[0]], popup=node, icon=folium.Icon(color=icon_color)).add_to(m)
                folium.PolyLine([
                    [last_coords[1], last_coords[0]],
                    [node_coords[1], node_coords[0]]
                ], color="blue", weight=2.5, opacity=0.5).add_to(m)
                last_coords = node_coords

        # Save to HTML and show path details in the interface
        m.save('map.html')
        map_html = m._repr_html_()
        window = webview.create_window('Map', html=map_html)
        webview.start(func=resize_window, args=(window,))
        return m._repr_html_()
    except Exception as e:
        messagebox.showerror("Error", str(e))

def resize_window(window):
    # Resize the window after it has been created
    window.resize(1200, 760)  # Resize to width=1024px, height=768px

def render_full_map():
    # Extracting coordinates from the locations dictionary and reversing the order
    try:
        coordinates = [(location["coords"][1], location["coords"][0]) for location in locations.values()]

        # Create a map centered around the mean of the coordinates
        m = folium.Map(location=[sum([coord[0] for coord in coordinates])/len(coordinates),
                                sum([coord[1] for coord in coordinates])/len(coordinates)], 
                    zoom_start=15)
        
        m.add_child(folium.ClickForMarker())
        folium.Marker()
        m.add_child(folium.LatLngPopup())

        # Add markers for each location
        for name, coords in locations.items():
            if name in destination_cities:
                # For mosques, use a different icon
                folium.Marker((coords['coords'][1], coords['coords'][0]), popup=name, icon=folium.Icon(color='red')).add_to(m)
            else:
                # For other locations, use the default icon
                folium.Marker((coords['coords'][1], coords['coords'][0]), popup=name).add_to(m)

        # Add paths between the nodes
        for node, connections in graph.items():
            start_coords = locations[node]["coords"]
            for connected_node in connections:
                end_coords = locations[connected_node]["coords"]
                folium.PolyLine([(start_coords[1], start_coords[0]), (end_coords[1], end_coords[0])], color="blue").add_to(m)

        # Display the map
        m.save('map.html')
        map_html = m._repr_html_()
        window = webview.create_window('Map', html=map_html)
        webview.start(func=resize_window, args=(window,))
        return m._repr_html_()
    except Exception as e:
        messagebox.showerror("Error", str(e))



def get_location_coordinates_by_ip(ip_address=None):
    access_token = '75f674ee331835'  # Replace with your API token from ipinfo.io
    if ip_address:
        url = f"https://ipinfo.io/{ip_address}/json?token={access_token}"
    else:
        url = f"https://ipinfo.io/json?token={access_token}"  # Uses your own IP if none specified
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises a HTTPError for bad responses
        data = response.json()
        location = data.get('loc', 'No location found')  # Extracts 'loc' or returns 'No location found'
        loca = location.split(',')
        lat_entry.delete(0, tk.END)
        lon_entry.delete(0, tk.END)
        lat_entry.insert(0, loca[0])
        lon_entry.insert(0, loca[1])
        output_text.delete(1.0, tk.END)
        output_text.insert(tk.END, f"Current Location Found: {location}\n")
        return location
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None
    
def which_map_to_show():
    # If longitude and latitude input are empty show full map
    if lat_entry.get() == '' and lon_entry.get() == '':
        render_full_map()
    else:
        create_and_show_map()

get_location_button = tk.Button(app, text="Get Current Location", command=get_location_coordinates_by_ip)
get_location_button.pack()

# Button to create and show the map
map_button = tk.Button(app, text="Show Map", command=which_map_to_show)
map_button.pack()

output_text = scrolledtext.ScrolledText(app, width=70, height=20)
output_text.pack()

app.mainloop()