%% FIRST:
% python3 src/scripts/generate_trip_id.py
% python3 src/scripts/generate_arr_dep.py 
% python3 src/scripts/generate_stoptimes_input.py 
% python3 -m clingo res/asp_encoding/stops.asp src/asp_scripts/encode_time_table.asp | grep "station" | tr ' ' '\n' | sed 's/$/./' > res/output/encoded_time_table.asp
% python3 src/scripts/generate_calendar_dates_encoding.py

%% RUN WITH:
%% python3 -m clingo res/asp_encoding/trip_id.asp res/output/arrival_departure.asp res/output/encoded_time_table.asp res/asp_encoding/calendar_dates.asp src/asp_scripts/train_assignment.asp --stats=2 | grep "assign_trip_train" | tr ' ' '\n' | sed 's/$/./' > res/output/prova_ottimizzazione.asp

train(1,  "Blues", 300).
train(2,  "Blues", 300).
train(3,  "Blues", 300).
train(4,  "Blues", 300).
train(5,  "Blues", 300).
train(6,  "Blues", 300).
train(7,  "Blues", 300).
train(8,  "Blues", 300).
train(9,  "Blues", 300).
train(10, "Blues", 300).
train(11, "Blues", 300).
train(12, "Blues", 300).

train(13, "Swing", 326).
train(14, "Swing", 326).
train(15, "Swing", 326).
train(16, "Swing", 326).
train(17, "Swing", 326).
train(18, "Swing", 326).
train(19, "Swing", 326).
train(20, "Swing", 326).
train(21, "Swing", 326).
train(22, "Swing", 326).

train(23, "Minuetto", 345).
train(24, "Minuetto", 345).
train(25, "Minuetto", 345).
train(26, "Minuetto", 345).
train(27, "Minuetto", 345).
train(28, "Minuetto", 345).
train(29, "Minuetto", 345).
train(30, "Minuetto", 345).
train(31, "Minuetto", 345).
train(32, "Minuetto", 345).

train(33, "CAF", 204).
train(34, "CAF", 204).
train(35, "CAF", 204).
train(36, "CAF", 204).
train(37, "CAF", 204).
train(38, "CAF", 204).
train(39, "CAF", 204).
train(40, "CAF", 204).



short_calendar_dates(Trip_id, Date) :- 
    calendar_dates(Trip_id, Date),
    Date >= 20241215,
    Date < 20241223.


1 { assign_trip_train(Trip_id, Date, Train_id) : train(Train_id, _, _) } 1 :- short_calendar_dates(Trip_id, Date).

%1 { assign_trip_train("1-22054-01C-0083", 20241216, Train_id) : train(Train_id, _, _) } 1 :- short_calendar_dates("1-22054-01C-0083",20241216).


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


allowed_trip(T1, T2) :- 
    short_calendar_dates(T1, Date_1),
    short_calendar_dates(T2, Date_2),
    T1 != T2,
    Date_1 != Date_2.


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
    not allowed_trip(T1, T2).
    [1@1, T1, T2]


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




#show max_capacity/4.
%#show next_station_time/4.
#show pendolarismo/4.
#show assign_trip_train/3.