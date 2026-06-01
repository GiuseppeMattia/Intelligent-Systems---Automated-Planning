from pandas.core import generic
import os
import re
import csv
from pathlib import Path
import folium
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

script_dir = Path(__file__).parent.resolve()
remote_dir = script_dir.parent.parent.resolve()

stops_csv_path = os.getenv("PATH_TO_STOPS_CSV")
encoded_time_table_path = os.getenv("PATH_TO_ENCODED_TIME_TABLE_ASP")
map_path = os.getenv("PATH_TO_MAP_OUTPUT")

if stops_csv_path:
    stops_csv_path = Path(stops_csv_path)
    if not stops_csv_path.is_absolute():
        temp_path = (script_dir / stops_csv_path).resolve()
        if temp_path.exists():
            stops_csv_path = temp_path
        else:
            stops_csv_path = (remote_dir / stops_csv_path).resolve()
else:
    stops_csv_path = remote_dir / "res" / "sanitized" / "stops.csv"



def load_stops(csv_path):
    """dal CSV perché non le abbiamo in ASP :)"""
    stations_coords = {}
    stations_names = {}

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stop_id = row["stop_id"].strip()
            stop_name = row["stop_name"].strip()
            try:
                lat = float(row["stop_lat"].strip())
                lon = float(row["stop_lon"].strip())
                stations_coords[stop_id] = (lat, lon)
                stations_names[stop_id] = stop_name
            except (ValueError, TypeError):
                continue
                
    return stations_coords, stations_names


def load_shapes():
    shapes_df = pd.read_csv("../../res/sanitized/shapes.csv")
    shapes_df = shapes_df[~shapes_df['shape_id'].astype(str).str.startswith('7')]
    shapes_dict = {}
    shapes_df = shapes_df.sort_values(by=['shape_id', 'shape_pt_sequence'])


    for shape_id, rows_df in shapes_df.groupby('shape_id'):
        coord_list = list(zip(rows_df['shape_pt_lat'], rows_df['shape_pt_lon']))
        shapes_dict[shape_id] = coord_list

    return shapes_dict


def parse_asp_timetable(file_path):
    first_stations = {}  # trip_id -> station_id
    next_stations = {}   # trip_id -> {station_from: station_to}
    
    first_pattern = re.compile(r'first_station\("([^"]+)"\s*,\s*"([^"]+)"\)')
    next_pattern = re.compile(r'next_station\("([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\)')

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("%"):
                continue
                
            m_first = first_pattern.search(line)
            if m_first:
                trip_id, station_id = m_first.groups()
                first_stations[trip_id] = station_id
                continue
                
            m_next = next_pattern.search(line)
            if m_next:
                trip_id, station_from, station_to = m_next.groups()
                if trip_id not in next_stations:
                    next_stations[trip_id] = {}
                next_stations[trip_id][station_from] = station_to
                
    return first_stations, next_stations


def reconstruct_routes(first_stations, next_stations):
    routes = {}
    for trip_id, start_station in first_stations.items():
        route = []
        curr = start_station
        visited = set()
        while curr and curr not in visited:  
            visited.add(curr)                   # per evitare eventuale while a vita
            route.append(curr)
            curr = next_stations.get(trip_id, {}).get(curr)
        routes[trip_id] = route
    return routes


def group_by_trip_id(routes):
    """Raggruppa i trip_id che hanno lo stesso percorso fisico (sequenza di stazioni)."""
    unique_paths = {}
    for trip_id, path in routes.items():
        if not path:
            continue
        path_key = tuple(path)
        if path_key not in unique_paths:
            unique_paths[path_key] = []
        unique_paths[path_key].append(trip_id)
    return unique_paths


def main():
    print("Inizio elaborazione dati...")
    
    stations_coords, stations_names = load_stops(stops_csv_path)
    print(f"Stazioni caricate da stops.csv: {len(stations_coords)}")

    shapes_coord = load_shapes()
    
    first_stations, next_stations = parse_asp_timetable(encoded_time_table_path)
    print(f"Fatti ASP analizzati: first_station={len(first_stations)}, next_station={len(next_stations)}")
    
    routes = reconstruct_routes(first_stations, next_stations)
    
    unique_paths = group_by_trip_id(routes)
    print(f"Corse totali: {len(routes)}")
    print(f"Percorsi unici: {len(unique_paths)}")
    
    if not unique_paths:
        print("Nessun percorso")
        return
        
    mappa = folium.Map(location=[40.1807, 9.0821], zoom_start=8, tiles=None)
    
    folium.TileLayer('cartodbpositron', name='Light Mode').add_to(mappa)
    folium.TileLayer('cartodbdarkmatter', name='Dark Mode').add_to(mappa)
    
    STATION_COLORS = {
        "830012891": "#1E88E5",  # CAGLIARI -> Electric Blue
        "830012807": "#E53935",  # SASSARI -> Crimson Red
        "830012855": "#43A047",  # OLBIA -> Emerald Green
        "830012950": "#FB8C00",  # IGLESIAS -> Vibrant Orange
        "830012878": "#8E24AA",  # ORISTANO -> Rich Purple
        "830013703": "#00ACC1",  # Carbonia Serbariu -> Deep Cyan
        "830012852": "#D81B60",  # GOLFO ARANCI -> Deep Pink
        "830012869": "#FDD835",  # MACOMER -> Amber Gold
        "830012882": "#3949AB",  # S.GAVINO (SAN GAVINO MONREALE) -> Indigo
        "830012888": "#00897B",  # DECIMOMANNU -> Teal
        "830012952": "#7CB342",  # VILLAMASSARGIA DOMUSNOVAS -> Light Green
        "830012818": "#F4511E",  # PORTO TORRES MARITTIMA -> Deep Orange
        "830012862": "#5E35B1",  # OZIERI CHILIVANI -> Deep Violet
        "830012902": "#039BE5",  # Olbia Terranova -> Light Blue
    }
    
    def get_station_color(station_id):
        if station_id in STATION_COLORS:
            return STATION_COLORS[station_id]
        fallback_colors = [
            "#D81B60", "#8E24AA", "#5E35B1", "#3949AB", "#1E88E5", 
            "#039BE5", "#00ACC1", "#00897B", "#43A047", "#7CB342", 
            "#FDD835", "#FB8C00", "#F4511E"
        ]
        hash_val = sum(ord(c) for c in station_id)
        return fallback_colors[hash_val % len(fallback_colors)]
        
    # active_starts = sorted(
    #     list(set(path_key[0] for path_key in unique_paths.keys() if path_key)),
    #     key=lambda sid: stations_names.get(sid, sid)
    # )   # in ordine alfabetico
    
    # feature_groups = {} # dictionary di feature groups, uno per ogni stazione di partenza
    #                     # per il filtro legenda
    # for sid in active_starts:
    #     name = stations_names.get(sid, sid)
    #     clean_name = name.replace("Stazione di ", "")
    #     group_name = f"Partenze da {clean_name}"
    #     fg = folium.FeatureGroup(name=group_name)
    #     feature_groups[sid] = fg

    feature_groups = {}  # trip_id -> FeatureGroup
    for path_key, trips in unique_paths.items():
        for trip_id in trips:
            fg = folium.FeatureGroup(name=f"Trip {trip_id}", show=False)
            feature_groups[trip_id] = fg
        
    active_stations = set()
    for path_key, trips in unique_paths.items():
        start_id = path_key[0]
        end_id = path_key[-1]

        valid_path_station_names = []
        for sid in path_key:
            if sid in stations_coords:
                valid_path_station_names.append(stations_names.get(sid, sid).replace("Stazione di ", ""))
                active_stations.add(sid)
                
        representative_trip = trips[0]
        
        if representative_trip in shapes_coord:
            coordinates = shapes_coord[representative_trip]
        else:
            coordinates = [stations_coords[sid] for sid in path_key if sid in stations_coords]
                
        if len(coordinates) < 2:
            continue

        start_name = stations_names.get(start_id, start_id).replace("Stazione di ", "")
        end_name = stations_names.get(end_id, end_id).replace("Stazione di ", "")
        color = get_station_color(start_id)
        # fg = feature_groups[start_id]
        
        stops_str = " → ".join(valid_path_station_names)
        trips_str = ", ".join(trips[:5])
        if len(trips) > 5:
            trips_str += f" e altre {len(trips) - 5} corse"
            
        popup_html = f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 13px; color: #333; line-height: 1.5; min-width: 220px; max-width: 300px;">
            <h4 style="margin: 0 0 5px; color: {color}; font-size: 14px; border-bottom: 2px solid #eee; padding-bottom: 3px; font-weight: 600;">
                Tratta: {start_name} &rarr; {end_name}
            </h4>
            <div style="margin-top: 8px;">
                <b>Fermate ({len(valid_path_station_names)}):</b><br>
                <span style="color: #555; font-size: 11px; word-break: break-word;">{stops_str}</span>
            </div>
            <div style="margin-top: 8px; border-top: 1px solid #eee; padding-top: 5px; font-size: 11px;">
                <b>Corse totali:</b> {len(trips)}<br>
                <span style="color: #777; font-size: 10px; font-family: monospace; word-break: break-word;">{trips_str}</span>
            </div>
        </div>
        """
        
        # folium.PolyLine(
        #     locations=coordinates,
        #     color=color,
        #     weight=4.5,
        #     opacity=0.8,
        #     popup=folium.Popup(popup_html, max_width=300),
        #     tooltip=f"Tratta: {start_name} → {end_name} ({len(trips)} corse)"
        # ).add_to(fg)

        for trip_id in trips:
            fg = feature_groups[trip_id]
            folium.PolyLine(
                locations=coordinates,
                color=color,
                weight=4.5,
                opacity=0.8,
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"Trip: {trip_id} — {start_name} → {end_name}"
            ).add_to(fg)
        
    group_stazioni = folium.FeatureGroup(name="Stazioni", control=True)
    
    for sid in active_stations:
        if sid not in stations_coords:
            continue
        coords = stations_coords[sid]
        name = stations_names.get(sid, sid)
        clean_name = name.replace("Stazione di ", "")
        
        serving_routes = []
        for path_key, trips in unique_paths.items():
            if sid in path_key:
                s_name = stations_names.get(path_key[0], path_key[0]).replace("Stazione di ", "")
                e_name = stations_names.get(path_key[-1], path_key[-1]).replace("Stazione di ", "")
                serving_routes.append(f"• {s_name} &rarr; {e_name} ({len(trips)} corse)")
                
        routes_list_str = "<br>".join(serving_routes[:6])
        if len(serving_routes) > 6:
            routes_list_str += f"<br>• e altre {len(serving_routes) - 6} tratte..."
            
        station_popup_html = f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 13px; color: #333; line-height: 1.5; min-width: 200px;">
            <h4 style="margin: 0 0 5px; color: #37474F; font-size: 14px; border-bottom: 2px solid #eee; padding-bottom: 3px; font-weight: 600;">
                {clean_name}
            </h4>
            <div style="margin-top: 8px; font-size: 11px;">
                <b>Tratte passanti ({len(serving_routes)}):</b><br>
                <div style="max-height: 150px; overflow-y: auto; margin-top: 5px; color: #555; line-height: 1.4;">
                    {routes_list_str}
                </div>
            </div>
        </div>
        """
        
        folium.CircleMarker(
            location=coords,
            radius=6,
            color="#37474F",
            weight=2,
            fill=True,
            fill_color="#FFFFFF",
            fill_opacity=1.0,
            popup=folium.Popup(station_popup_html, max_width=250),
            tooltip=clean_name
        ).add_to(group_stazioni)
        
    # for sid in active_starts:
    #     mappa.add_child(feature_groups[sid])
    # mappa.add_child(group_stazioni)

    for fg in feature_groups.values():
        mappa.add_child(fg)
    mappa.add_child(group_stazioni)
    
    folium.LayerControl(position='topright', collapsed=False).add_to(mappa)
    
    stats_html = f"""
    <div style="position: fixed; 
                bottom: 20px; left: 20px; width: 300px; height: auto; 
                z-index:9999; font-size:14px;
                background-color: rgba(33, 33, 33, 0.85);
                color: white;
                padding: 15px; border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.4);
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                border: 1px solid rgba(255,255,255,0.15);">
        
        <div style="font-size:12px; line-height: 1.6; color: #eceff1;">
            <b>Statistiche</b><br>
            <span style="color: #ffb74d;">•</span> Corse Totali (Trip IDs): <b style="color: #fff;">{len(routes)}</b><br>
            <span style="color: #81c784;">•</span> Percorsi Fisici Unici: <b style="color: #fff;">{len(unique_paths)}</b><br>
            <span style="color: #64b5f6;">•</span> Stazioni Attive: <b style="color: #fff;">{len(active_stations)}</b>
        </div>
    </div>
    """
    mappa.get_root().html.add_child(folium.Element(stats_html))
    #buttons to show every trip or to don't show any trip at all
    buttons_html = """
    <style>
        .toggle-btn {
            padding: 8px 14px; border-radius: 8px; border: none; cursor: pointer;
            background-color: silver; color: white; font-size: 13px; font-weight: 600;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            transition: background-color 0.2s ease;
        }
        .toggle-btn:hover {
            background-color: #909090;
        }
    </style>
    <div style="position: fixed;
                top: 10px; left: 50px;
                z-index: 9999;
                display: flex; gap: 8px;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
        <button class="toggle-btn" onclick="toggleAllLayers(true)">Tutte le corse</button>
        <button class="toggle-btn" onclick="toggleAllLayers(false)">Nessuna corsa</button>
    </div>
    <script>
        function toggleAllLayers(show) {
            document.querySelectorAll('.leaflet-control-layers-overlays input[type=checkbox]').forEach(function(cb) {
                var label = cb.closest('label');
                if (cb.checked !== show && !label.innerText.trim().startsWith('Stazioni')){
                    cb.click();
                    } 
            });
        }
    </script>
    """
    mappa.get_root().html.add_child(folium.Element(buttons_html))
 
    mappa.save(map_path)
    print(f"Mappa generata e salvata in: {map_path}")


if __name__ == "__main__":
    main()