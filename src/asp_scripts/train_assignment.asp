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



% trip_non_intersecati(Trip_1, Trip_2) :- 
%     Trip_1 != Trip_2,
%     trip_arrival_time(Trip_1, Time_1),
%     trip_departure_time(Trip_2, Time_2),
%     Time_1 < Time_2.


% trip_non_intersecati(T2, T1) :- trip_non_intersecati(T1, T2).

% trip_intersecati(T1, T2) :- trip_id(T1), trip_id(T2), not trip_non_intersecati(T1, T2), T1 < T2.






% coppia_stessa_data(T1, T2) :- 
%     calendar_dates(T1, Date), 
%     calendar_dates(T2, Date), 
%     T1 < T2.

% trip_intersecati(T1, T2) :-
%     coppia_stessa_data(T1, T2),
%     trip_departure_time(T1, Dep1), trip_arrival_time(T1, Arr1),
%     trip_departure_time(T2, Dep2), trip_arrival_time(T2, Arr2),
%     Arr1 >= Dep2,
%     Arr2 >= Dep1.


% :- assign_trip_train(Trip_1, Date, Train),
%     assign_trip_train(Trip_2, Date, Train),
%     trip_intersecati(Trip_1, Trip_2).




% sovrapposizione(T1, T2, Date) :-
%     calendar_dates(T1, Date),
%     calendar_dates(T2, Date),
%     T1 < T2,
%     trip_departure_time(T1, Dep1), trip_arrival_time(T1, Arr1),
%     trip_departure_time(T2, Dep2), trip_arrival_time(T2, Arr2),
%     Arr1 >= Dep2,
%     Arr2 >= Dep1.


% :- sovrapposizione(T1, T2, Date),
%    assign_trip_train(T1, Date, Train),
%    assign_trip_train(T2, Date, Train).




train_id(Id) :- train(Id, _, _).

1 { assign_trip_train(Trip_id, Date, Train_id) : train_id(Train_id) } 1 :- calendar_dates(Trip_id, Date).



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
    T1 < T2,
    trip_departure_time(T1, Dep1), trip_arrival_time(T1, Arr1),
    trip_departure_time(T2, Dep2), trip_arrival_time(T2, Arr2),
    Arr1 >= Dep2,
    Arr2 >= Dep1.


sovrapposizione_data(T1, T2) :-
    T1 < T2,
    calendar_dates(T1, Date),
    calendar_dates(T2, Date).


short_assign(Trip, Train) :- assign_trip_train(Trip, _, Train).


:- sovrapposizione_oraria(T1, T2),
    sovrapposizione_data(T1, T2),
    short_assign(T1, Train),
    short_assign(T2, Train).



% Rules        : 2713591  (Original: 1639531)
% Rules        : 2720141  (Original: 1646081)
% Rules        : 2720116  (Original: 1646056)



% CON QUESTO È UNSAT
% allowed_trip(Trip_1, Trip_2) :-
%     Trip_1 < Trip_2,
%     sovrapposizione_data(Trip_1, Trip_2),
%     last_station(Trip_1, Station),
%     first_station(Trip_2, Station),
%     trip_departure_time(Trip_2, Dep_2),
%     trip_arrival_time(Trip_1, Arr_1),
%     Dep_2 > Arr_1.



% :- short_assign(Trip_1, Train),
%     short_assign(Trip_2, Train),
%     not allowed_trip(Trip_1, Trip_2).




% CON QUESTO VA, MA IL SOLVING È MOLTO LUNGO
connessione_valida(T_Prima, T_Dopo) :-
    sovrapposizione_data(T_Prima, T_Dopo),
    last_station(T_Prima, Station),
    first_station(T_Dopo, Station),
    trip_departure_time(T_Dopo, Dep),
    trip_arrival_time(T_Prima, Arr),
    Dep > Arr.

allowed_trip(T1, T2) :- T1 < T2, connessione_valida(T1, T2).
allowed_trip(T1, T2) :- T1 < T2, connessione_valida(T2, T1).

:- short_assign(T1, Train),
   short_assign(T2, Train),
   T1 < T2,
   not allowed_trip(T1, T2).








% :- assign_trip_train(Trip_1, Date, Train),
%     assign_trip_train(Trip_2, Date, Train),
%     Trip_1 != Trip_2,
%     last_station(Trip_1, Station_1),
%     first_station(Trip_2, Station_2),
%     Station_1 != Station_2.






#show assign_trip_train/3.



% Time         : 66.911s (Solving: 0.71s 1st Model: 0.64s Unsat: 0.00s)
