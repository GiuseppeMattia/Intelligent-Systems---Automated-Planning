conteggio(Treno, Data, Cont) :- Cont = #count{Trip : assign_trip_train(Trip, Data, Treno)}, train(Treno, _, _), calendar_dates(_, Data).

#show conteggio/3.