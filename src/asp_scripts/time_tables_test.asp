% RUN WITH:
% python3 -m clingo res/asp_encoding/links.asp res/asp_encoding/stations.asp res/asp_encoding/trip_id.asp src/asp_scripts/time_tables.asp | grep "station" | tr ' ' '\n' | sed 's/$./' > res/output/prova.asp

% RUN WITH ENCODED TIME TABLES
% python3 -m clingo res/asp_encoding/links.asp res/asp_encoding/stations.asp res/asp_encoding/trip_id.asp src/asp_scripts/time_tables.asp res/output/encoded_time_table.asp | grep "station" | tr ' ' '\n' | sed 's/$/./' > res/output/prova.asp



%1 { first_station(Trip_id, Station_id) : station(Station_id, _, _) } 1 :- trip_id(Trip_id).

%1 { next_station(Trip_id, Station_1_id, Station_2_id) : connected(Station_1_id, Station_2_id) } 1 :- first_station(Trip_id, Station_1_id).

0 { next_station(Trip_id, Station_1_id, Station_2_id) : connected(Station_1_id, Station_2_id) } 1 :- next_station(Trip_id, _, Station_1_id).



% ── Vincoli temporali ────────────────────────────────────────────────────────

% 1. La partenza da S1 deve precedere l'arrivo a S2.
:- next_station(Trip_id, Station_1_id, Station_2_id),
   departure_time(Trip_id, Station_1_id, Dep),
   arrival_time(Trip_id, Station_2_id, Arr),
   Arr <= Dep.

% 2. Non si può partire da una stazione prima di essere arrivati.
:- arrival_time(Trip_id, Station_id, Arr),
   departure_time(Trip_id, Station_id, Dep),
   Dep < Arr.

% 3. Il dwell time deve rispettare il range definito in rests.asp.
:- arrival_time(Trip_id, Station_id, Arr),
   departure_time(Trip_id, Station_id, Dep),
   rest(Station_id, Min_rest, _),
   Dep - Arr < Min_rest.

:- arrival_time(Trip_id, Station_id, Arr),
   departure_time(Trip_id, Station_id, Dep),
   rest(Station_id, _, Max_rest),
   Max_rest > 0,
   Dep - Arr > Max_rest.



#show first_station/2.
#show next_station/3.
