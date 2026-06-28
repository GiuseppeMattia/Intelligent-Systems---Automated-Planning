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



1 { assign_trip_train(Trip_id, Date, Train_id) : train(Train_id, _, _) } 1 :- calendar_dates(Trip_id, Date), trip_id(Trip_id).



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



trip_non_intersecati(Trip_1, Trip_2) :- 
    Trip_1 != Trip_2,
    trip_arrival_time(Trip_1, Time_1),
    trip_departure_time(Trip_2, Time_2),
    Time_1 < Time_2.


trip_non_intersecati(T2, T1) :- trip_non_intersecati(T1, T2).

trip_intersecati(T1, T2) :- trip_id(T1), trip_id(T2), not trip_non_intersecati(T1, T2), T1 < T2.



:- assign_trip_train(Trip_1, Date, Train),
    assign_trip_train(Trip_2, Date, Train),
    trip_intersecati(Trip_1, Trip_2).




#show assign_trip_train/3.



