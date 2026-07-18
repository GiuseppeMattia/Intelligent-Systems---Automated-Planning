% python3 -m clingo src/asp_scripts/previous_station_generator.asp res/asp_encoding/stops.asp -V0 | tr ' ' '\n' | grep
'^previous_station' | sed 's/$/./' > res/asp_encoding/previous_stations

previous_station(T, S1, S2) :- stop(_, T, S1, X, _), stop(_, T, S2, Y, _), X < Y, S1 !=S2. #show previous_station/3.