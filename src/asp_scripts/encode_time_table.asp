first_station(Trip_id, Station_id) :- stop(_, Trip_id, Station_id, 1, _).
next_station(Trip_id, Station_1_id, Station_2_id) :- stop(Stop_1_id, Trip_id, Station_1_id, Seq, Max), stop(Stop_2_id, Trip_id, Station_2_id, Seq + 1, Max), Stop_1_id != Stop_2_id.


#show first_station/2.
#show next_station/3.