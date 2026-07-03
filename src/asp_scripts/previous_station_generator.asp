previous_station(T, S1, S2) :- stop(_, T, S1, X, _), stop(_, T, S2, Y, _), X < Y, S1 != S2.

#show previous_station/3.

