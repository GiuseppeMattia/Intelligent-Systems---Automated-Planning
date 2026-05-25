% RUN WITH:
% python3 -m clingo res/asp_encoding/links.asp res/asp_encoding/stations.asp res/asp_encoding/trip_id.asp src/asp_scripts/time_tables.asp 

%stop_time(Trip_id, Station_id, Stop_sequence) :- station(Station_id, _, _), trip_id(Trip_id), Stop_sequence = 1.

{ stop_time(Trip_id, Station_id, 1) : station(Station_id, _, _) } :- trip_id(Trip_id).

:- trip_id(Trip_id), not #count{Station_id : stop_time(Trip_id, Station_id, 1)} = 1.




% stop_time(Trip_id, Station_id_2, Stop_sequence_2) :- 
%     stop_time(Trip_id, Station_id_1, Stop_sequence_1), 
%     Stop_sequence_2 = Stop_sequence_1 + 1, 
%     connected(Station_id_1, Station_id_2).

% :- stop_time(Trip_id, Station_id_1, _), stop_time(Trip_id, Station_id_2, _), Station_id_1=Station_id_2.




#show stop_time/3.