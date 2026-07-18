%% FIRST:
% python3 src/scripts/generate_trip_id.py
% python3 src/scripts/generate_arr_dep.py 
% python3 src/scripts/generate_stoptimes_input.py 
% python3 -m clingo res/asp_encoding/stops.asp src/asp_scripts/encode_time_table.asp | grep "station" | tr ' ' '\n' | sed 's/$/./' > res/output/encoded_time_table.asp
% python3 src/scripts/generate_calendar_dates_encoding.py

%% RUN WITH: (Windows)
% python -m clingo res/asp_encoding/trip_id.asp res/output/arrival_departure.asp res/output/encoded_time_table.asp res/asp_encoding/calendar_dates.asp src/asp_scripts/train_types.asp res/output/fatti_pendolarismo.asp  src/asp_scripts/train_assignment.asp --stats=2 --quiet=1 |
% >>   Select-String "assign_trip_train" |
% >>   ForEach-Object { $_.Line -split ' ' } |
% >>   ForEach-Object { "$_." } |
% >>   Set-Content  res/output/prova_ottimizzazione.asp
% (NB: this is the command for Windows Powershell environment)

% RUN WITH: (Linux)
% python3 -m clingo res/asp_encoding/trip_id.asp res/output/arrival_departure.asp res/output/encoded_time_table.asp res/asp_encoding/calendar_dates.asp res/output/fatti_pendolarismo.asp src/asp_scripts/train_types.asp res/asp_encoding/previous_stations src/asp_scripts/optimizations/number_of_trains.asp --stats=2 --quiet=1 --time-limit=300 | grep "assign_trip_train" | tr ' ' '\n' | sed 's/$/./' > res/output/prova_ottimizzazione_number.asp


short_calendar_dates(Trip_id, Date) :- 
    calendar_dates(Trip_id, Date),
    Date >= 20241215,
    Date < 20241223.


% short_calendar_dates(Trip_id, Date) :- 
%     calendar_dates(Trip_id, Date),
%     Date >= 20250601,
%     Date < 20250605.


1 { assign_trip_train(Trip_id, Date, Train_id) : train(Train_id, _, _) } 1 :- short_calendar_dates(Trip_id, Date).

%% 1 { assign_trip_train("1-4751-149-0083", 20250601, Train_id) : train(Train_id, _, _) } 1 :- short_calendar_dates("1-4751-149-0083", 20250601).


last_station(Trip_id, Station_id) :-
    trip_id(Trip_id),
    next_station(Trip_id, _, Station_id),
    not next_station(Trip_id, Station_id, _).

trip_departure_time(Trip_id, Time) :-
    trip_id(Trip_id),
    first_station(Trip_id, Station_id),
    departure_time(Trip_id, Station_id, Time).

trip_arrival_time(Trip_id, Time) :-
    trip_id(Trip_id),
    last_station(Trip_id, Station_id),
    arrival_time(Trip_id, Station_id, Time).


sovrapposizione_oraria(T1, T2) :-
    T1 != T2,
    trip_departure_time(T1, Dep1), trip_arrival_time(T1, Arr1),
    trip_departure_time(T2, Dep2), trip_arrival_time(T2, Arr2),
    Arr1 > Dep2,
    Arr2 > Dep1.


:- assign_trip_train(T1, Date, Train),
    assign_trip_train(T2, Date, Train),
    sovrapposizione_oraria(T1, T2).


% allowed_trip(T1, T2) :- 
%     short_calendar_dates(T1, Date_1),
%     short_calendar_dates(T2, Date_2),
%     T1 != T2,
%     Date_1 != Date_2.


allowed_trip(T1, T2) :- 
    short_calendar_dates(T1, Date),
    short_calendar_dates(T2, Date),
    T1 != T2,
    last_station(T1, Station), 
    first_station(T2, Station),
    trip_departure_time(T2, Dep),
    trip_arrival_time(T1, Arr),
    Dep >= Arr.                  


:~ assign_trip_train(T1, Date, Train),
    assign_trip_train(T2, Date, Train),
    not allowed_trip(T1, T2),
    not allowed_trip(T2, T1).
    [1@2, T1]



new_station("830012810", "830012891"). % CAGLIARI S.GILLA -> CAGLIARI
new_station("830012819", "830012890"). % Elmas Aeroporto -> CAGLIARI ELMAS
new_station("830012808", "830012889"). % Assemini S. Lucia -> ASSEMINI
new_station("830012809", "830012889"). % Assemini Carmine -> ASSEMINI
new_station("830012895", "830012852"). % RUDALZA (GOLFO ARANCI) -> GOLFO ARANCI
new_station("830012854", "830012852"). % MARINELLA (GOLFO ARANCI) -> GOLFO ARANCI
new_station("830012902", "830012855"). % Olbia Terranova -> OLBIA
new_station("830012896", "830012857"). % SU CANALE (MONTI) -> MONTI TELTI
new_station("830012818", "830012802"). % PORTO TORRES MARITTIMA -> PORTO TORRES

pendolarismo(S1, S2, Sum, 1) :- people(S1, _, S2, _, _, "prima delle 7,15"), Sum = #sum{C : people(S1, _, S2, _, C, "prima delle 7,15")}, S1 != S2.
pendolarismo(S1, S2, Sum, 2) :- people(S1, _, S2, _, _, "dalle 7,15 alle 8,14"), Sum = #sum{C : people(S1, _, S2, _, C, "dalle 7,15 alle 8,14")}, S1 != S2.
pendolarismo(S1, S2, Sum, 3) :- people(S1, _, S2, _, _, "dalle 8,15 alle 9,14"), Sum = #sum{C : people(S1, _, S2, _, C, "dalle 8,15 alle 9,14")}, S1 != S2.
pendolarismo(S1, S2, Sum, 4) :- people(S1, _, S2, _, _, "dopo le 9,14"), Sum = #sum{C : people(S1, _, S2, _, C, "dopo le 9,14")}, S1 != S2.



next_station_time(Trip, Station_1, Station_2, 1) :- 
    next_station(Trip, Station_1, Station_2),
    departure_time(Trip, Station_1, Time),
    Time < 435.

next_station_time(Trip, Station_1, Station_2, 2) :- 
    next_station(Trip, Station_1, Station_2),
    departure_time(Trip, Station_1, Time),
    Time >= 435,
    Time < 495.

next_station_time(Trip, Station_1, Station_2, 3) :- 
    next_station(Trip, Station_1, Station_2),
    departure_time(Trip, Station_1, Time),
    Time >= 495,
    Time < 554.

next_station_time(Trip, Station_1, Station_2, 4) :- 
    next_station(Trip, Station_1, Station_2),
    departure_time(Trip, Station_1, Time),
    Time >= 554.


max_capacity(Station_1, Station_2, Cap, Fascia) :-
    pendolarismo(Station_1, Station_2, _, Fascia),
    Cap = #sum{C, Trip : next_station_time(Trip, Station_1, Station_2, Fascia), assign_trip_train(Trip, _, Train), train(Train, _, C)},
    Cap > 0.


:- pendolarismo(S1, S2, Pass, Fascia),
    max_capacity(S1, S2, Cap, Fascia),
    Pass > Cap.


ha_pendolarismo(S2, F, T) :- pendolarismo(S1, S2, _, F), previous_station(T, S1, S2), assign_trip_train(T, _, _), next_station_time(T, S1, _, F), 
    not new_station(S1, _),
    not new_station(S2, _).

ha_pendolarismo(S2, F, T) :- pendolarismo(New_S1, S2, _, F), previous_station(T, New_S1, S2), assign_trip_train(T, _, _), next_station_time(T, New_S1, _, F), 
    new_station(S1, New_S1).

ha_pendolarismo(New_S2, F, T) :- pendolarismo(S1, New_S2, _, F), previous_station(T, S1, New_S2), assign_trip_train(T, _, _), next_station_time(T, S1, _, F), 
    new_station(S2, New_S2).


salta(Trip, S1, S2) :-
    next_station_time(Trip, S1, S2, Fascia),
    not ha_pendolarismo(S2, Fascia, Trip),
    assign_trip_train(Trip, _, _),
    not last_station(Trip, S2).



allowed_next_station(Trip, S1, S2) :-
    assign_trip_train(Trip, _, _),
    next_station(Trip, S1, S2),
    not salta(Trip, S1, S2).


tot_fermate_per_trip(Tot, Trip) :- 
    Tot = #count{S1, S2 : next_station(Trip, S1, S2), not salta(Trip, S1, S2)}, 
    assign_trip_train(Trip, _, _).


tot_fermate(Tot) :- Tot = #sum{F, Trip : tot_fermate_per_trip(F, Trip)}.



tempo_impegato(T, S1, S2, Tempo) :-
    assign_trip_train(T, _, _),
    next_station(T, S1, S2),
    departure_time(T, S1, Start),
    arrival_time(T, S2, End),
    Tempo = End - Start.


tempo_rest(T, S2, Tempo) :-
    assign_trip_train(T, _, _),
    not salta(T, S1, S2),
    next_station(T, S1, S2),
    not first_station(T, S2),
    not last_station(T, S2),
    arrival_time(T, S2, Start),
    departure_time(T, S2, End),
    Tempo = End - Start.


tempo_per_trip(T, Tempo) :-
    assign_trip_train(T, _, _),
    Tempo_percorso = #sum{Time, S1, S2 : tempo_impegato(T, S1, S2, Time)},
    Tempo_rest = #sum{Time, S : tempo_rest(T, S, Time)},
    Tempo = Tempo_percorso + Tempo_rest.


% tempo_totale(Tot) :- Tot = #sum{Tempo, T : tempo_per_trip(T, Tempo)}.



used_train(T) :- assign_trip_train(_, _, T).

:~ used_train(T). [1@1, T]






    



% vedere il tempo risparmiato
% minimizzare il numero di treni


%#show max_capacity/4.
#show used_train/1.
#show tempo_per_trip/2.
#show tempo_rest/3.
#show pendolarismo/4.
#show tot_fermate_per_trip/2.
#show tot_fermate/1.
#show salta/3.
#show next_station_time/4.
#show allowed_next_station/3.
#show ha_pendolarismo/3.
#show tempo_impegato/4.
#show assign_trip_train/3.
#show allowed_trip/2.