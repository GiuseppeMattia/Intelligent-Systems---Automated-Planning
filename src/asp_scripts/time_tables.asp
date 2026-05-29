% RUN WITH:
% python3 -m clingo res/asp_encoding/links.asp res/asp_encoding/stations.asp res/asp_encoding/trip_id.asp src/asp_scripts/time_tables.asp | grep "station" | tr ' ' '\n' | sed 's/$/./' > res/output/prova.asp

% RUN WITH ENCODED TIME TABLES
% python3 -m clingo res/asp_encoding/links.asp res/asp_encoding/stations.asp res/asp_encoding/trip_id.asp src/asp_scripts/time_tables.asp res/output/encoded_time_table.asp | grep "station" | tr ' ' '\n' | sed 's/$/./' > res/output/prova.asp




1 { first_station(Trip_id, Station_id) : station(Station_id, _, _) } 1 :- trip_id(Trip_id).

1 { next_station(Trip_id, Station_1_id, Station_2_id) : connected(Station_1_id, Station_2_id) } 1 :- first_station(Trip_id, Station_1_id).

0 { next_station(Trip_id, Station_1_id, Station_2_id) : connected(Station_1_id, Station_2_id) } 1 :- next_station(Trip_id, _, Station_1_id).





#show first_station/2.
#show next_station/3.