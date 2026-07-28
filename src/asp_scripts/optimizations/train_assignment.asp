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
% python3 -m clingo res/asp_encoding/trip_id.asp res/output/arrival_departure.asp res/output/encoded_time_table.asp res/asp_encoding/calendar_dates.asp res/output/fatti_pendolarismo.asp src/asp_scripts/train_types.asp res/asp_encoding/previous_stations.asp src/asp_scripts/train_assignment.asp --stats=2 --quiet=1 --time-limit=300 | grep "assign_trip_train" | tr ' ' '\n' | sed 's/$/./' > res/output/prova_ottimizzazione.asp

%selection on a specific week to handle dimension of search space
short_calendar_dates(Trip_id, Date) :- 
    calendar_dates(Trip_id, Date),
    Date >= 20241215,
    Date < 20241223.


%guess
1 { assign_trip_train(Trip_id, Date, Train_id) : train(Train_id, _, _) } 1 :- short_calendar_dates(Trip_id, Date).

%Here we map the inconsistent stations to the new one, handling all the logic we need later

new_station("830012810", "830012891"). % CAGLIARI S.GILLA -> CAGLIARI
new_station("830012819", "830012890"). % Elmas Aeroporto -> CAGLIARI ELMAS
new_station("830012808", "830012889"). % Assemini S. Lucia -> ASSEMINI
new_station("830012809", "830012889"). % Assemini Carmine -> ASSEMINI
new_station("830012895", "830012852"). % RUDALZA (GOLFO ARANCI) -> GOLFO ARANCI
new_station("830012854", "830012852"). % MARINELLA (GOLFO ARANCI) -> GOLFO ARANCI
new_station("830012902", "830012855"). % Olbia Terranova -> OLBIA
new_station("830012896", "830012857"). % SU CANALE (MONTI) -> MONTI TELTI
new_station("830012818", "830012802"). % PORTO TORRES MARITTIMA -> PORTO TORRES

abolita(S) :- new_station(S, _).

collegamento(Trip, S1, S2) :- next_station(Trip, S1, S2).
collegamento(Trip, S1, S3) :- 
    collegamento(Trip, S1, S2), 
    abolita(S2), 
    next_station(Trip, S2, S3).

effective_next_station(Trip, S1, S2) :- 
    collegamento(Trip, S1, S2), 
    not abolita(S1), 
    not abolita(S2).

effective_first_station(Trip, S) :- 
    first_station(Trip, S), 
    not abolita(S).
effective_first_station(Trip, S2) :- 
    first_station(Trip, S1), 
    abolita(S1), 
    collegamento(Trip, S1, S2), 
    not abolita(S2).

actual_station(Old, New) :- new_station(Old, New).
actual_station(S, S) :- pendolarismo(S, _, _, _), not abolita(S).
actual_station(S, S) :- pendolarismo(_, S, _, _), not abolita(S).

effective_pendolarismo(Real_S1, Real_S2, Pass, Fascia) :-
    pendolarismo(S1, S2, Pass, Fascia),
    actual_station(S1, Real_S1),
    actual_station(S2, Real_S2).

%For every trip, we compute the last station
last_station(Trip_id, Station_id) :-
    trip_id(Trip_id),
    effective_next_station(Trip_id, _, Station_id),
    not effective_next_station(Trip_id, Station_id, _).

%Auxiliar predicates to understand the departure and arrival time of each trip 
trip_departure_time(Trip_id, Time) :-
    trip_id(Trip_id),
    effective_first_station(Trip_id, Station_id),
    departure_time(Trip_id, Station_id, Time).

trip_arrival_time(Trip_id, Time) :-
    trip_id(Trip_id),
    last_station(Trip_id, Station_id),
    arrival_time(Trip_id, Station_id, Time).

%If two trips are superimposed in time, that they cannot be assigned to the same train
sovrapposizione_oraria(T1, T2) :-
    T1 != T2,
    trip_departure_time(T1, Dep1), trip_arrival_time(T1, Arr1),
    trip_departure_time(T2, Dep2), trip_arrival_time(T2, Arr2),
    Arr1 > Dep2,
    Arr2 > Dep1.

:- assign_trip_train(T1, Date, Train),
    assign_trip_train(T2, Date, Train),
    sovrapposizione_oraria(T1, T2).

%allowed_trip
allowed_trip(T1, T2) :- 
    short_calendar_dates(T1, Date),
    short_calendar_dates(T2, Date),
    T1 != T2,
    last_station(T1, Station), 
    effective_first_station(T2, Station),
    trip_departure_time(T2, Dep),
    trip_arrival_time(T1, Arr),
    Dep >= Arr.                  


:~ assign_trip_train(T1, Date, Train),
    assign_trip_train(T2, Date, Train),
    not allowed_trip(T1, T2),
    not allowed_trip(T2, T1).
    [1@1, T1, T2]


%projection and sum on commuting matrix
pendolarismo(S1, S2, Sum, 1) :- people(S1, _, S2, _, _, "prima delle 7,15"), Sum = #sum{C : people(S1, _, S2, _, C, "prima delle 7,15")}, S1 != S2.
pendolarismo(S1, S2, Sum, 2) :- people(S1, _, S2, _, _, "dalle 7,15 alle 8,14"), Sum = #sum{C : people(S1, _, S2, _, C, "dalle 7,15 alle 8,14")}, S1 != S2.
pendolarismo(S1, S2, Sum, 3) :- people(S1, _, S2, _, _, "dalle 8,15 alle 9,14"), Sum = #sum{C : people(S1, _, S2, _, C, "dalle 8,15 alle 9,14")}, S1 != S2.
pendolarismo(S1, S2, Sum, 4) :- people(S1, _, S2, _, _, "dopo le 9,14"), Sum = #sum{C : people(S1, _, S2, _, C, "dopo le 9,14")}, S1 != S2.

%Assigning each next_station/2 predicate to the currect time slot
next_station_time(Trip, Station_1, Station_2, 1) :- 
    effective_next_station(Trip, Station_1, Station_2),
    departure_time(Trip, Station_1, Time),
    Time < 435.

next_station_time(Trip, Station_1, Station_2, 2) :- 
    effective_next_station(Trip, Station_1, Station_2),
    departure_time(Trip, Station_1, Time),
    Time >= 435,
    Time < 495.

next_station_time(Trip, Station_1, Station_2, 3) :- 
    effective_next_station(Trip, Station_1, Station_2),
    departure_time(Trip, Station_1, Time),
    Time >= 495,
    Time < 554.

next_station_time(Trip, Station_1, Station_2, 4) :- 
    effective_next_station(Trip, Station_1, Station_2),
    departure_time(Trip, Station_1, Time),
    Time >= 554.

%If a train should exceed its capacity to satisfy the commuting matrix needs, the assignment CANNOT BE DONE.
max_capacity(Station_1, Station_2, Cap, Fascia) :-
    effective_pendolarismo(Station_1, Station_2, _, Fascia),
    Cap = #sum{C, Trip : next_station_time(Trip, Station_1, Station_2, Fascia), assign_trip_train(Trip, _, Train), train(Train, _, C)},
    Cap > 0.

:- effective_pendolarismo(S1, S2, Pass, Fascia),
    max_capacity(S1, S2, Cap, Fascia),
    Pass > Cap.

%Select all the stations that actually are involved in commuting matrix
ha_pendolarismo(S2, Fascia, Trip) :- 
    effective_pendolarismo(S1, S2, _, Fascia), 
    assign_trip_train(Trip, _, _), 
    effective_next_station(Trip, S1, S2), 
    next_station_time(Trip, S1, _, Fascia).

%The "salta" predicate (skip) models all the stations in a Trip that aren't the endpoint and aren't involved in commuting matrix
salta(Trip, S1, S2) :-
    next_station_time(Trip, S1, S2, Fascia),
    not ha_pendolarismo(S2, Fascia, Trip),
    assign_trip_train(Trip, _, _),
    not last_station(Trip, S2).

%A next_station is allowed if it's not skippable
allowed_next_station(Trip, S1, S2) :-
    assign_trip_train(Trip, _, _),
    effective_next_station(Trip, S1, S2),
    not salta(Trip, S1, S2).

%This section computes the time gained by skipping the station where no people needs the train according to commuting matrix
tot_fermate_per_trip(Tot, Trip) :- 
    Tot = #count{S1, S2 : effective_next_station(Trip, S1, S2), not salta(Trip, S1, S2)}, 
    assign_trip_train(Trip, _, _).


tot_fermate(Tot) :- Tot = #sum{F, Trip : tot_fermate_per_trip(F, Trip)}.

tempo_impiegato(T, S1, S2, Tempo) :-
    assign_trip_train(T, _, _),
    effective_next_station(T, S1, S2),
    departure_time(T, S1, Start),
    arrival_time(T, S2, End),
    Tempo = End - Start.


tempo_rest(T, S2, Tempo) :-
    assign_trip_train(T, _, _),
    not salta(T, S1, S2),
    effective_next_station(T, S1, S2),
    not effective_first_station(T, S2),
    not last_station(T, S2),
    arrival_time(T, S2, Start),
    departure_time(T, S2, End),
    Tempo = End - Start.

tempo_per_trip(T, Tempo) :-
    assign_trip_train(T, _, _),
    Tempo_percorso = #sum{Time, S1, S2 : tempo_impiegato(T, S1, S2, Time)},
    Tempo_rest = #sum{Time, S : tempo_rest(T, S, Time)},
    Tempo = Tempo_percorso + Tempo_rest.

#show assign_trip_train/3.
#show effective_first_station/2.
#show last_station/2.
#show allowed_next_station/3.
#show effective_next_station/3.
#show salta/3.
#show new_station/2.
#show trip_departure_time/2.
#show trip_arrival_time/2.
#show departure_time/3.
#show arrival_time/3.