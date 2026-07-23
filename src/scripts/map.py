import sys
import os
import re
import csv
import json
from pathlib import Path
import folium
import pandas as pd

from dotenv import load_dotenv
load_dotenv()

script_dir = Path(__file__).parent.resolve()
remote_dir = script_dir.parent.parent.resolve()

def resolve_path(env_path, default_relative):
    if env_path:
        p = Path(env_path)
        if not p.is_absolute():
            temp_path = (script_dir / p).resolve()
            if temp_path.exists() or temp_path.parent.exists():
                return temp_path
            return (remote_dir / p).resolve()
        return p
    return (remote_dir / default_relative).resolve()

stops_csv_path = resolve_path(os.getenv("PATH_TO_STOPS_CSV"), "res/sanitized/stops.csv")
standard_timetable_path = resolve_path(os.getenv("PATH_TO_OPT_FER"), "res/output/ottimizzazione_fermate.asp")
optimized_timetable_path = resolve_path(os.getenv("PATH_TO_OPT_NUM"), "res/output/ottimizzazione_number.asp")


def load_stops(csv_path):
    """carica le stazioni - dal CSV perché non le abbiamo in ASP con le coordinate :)"""
    stations_coords = {}
    stations_names = {}

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stop_id = row["stop_id"].strip()
            stop_name = row["stop_name"].strip().upper()
            try:
                lat = float(row["stop_lat"].strip())
                lon = float(row["stop_lon"].strip())
                stations_coords[stop_id] = (lat, lon)
                stations_names[stop_id] = stop_name
            except (ValueError, TypeError):
                continue
                
    return stations_coords, stations_names


def load_shapes():
    """Carica le coordinate dei shapes da shapes.csv"""
    shapes_path = remote_dir / "res" / "sanitized" / "shapes.csv"
    shapes_df = pd.read_csv(shapes_path)
    shapes_df = shapes_df[~shapes_df['shape_id'].astype(str).str.startswith('7')]
    shapes_dict = {}
    shapes_df = shapes_df.sort_values(by=['shape_id', 'shape_pt_sequence'])


    for shape_id, rows_df in shapes_df.groupby('shape_id'):
        coord_list = list(zip(rows_df['shape_pt_lat'], rows_df['shape_pt_lon']))
        shapes_dict[shape_id] = coord_list

    return shapes_dict


def format_time_minutes(t):
    try:
        minutes = int(str(t).strip('"'))
        hours = (minutes // 60) % 24
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
    except (ValueError, TypeError):
        return str(t).strip('"')


def parse_asp_timetable(file_paths):
    """Parsa i file ASP e restituisce informazioni sulle corse, stazioni, orari e assegnazioni dei treni."""
    eff_first_stations = {} # trip_id -> station_id
    last_stations = {}   # trip_id -> station_id
    eff_next_stations = {} # trip_id -> {station_from: station_to}
    allowed_next_stations = {}  # trip_id -> {station_from: station_to}
    skipped_edges = {}  # trip_id -> {(station_from, station_to)}
    new_station_map = {}  # old_station_id -> new_station_id
    trip_train_assignments = {}  # trip_id -> train_id
    trip_dep_times = {}  # trip_id -> dep_time_str
    trip_arr_times = {}  # trip_id -> arr_time_str
    station_dep_times = {}  # trip_id -> {station_id: dep_time_str}
    station_arr_times = {}  # trip_id -> {station_id: arr_time_str}

    if isinstance(file_paths, (str, Path)):
        file_paths = [file_paths]

    eff_first_pattern = re.compile(r'^\s*effective_first_station\("([^"]+)"\s*,\s*"([^"]+)"\)')
    last_pattern = re.compile(r'^\s*last_station\("([^"]+)"\s*,\s*"([^"]+)"\)')
    allowed_next_pattern = re.compile(r'^\s*allowed_next_station\("([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\)')
    eff_next_pattern = re.compile(r'^\s*effective_next_station\("([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\)')
    salta_pattern = re.compile(r'^\s*salta\("([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\)')
    new_station_pattern = re.compile(r'^\s*new_station\("([^"]+)"\s*,\s*"([^"]+)"\)')
    assign_trip_pattern = re.compile(r'^\s*assign_trip_train\("([^"]+)"\s*,\s*\d+\s*,\s*(\d+)\)')
    trip_dep_pattern = re.compile(r'^\s*trip_departure_time\("([^"]+)"\s*,\s*(\d+|"[^"]+")\)')
    trip_arr_pattern = re.compile(r'^\s*trip_arrival_time\("([^"]+)"\s*,\s*(\d+|"[^"]+")\)')
    station_dep_pattern = re.compile(r'^\s*departure_time\("([^"]+)"\s*,\s*"([^"]+)"\s*,\s*(\d+|"[^"]+")\)')
    station_arr_pattern = re.compile(r'^\s*arrival_time\("([^"]+)"\s*,\s*"([^"]+)"\s*,\s*(\d+|"[^"]+")\)')

    for file_path in file_paths:
        if not file_path:
            continue

        resolved_path = Path(file_path)
        if not resolved_path.exists():
            continue

        with open(resolved_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("%"):
                    continue

                m_eff_first = eff_first_pattern.search(line)
                if m_eff_first:
                    trip_id, station_id = m_eff_first.groups()
                    eff_first_stations[trip_id] = station_id
                    continue

                m_last = last_pattern.search(line)
                if m_last:
                    trip_id, station_id = m_last.groups()
                    last_stations[trip_id] = station_id
                    continue

                m_eff_next = eff_next_pattern.search(line)
                if m_eff_next:
                    trip_id, station_from, station_to = m_eff_next.groups()
                    eff_next_stations.setdefault(trip_id, {})[station_from] = station_to
                    continue

                m_allowed = allowed_next_pattern.search(line)
                if m_allowed:
                    trip_id, station_from, station_to = m_allowed.groups()
                    allowed_next_stations.setdefault(trip_id, {})[station_from] = station_to
                    continue

                m_skip = salta_pattern.search(line)
                if m_skip:
                    trip_id, station_from, station_to = m_skip.groups()
                    skipped_edges.setdefault(trip_id, set()).add((station_from, station_to))
                    continue

                m_new = new_station_pattern.search(line)
                if m_new:
                    old_station, new_station = m_new.groups()
                    new_station_map[old_station] = new_station
                    continue

                m_assign = assign_trip_pattern.search(line)
                if m_assign:
                    trip_id, train_id = m_assign.groups()
                    trip_train_assignments[trip_id] = train_id
                    continue

                m_tdep = trip_dep_pattern.search(line)
                if m_tdep:
                    trip_id, t_val = m_tdep.groups()
                    trip_dep_times[trip_id] = format_time_minutes(t_val)
                    continue

                m_tarr = trip_arr_pattern.search(line)
                if m_tarr:
                    trip_id, t_val = m_tarr.groups()
                    trip_arr_times[trip_id] = format_time_minutes(t_val)
                    continue

                m_sdep = station_dep_pattern.search(line)
                if m_sdep:
                    trip_id, station_id, t_val = m_sdep.groups()
                    station_dep_times.setdefault(trip_id, {})[station_id] = format_time_minutes(t_val)
                    continue

                m_sarr = station_arr_pattern.search(line)
                if m_sarr:
                    trip_id, station_id, t_val = m_sarr.groups()
                    station_arr_times.setdefault(trip_id, {})[station_id] = format_time_minutes(t_val)
                    continue

    trip_times = {}
    all_trips = set(eff_first_stations.keys()).union(trip_dep_times.keys()).union(trip_arr_times.keys())
    for trip_id in all_trips:
        dep = trip_dep_times.get(trip_id)
        if dep is None:
            first_st = eff_first_stations.get(trip_id)
            if first_st:
                dep = station_dep_times.get(trip_id, {}).get(first_st)

        arr = trip_arr_times.get(trip_id)
        if arr is None and trip_id in last_stations:
            last_st = last_stations[trip_id]
            arr = station_arr_times.get(trip_id, {}).get(last_st)

        if dep or arr:
            trip_times[trip_id] = (dep or "", arr or "")

    return (
        eff_first_stations,
        eff_next_stations,
        allowed_next_stations,
        skipped_edges,
        new_station_map,
        trip_train_assignments,
        trip_times
    )


def apply_station_replacements(route, new_station_map):
    return [new_station_map.get(station_id, station_id) for station_id in route]


def reconstruct_routes(eff_first_stations, eff_next_stations, new_station_map=None):
    """Ricostruisce i percorsi per ogni trip_id a partire unicamente da effective_first_station e effective_next_station."""
    routes = {}
    new_station_map = new_station_map or {}

    for trip_id, start_station in eff_first_stations.items():
        route = []
        curr = start_station
        visited = set()
        trip_edges = eff_next_stations.get(trip_id, {})
        while curr and curr not in visited:
            visited.add(curr)
            route.append(curr)
            curr = trip_edges.get(curr)

        if route:
            routes[trip_id] = apply_station_replacements(route, new_station_map)

    return routes


def group_by_trip_id(routes):
    """Raggruppa i trip_id che hanno lo stesso percorso (sequenza di stazioni)."""
    unique_paths = {}
    for trip_id, path in routes.items():
        if not path:
            continue
        path_key = tuple(path)
        if path_key not in unique_paths:
            unique_paths[path_key] = []
        unique_paths[path_key].append(trip_id)
    return unique_paths


def get_coherent_station_ids(stations_coords, new_station_map):
    """Restituisce l'insieme delle stazioni coerenti per la mappa, considerando le stazioni presenti in stations_coords e le sostituzioni in new_station_map."""
    old_station_ids = set(new_station_map.keys())
    coherent_station_ids = {sid for sid in stations_coords if sid not in old_station_ids}
    coherent_station_ids.update(
        sid for sid in new_station_map.values() if sid in stations_coords
    )
    return coherent_station_ids


def main():
    stations_coords, stations_names = load_stops(stops_csv_path)
    print(f"\tStazioni: {len(stations_coords)}")

    shapes_coord = load_shapes()

    args = sys.argv[1:]
    if any(arg in ("-o1", "--opt1", "-o") for arg in args):
        map_path = resolve_path(os.getenv("PATH_TO_MAP_OUTPUT_NUM"), "res/output/train_map_num.html")
        timetable_path = optimized_timetable_path
        mode_label = "Ottimizzazione #1 (-o1)"
    else:
        map_path = resolve_path(os.getenv("PATH_TO_MAP_OUTPUT_FER"), "res/output/train_map_fer.html")
        timetable_path = standard_timetable_path
        mode_label = "Standard"

    print(f"\tModalità: {mode_label}")

    timetable_sources = [timetable_path]

    (
        eff_first_stations,
        eff_next_stations,
        allowed_next_stations,
        skipped_edges,
        new_station_map,
        trip_train_assignments,
        trip_times
    ) = parse_asp_timetable(timetable_sources)

    print(
        f"Fatti ASP analizzati: effective_first_station={len(eff_first_stations)}, "
        f"effective_next_station={len(eff_next_stations)}, "
        f"allowed_next_station={len(allowed_next_stations)}, saltate={len(skipped_edges)}, "
        f"new_station={len(new_station_map)}, trip_times={len(trip_times)}"
    )

    routes = reconstruct_routes(
        eff_first_stations,
        eff_next_stations,
        new_station_map=new_station_map,
    )

    assigned_routes = {
        trip_id: route
        for trip_id, route in routes.items()
        if trip_id in trip_train_assignments and str(trip_train_assignments[trip_id]).strip()
    }

    coherent_station_ids = get_coherent_station_ids(stations_coords, new_station_map)
    print(f"\tStazioni considerando le sostituzioni: {len(coherent_station_ids)}")
    
    all_unique_paths = group_by_trip_id(routes)
    unique_paths = group_by_trip_id(assigned_routes)
    print(f"\tCorse totali: {len(assigned_routes)}")
    print(f"\tPercorsi unici: {len(unique_paths)}")

    display_route_names = {
        path_key: (path_key[0], path_key[-1])
        for path_key in unique_paths
    }
    
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

    fg_list = []
    for path_key, trips in unique_paths.items():
        start_id, end_id = display_route_names.get(path_key, (path_key[0], path_key[-1]))
        start_name = stations_names.get(start_id, start_id).replace("STAZIONE DI ", "")
        end_name = stations_names.get(end_id, end_id).replace("STAZIONE DI ", "")
        for trip_id in trips:
            s_time, e_time = ("", "")
            if trip_id in trip_times:
                s_time, e_time = trip_times[trip_id]
                name = f"({start_name} → {end_name}) [{s_time} → {e_time}] {trip_id}"
            else:
                name = f"({start_name} → {end_name}) {trip_id}"
            fg = folium.FeatureGroup(name=name, show=False)
            sort_key = (start_name, end_name, s_time, trip_id)
            fg_list.append((sort_key, trip_id, fg))

    fg_list.sort()

    feature_groups = {}  
    for _, trip_id, fg in fg_list:
        feature_groups[trip_id] = fg
        
    active_stations = set(coherent_station_ids)
    for path_key, trips in unique_paths.items():
        start_id = path_key[0]
        end_id = path_key[-1]

        for sid in path_key:
            if sid in stations_coords and sid in coherent_station_ids:
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

        for trip_id in trips:
            trip_skips = skipped_edges.get(trip_id, set())
            allowed_station_ids = [path_key[0]]
            for i in range(len(path_key) - 1):
                s_from = path_key[i]
                s_to = path_key[i + 1]
                if (s_from, s_to) not in trip_skips:
                    allowed_station_ids.append(s_to)

            valid_path_station_names = []
            for sid in allowed_station_ids:
                if sid not in stations_coords or sid not in coherent_station_ids:
                    continue
                valid_path_station_names.append(stations_names.get(sid, sid).replace("Stazione di ", ""))

            stops_str = " → ".join(valid_path_station_names)
            trip_dep_arr = trip_times.get(trip_id, ("", ""))
            time_str = f" [{trip_dep_arr[0]} → {trip_dep_arr[1]}]" if (trip_dep_arr[0] or trip_dep_arr[1]) else ""

            popup_html = f"""
            <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 13px; color: #333; line-height: 1.5; min-width: 220px; max-width: 300px;">
                <h4 style="margin: 0 0 5px; color: {color}; font-size: 14px; border-bottom: 2px solid #eee; padding-bottom: 3px; font-weight: 600;">
                    Corsa: {trip_id}
                </h4>
                <div style="font-size: 12px; color: #555; margin-bottom: 6px;">
                    <b>Tratta:</b> {start_name} &rarr; {end_name}{time_str}
                </div>
                <div style="margin-top: 8px;">
                    <b>Fermate effettive ({len(valid_path_station_names)}):</b><br>
                    <span style="color: #333; font-size: 11px; word-break: break-word;">{stops_str}</span>
                </div>
            </div>
            """

            fg = feature_groups[trip_id]
            folium.PolyLine(
                locations=coordinates,
                color=color,
                weight=4.5,
                opacity=0.8,
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"Corsa: {trip_id} — {start_name} → {end_name}{time_str}"
            ).add_to(fg)
        
    group_stazioni = folium.FeatureGroup(name="Stazioni", control=True)
    station_marker_js_names = {}
    station_group_name = group_stazioni.get_name()
    
    for sid in active_stations:
        if sid not in stations_coords or sid not in coherent_station_ids:
            continue
        coords = stations_coords[sid]
        name = stations_names.get(sid, sid)
        clean_name = name.replace("Stazione di ", "")
        
        serving_routes = []
        for path_key, trips in unique_paths.items():
            if sid in path_key:
                start_id, end_id = display_route_names.get(path_key, (path_key[0], path_key[-1]))
                s_name = stations_names.get(start_id, start_id).replace("Stazione di ", "")
                e_name = stations_names.get(end_id, end_id).replace("Stazione di ", "")
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
        
        marker = folium.CircleMarker(
            location=coords,
            radius=6,
            color="#37474F",
            weight=2,
            fill=True,
            fill_color="#FFFFFF",
            fill_opacity=1.0,
            popup=folium.Popup(station_popup_html, max_width=250),
            tooltip=clean_name
        )
        marker.add_to(group_stazioni)
        station_marker_js_names[sid] = marker.get_name()
        
    # for sid in active_starts:
    #     mappa.add_child(feature_groups[sid])
    # mappa.add_child(group_stazioni)

    for fg in feature_groups.values():
        mappa.add_child(fg)
    mappa.add_child(group_stazioni)
    
    folium.LayerControl(position='topright', collapsed=True).add_to(mappa)
    
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
            <span style="color: #ffb74d;">•</span> Corse Totali (Trip IDs): <b style="color: #fff;">{len(assigned_routes)}</b><br>
            <span style="color: #81c784;">•</span> Percorsi Fisici Unici: <b style="color: #fff;">{len(unique_paths)}</b><br>
            <span style="color: #64b5f6;">•</span> Stazioni Mostrate: <b style="color: #fff;">{len(active_stations)}</b>
        </div>
    </div>
    """
    mappa.get_root().html.add_child(folium.Element(stats_html))
    
    js_stations_data = []
    for sid in active_stations:
        if sid not in stations_coords or sid not in coherent_station_ids:
            continue
        coords = stations_coords[sid]
        name = stations_names.get(sid, sid)
        clean_name = name.replace("STAZIONE DI ", "").replace("Stazione di ", "")
        js_stations_data.append({
            "id": sid,
            "name": clean_name.upper(),
            "lat": coords[0],
            "lon": coords[1],
            "js_name": station_marker_js_names.get(sid, "")
        })
        
    trip_route_stations = {}
    trip_skipped_stations = {}
    for trip_id, route in routes.items():
        if not route:
            continue

        route_station_ids = [route[0]]
        skipped_station_ids = []
        trip_skips = skipped_edges.get(trip_id, set())

        for i in range(len(route) - 1):
            s_from = route[i]
            s_to = route[i + 1]
            if (s_from, s_to) in trip_skips:
                skipped_station_ids.append(s_to)
            else:
                route_station_ids.append(s_to)

        trip_route_stations[trip_id] = [sid for sid in route_station_ids if sid in coherent_station_ids]
        trip_skipped_stations[trip_id] = [sid for sid in skipped_station_ids if sid in coherent_station_ids]

    js_trips_data = []
    for sort_key, trip_id, fg in fg_list:
        start_name, end_name, s_time, _ = sort_key
        e_time = ""
        if trip_id in trip_times:
            _, e_time = trip_times[trip_id]
        js_trips_data.append({
            "id": trip_id,
            "start": start_name,
            "end": end_name,
            "start_time": s_time,
            "end_time": e_time,
            "js_name": fg.get_name(),
            "route_stations": trip_route_stations.get(trip_id, []),
            "skipped_stations": trip_skipped_stations.get(trip_id, [])
        })
        
    stations_json = json.dumps({
        "stations": js_stations_data,
        "trips": js_trips_data
    })
    map_name = mappa.get_name()

    # Barra di ricerca e bottoni
    buttons_html = """
    <style>
        .toggle-btn {
            padding: 8px 14px; border-radius: 8px; border: none; cursor: pointer;
            background-color: #757575; color: white; font-size: 13px; font-weight: 600;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            transition: background-color 0.2s ease, transform 0.1s ease;
        }
        .toggle-btn:hover {
            background-color: #616161;
        }
        .toggle-btn:active {
            transform: scale(0.97);
        }
        
        /* Stili della Barra di Ricerca */
        .search-container {
            position: relative;
            display: inline-block;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .search-input {
            padding: 8px 14px 8px 36px; 
            border-radius: 8px; 
            border: 1px solid rgba(0,0,0,0.15); 
            background-color: white; 
            color: #333; 
            font-size: 13px; 
            font-weight: 500;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15); 
            width: 250px; 
            outline: none;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .search-input:focus {
            border-color: #1E88E5;
            box-shadow: 0 2px 12px rgba(30, 136, 229, 0.35);
            width: 280px;
        }
        .search-icon {
            position: absolute; 
            left: 12px; 
            top: 50%; 
            transform: translateY(-50%); 
            width: 14px; 
            height: 14px; 
            fill: #757575;
            pointer-events: none;
            transition: fill 0.25s ease;
        }
        .search-input:focus + .search-icon {
            fill: #1E88E5;
        }
        .search-results {
            position: absolute; 
            top: calc(100% + 6px); 
            left: 0; 
            width: 100%;
            max-height: 260px; 
            overflow-y: auto; 
            background: white; 
            border-radius: 8px; 
            border: 1px solid rgba(0,0,0,0.1); 
            box-shadow: 0 4px 20px rgba(0,0,0,0.15); 
            display: none; 
            z-index: 10000;
        }
        .search-header {
            padding: 6px 14px 4px;
            font-size: 10px;
            font-weight: 700;
            color: #1E88E5;
            background-color: #f5f5f5;
            letter-spacing: 0.5px;
            border-bottom: 1px solid #eee;
            text-transform: uppercase;
        }
        .search-item {
            padding: 10px 14px;
            cursor: pointer;
            border-bottom: 1px solid #f5f5f5;
            display: flex;
            flex-direction: column;
            gap: 2px;
            transition: background-color 0.15s ease;
        }
        .search-item:last-child {
            border-bottom: none;
        }
        .search-item:hover, .search-item.selected {
            background-color: #f5f5f5;
        }
        .search-item-name {
            font-size: 13px;
            font-weight: 600;
            color: #212121;
        }
        .search-item-id {
            font-size: 10px;
            color: #757575;
            font-family: monospace;
        }
    </style>
    <div style="position: fixed;
                top: 10px; left: 50px;
                z-index: 9999;
                display: flex; gap: 10px; align-items: center;">
        
        <div class="search-container">
            <input type="text" id="station-search" class="search-input" placeholder="Cerca Stazione o Trip ID..." 
                   oninput="filterStations(this.value)"
                   onkeydown="handleSearchKey(event)">
            <svg class="search-icon" viewBox="0 0 24 24">
                <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
            </svg>
            <div id="search-results" class="search-results"></div>
        </div>

        <button class="toggle-btn" onclick="toggleAllLayers(true)">Tutte le corse</button>
        <button class="toggle-btn" onclick="toggleAllLayers(false)">Nessuna corsa</button>
    </div>
    <script>
        const stationsData = {stations_json};
        const stationGroupName = "{station_group_name}";
        let selectedIndex = -1;
        let filteredList = [];

        function hideAllStationMarkers() {
            const map = {map_name};
            const stationGroup = window[stationGroupName];
            if (stationGroup && map.hasLayer(stationGroup)) {
                map.removeLayer(stationGroup);
            }
        }

        function showAllStationMarkers() {
            const map = {map_name};
            stationsData.stations.forEach(station => {
                const markerName = station.js_name;
                const marker = window[markerName];
                if (!marker) return;
                setMarkerStyle(marker, false);
                if (!map.hasLayer(marker)) {
                    map.addLayer(marker);
                }
            });
        }

        function setMarkerStyle(marker, isSkipped) {
            if (!marker || !marker.setStyle) return;
            if (isSkipped) {
                marker.setStyle({
                    color: '#D32F2F',
                    weight: 2,
                    fillColor: '#FFCDD2',
                    fillOpacity: 1.0,
                    radius: 6
                });
            } else {
                marker.setStyle({
                    color: '#37474F',
                    weight: 2,
                    fillColor: '#FFFFFF',
                    fillOpacity: 1.0,
                    radius: 6
                });
            }
        }

        function showTripStationMarkers(routeStationIds, skippedStationIds) {
            const map = {map_name};
            const routeIdSet = new Set(routeStationIds || []);
            const skippedIdSet = new Set(skippedStationIds || []);
            stationsData.stations.forEach(station => {
                const markerName = station.js_name;
                const marker = window[markerName];
                if (!marker) return;

                const isRouteStation = routeIdSet.has(station.id);
                const isSkippedStation = skippedIdSet.has(station.id);

                if (isRouteStation || isSkippedStation) {
                    setMarkerStyle(marker, isSkippedStation);
                    if (!map.hasLayer(marker)) {
                        map.addLayer(marker);
                    }
                } else if (map.hasLayer(marker)) {
                    map.removeLayer(marker);
                }
            });
        }

        function getActiveTripLayers() {
            const map = {map_name};
            return stationsData.trips.filter(trip => {
                const layer = window[trip.js_name];
                return !!(layer && map.hasLayer(layer));
            });
        }

        function syncStationsFromActiveTrips() {
            const activeTrips = getActiveTripLayers();
            const map = {map_name};
            
            if (activeTrips.length === 0) {
                showAllStationMarkers();
                return;
            }

            const routeIdSet = new Set();
            const skippedIdSet = new Set();
            activeTrips.forEach(trip => {
                (trip.route_stations || []).forEach(stationId => routeIdSet.add(stationId));
                (trip.skipped_stations || []).forEach(stationId => skippedIdSet.add(stationId));
            });

            stationsData.stations.forEach(station => {
                const markerName = station.js_name;
                const marker = window[markerName];
                if (!marker) return;

                const isRouteStation = routeIdSet.has(station.id);
                const isSkippedStation = skippedIdSet.has(station.id);
                if (isRouteStation || isSkippedStation) {
                    setMarkerStyle(marker, isSkippedStation);
                    if (!map.hasLayer(marker)) {
                        map.addLayer(marker);
                    }
                } else if (map.hasLayer(marker)) {
                    map.removeLayer(marker);
                }
            });
        }

        function filterStations(query) {
            const resultsDiv = document.getElementById('search-results');
            resultsDiv.innerHTML = '';
            selectedIndex = -1;
            
            const cleanQuery = query.trim().toUpperCase();
            if (!cleanQuery) {
                resultsDiv.style.display = 'none';
                filteredList = [];
                return;
            }

            // Filtra stazioni
            const matchedStations = stationsData.stations.filter(station => 
                station.name.includes(cleanQuery) || station.id.includes(cleanQuery)
            ).slice(0, 5);

            // Filtra corse
            const matchedTrips = stationsData.trips.filter(trip => 
                trip.id.toUpperCase().includes(cleanQuery) ||
                trip.start.toUpperCase().includes(cleanQuery) || 
                trip.end.toUpperCase().includes(cleanQuery) ||
                (trip.start + " " + trip.end).toUpperCase().includes(cleanQuery)
            ).slice(0, 5);

            filteredList = [];

            if (matchedStations.length > 0) {
                const header = document.createElement('div');
                header.className = 'search-header';
                header.innerText = 'Stazioni';
                resultsDiv.appendChild(header);

                matchedStations.forEach(station => {
                    const idx = filteredList.length;
                    filteredList.push({ type: 'station', data: station });

                    const item = document.createElement('div');
                    item.className = 'search-item';
                    item.id = 'search-item-' + idx;
                    item.onclick = () => selectStation(station);
                    
                    const displayName = highlightMatch(station.name, cleanQuery);
                    const displayId = highlightMatch(station.id, cleanQuery);

                    item.innerHTML = `
                        <span class="search-item-name">${displayName}</span>
                        <span class="search-item-id">ID: ${displayId}</span>
                    `;
                    resultsDiv.appendChild(item);
                });
            }

            if (matchedTrips.length > 0) {
                const header = document.createElement('div');
                header.className = 'search-header';
                header.innerText = 'Corse (Trip ID)';
                resultsDiv.appendChild(header);

                matchedTrips.forEach(trip => {
                    const idx = filteredList.length;
                    filteredList.push({ type: 'trip', data: trip });

                    const item = document.createElement('div');
                    item.className = 'search-item';
                    item.id = 'search-item-' + idx;
                    item.onclick = () => selectTrip(trip);
                    
                    const displayId = highlightMatch(trip.id, cleanQuery);
                    const displayStart = highlightMatch(trip.start, cleanQuery);
                    const displayEnd = highlightMatch(trip.end, cleanQuery);
                    const timeStr = trip.start_time ? ` [${trip.start_time} → ${trip.end_time}]` : '';

                    item.innerHTML = `
                        <span class="search-item-name">Corsa ${displayId}${timeStr}</span>
                        <span class="search-item-id">${displayStart} &rarr; ${displayEnd}</span>
                    `;
                    resultsDiv.appendChild(item);
                });
            }

            if (filteredList.length === 0) {
                resultsDiv.style.display = 'none';
                return;
            }

            resultsDiv.style.display = 'block';
        }

        function highlightMatch(text, query) {
            const idx = text.indexOf(query);
            if (idx === -1) return text;
            return text.substring(0, idx) + '<mark style="background-color: #ffe082; padding: 0 2px; border-radius: 2px;">' + text.substring(idx, idx + query.length) + '</mark>' + text.substring(idx + query.length);
        }

        function handleSearchKey(event) {
            const resultsDiv = document.getElementById('search-results');
            if (resultsDiv.style.display === 'none' || filteredList.length === 0) return;

            if (event.key === 'ArrowDown') {
                event.preventDefault();
                changeSelection(1);
            } else if (event.key === 'ArrowUp') {
                event.preventDefault();
                changeSelection(-1);
            } else if (event.key === 'Enter') {
                event.preventDefault();
                if (selectedIndex >= 0 && selectedIndex < filteredList.length) {
                    const sel = filteredList[selectedIndex];
                    if (sel.type === 'station') selectStation(sel.data);
                    else if (sel.type === 'trip') selectTrip(sel.data);
                } else if (filteredList.length > 0) {
                    const sel = filteredList[0];
                    if (sel.type === 'station') selectStation(sel.data);
                    else if (sel.type === 'trip') selectTrip(sel.data);
                }
            } else if (event.key === 'Escape') {
                resultsDiv.style.display = 'none';
            }
        }

        function changeSelection(direction) {
            if (selectedIndex >= 0) {
                const prevItem = document.getElementById('search-item-' + selectedIndex);
                if (prevItem) prevItem.classList.remove('selected');
            }

            selectedIndex += direction;
            if (selectedIndex < 0) selectedIndex = filteredList.length - 1;
            if (selectedIndex >= filteredList.length) selectedIndex = 0;

            const currItem = document.getElementById('search-item-' + selectedIndex);
            if (currItem) {
                currItem.classList.add('selected');
                currItem.scrollIntoView({ block: 'nearest' });
            }
        }

        function selectStation(station) {
            document.getElementById('station-search').value = station.name;
            document.getElementById('search-results').style.display = 'none';
            
            const map = {map_name};
            map.setView([station.lat, station.lon], 10, { animate: true, duration: 1.0 });

            const markerName = station.js_name;
            if (window[markerName]) {
                window[markerName].openPopup();
            }
        }

        function selectTrip(trip) {
            document.getElementById('station-search').value = `Corsa ${trip.id}`;
            document.getElementById('search-results').style.display = 'none';
            
            const map = {map_name};
            
            // Spegni tutte le altre corse
            stationsData.trips.forEach(t => {
                const fgName = t.js_name;
                if (window[fgName] && map.hasLayer(window[fgName])) {
                    map.removeLayer(window[fgName]);
                }
            });

            const relatedTrips = [trip];

            // Mostra solo le stazioni della corsa selezionata e quelle saltate in rosso
            const selectedStations = trip.route_stations || [];
            const skippedStations = trip.skipped_stations || [];
            hideAllStationMarkers();
            showTripStationMarkers(selectedStations, skippedStations);
            syncStationsFromActiveTrips();

            // Nascondi tutte le altre tratte e lascia solo quella selezionata
            const allTripLayerNames = stationsData.trips.map(t => t.js_name);
            allTripLayerNames.forEach(layerName => {
                const layer = window[layerName];
                if (layer && map.hasLayer(layer) && layerName !== trip.js_name) {
                    map.removeLayer(layer);
                }
            });

            // corsa selezionata
            relatedTrips.forEach(relatedTrip => {
                const selectedFg = window[relatedTrip.js_name];
                if (selectedFg && !map.hasLayer(selectedFg)) {
                    map.addLayer(selectedFg);
                }
            });

            if (relatedTrips.length > 0) {
                const bounds = relatedTrips
                    .map(rt => window[rt.js_name])
                    .filter(Boolean)
                    .map(layer => layer.getBounds ? layer.getBounds() : null)
                    .filter(Boolean);
                if (bounds.length > 0) {
                    const combinedBounds = bounds.reduce((acc, b) => acc.extend(b), bounds[0].clone());
                    map.fitBounds(combinedBounds, { padding: [80, 80], maxZoom: 9, animate: true, duration: 1.0 });
                }
            }

            // popup della corsa selezionata
            const selectedFg = window[trip.js_name];
            if (selectedFg) {
                setTimeout(() => {
                    selectedFg.eachLayer(layer => {
                        if (layer.openPopup) {
                            layer.openPopup();
                        }
                    });
                }, 350);
            }
        }

        document.addEventListener('click', function(e) {
            const container = document.querySelector('.search-container');
            if (container && !container.contains(e.target)) {
                document.getElementById('search-results').style.display = 'none';
            }
        });

        document.addEventListener('change', function(e) {
            const checkbox = e.target;
            if (!checkbox.matches('.leaflet-control-layers-overlays input[type="checkbox"]')) return;

            const label = checkbox.closest('label');
            if (!label) return;
            const labelText = label.innerText.trim();
            if (!labelText || labelText.startsWith('Stazioni')) return;

            setTimeout(syncStationsFromActiveTrips, 0);
        });

        function toggleAllLayers(show) {
            document.querySelectorAll('.leaflet-control-layers-overlays input[type=checkbox]').forEach(function(cb) {
                var label = cb.closest('label');
                if (cb.checked !== show && !label.innerText.trim().startsWith('Stazioni')){
                    cb.click();
                } 
            });
        }
    </script>
    """.replace("{stations_json}", stations_json).replace("{map_name}", map_name).replace("{station_group_name}", station_group_name)
    mappa.get_root().html.add_child(folium.Element(buttons_html))
 
    mappa.save(map_path)
    print(f"Mappa generata e salvata in: {map_path}")


if __name__ == "__main__":
    main()