short_calendar_dates(Trip_id, Date) :- 
    calendar_dates(Trip_id, Date),
    Date >= 20241215,
    Date < 20241223.


1 { assign_trip_train(Trip_id, Date, Train_id) : train(Train_id, _, _) } :- short_calendar_dates(Trip_id, Date).


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


last_station(Trip_id, Station_id) :-
    trip_id(Trip_id),
    effective_next_station(Trip_id, _, Station_id),
    not effective_next_station(Trip_id, Station_id, _).

trip_departure_time(Trip_id, Time) :-
    trip_id(Trip_id),
    effective_first_station(Trip_id, Station_id),
    departure_time(Trip_id, Station_id, Time).

trip_arrival_time(Trip_id, Time) :-
    trip_id(Trip_id),
    last_station(Trip_id, Station_id),
    arrival_time(Trip_id, Station_id, Time).


sovrapposizione_oraria(T1, T2) :-
    T1 < T2,
    trip_departure_time(T1, Dep1), trip_arrival_time(T1, Arr1),
    trip_departure_time(T2, Dep2), trip_arrival_time(T2, Arr2),
    Arr1 > Dep2,
    Arr2 > Dep1.


:- assign_trip_train(T1, Date, Train),
    assign_trip_train(T2, Date, Train),
    sovrapposizione_oraria(T1, T2).


allowed_trip(T1, T2) :- 
    short_calendar_dates(T1, Date),
    short_calendar_dates(T2, Date),
    T1 != T2,
    last_station(T1, Station), 
    effective_first_station(T2, Station),
    trip_departure_time(T2, Dep),
    trip_arrival_time(T1, Arr),
    Dep >= Arr.                  

%Now this weak constraint pays at level 3, as it needs to be prioritized with respect to the number of trains
has_valid_pred(T2, Date, Train) :-
    assign_trip_train(T1, Date, Train),
    assign_trip_train(T2, Date, Train),
    allowed_trip(T1, T2).

:~ assign_trip_train(T2, Date, Train),
   not has_valid_pred(T2, Date, Train).
   [1@3, T2, Train]



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


:- effective_pendolarismo(S1, S2, Pass, Fascia),
    short_calendar_dates(Trip, Date),
    next_station_time(Trip, S1, S2, Fascia),
    Sum = #sum{C : assign_trip_train(Trip, Date, Train), train(Train, _, C)},
    Sum < Pass.


ha_pendolarismo(S2, Fascia, Trip) :- 
    effective_pendolarismo(S1, S2, _, Fascia), 
    short_calendar_dates(Trip, _),
    effective_next_station(Trip, S1, S2), 
    next_station_time(Trip, S1, _, Fascia).


salta(Trip, S1, S2) :-
    next_station_time(Trip, S1, S2, Fascia),
    not ha_pendolarismo(S2, Fascia, Trip),
    short_calendar_dates(Trip, _),
    not last_station(Trip, S2).



allowed_next_station(Trip, S1, S2) :-
    short_calendar_dates(Trip, _),
    effective_next_station(Trip, S1, S2),
    not salta(Trip, S1, S2).


tot_fermate_per_trip(Tot, Trip) :- 
    Tot = #count{S1, S2 : effective_next_station(Trip, S1, S2), not salta(Trip, S1, S2)}, 
    short_calendar_dates(Trip, _).


tot_fermate(Tot) :- Tot = #sum{F, Trip : tot_fermate_per_trip(F, Trip)}.



tempo_impiegato(T, S1, S2, Tempo) :-
    short_calendar_dates(T, _),
    effective_next_station(T, S1, S2),
    departure_time(T, S1, Start),
    arrival_time(T, S2, End),
    Tempo = End - Start.


tempo_rest(T, S2, Tempo) :-
    short_calendar_dates(T, _),
    not salta(T, S1, S2),
    effective_next_station(T, S1, S2),
    not effective_first_station(T, S2),
    not last_station(T, S2),
    arrival_time(T, S2, Start),
    departure_time(T, S2, End),
    Tempo = End - Start.


tempo_per_trip(T, Tempo) :-
    short_calendar_dates(T, _),
    Tempo_percorso = #sum{Time, S1, S2 : tempo_impiegato(T, S1, S2, Time)},
    Tempo_rest = #sum{Time, S : tempo_rest(T, S, Time)},
    Tempo = Tempo_percorso + Tempo_rest.

%This weak constraint makes the solver pay for every train that it uses
used_train(T) :- assign_trip_train(_, _, T).
:~ used_train(T). [1@1, T]



1 { limite_max(M * 20) : M = 50..250 } 1.

1 { limite_min(N * 20) : N = 0..250 } 1.

:- limite_min(MinT), limite_max(MaxT), MinT > MaxT.

:- train(Train, _, _), 
    limite_max(MaxT),
    #sum{Tempo, Trip : tempo_per_trip(Trip, Tempo), assign_trip_train(Trip, _, Train)} > MaxT.

:- train(Train, _, _), limite_min(MinT), 
    used_train(Train),
    #sum{Tempo, Trip : tempo_per_trip(Trip, Tempo), assign_trip_train(Trip, _, Train)} < MinT.

:~ limite_max(MaxT), limite_min(MinT). [MaxT-MinT@2]




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
#show used_train/1.
#show tempo_per_trip/2.

