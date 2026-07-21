.PHONY: rimuovi_input crea_input

rimuovi_input:
	rm -f res/asp_encoding/calendar_dates.asp
	rm -f res/asp_encoding/trip_id.asp
	rm -f res/asp_encoding/arrival_departure.asp
	rm -f res/asp_encoding/stops.asp
	rm -f res/asp_encoding/encoded_time_table.asp
	rm -f res/asp_encoding/previous_stations.asp

crea_input:
	python3 src/scripts/generate_calendar_dates_encoding.py
	python3 src/scripts/generate_trip_id.py
	python3 src/scripts/generate_arr_dep.py
	python3 src/scripts/generate_stoptimes_input.py
	python3 -m clingo res/asp_encoding/stops.asp src/asp_scripts/encode_time_table.asp | grep "station" | tr ' ' '\n' | sed 's/$$/./' > res/asp_encoding/encoded_time_table.asp
	python3 -m clingo res/asp_encoding/stops.asp src/asp_scripts/previous_station_generator.asp -V0 | tr ' ' '\n' | grep '^previous_station' | sed 's/$$/./' > res/asp_encoding/previous_stations.asp


ottimizzazione_number:
	rm -f res/output/prova_ottimizzazione_number.asp
	python3 -m clingo res/asp_encoding/trip_id.asp res/asp_encoding/arrival_departure.asp res/asp_encoding/encoded_time_table.asp res/asp_encoding/calendar_dates.asp res/output/fatti_pendolarismo.asp src/asp_scripts/train_types.asp res/asp_encoding/previous_stations.asp src/asp_scripts/optimizations/number_of_trains.asp --stats=2 --quiet=1 --time-limit=300 | grep "assign_trip_train" | tr ' ' '\n' | sed 's/$$/./' > res/output/prova_ottimizzazione_number.asp


ottimizzazione_fermate:
	rm -f res/output/prova_ottimizzazione_fermate.asp
	python3 -m clingo res/asp_encoding/trip_id.asp res/asp_encoding/arrival_departure.asp res/asp_encoding/encoded_time_table.asp res/asp_encoding/calendar_dates.asp res/output/fatti_pendolarismo.asp src/asp_scripts/train_types.asp res/asp_encoding/previous_stations.asp src/asp_scripts/optimizations/train_assignment.asp --stats=2 --quiet=1 --time-limit=300 | grep "assign_trip_train" | tr ' ' '\n' | sed 's/$$/./' > res/output/prova_ottimizzazione_fermate.asp


prova_ottimizzazione: 
	clear && python3 -m clingo res/asp_encoding/trip_id.asp res/output/arrival_departure.asp res/output/encoded_time_table.asp res/asp_encoding/calendar_dates.asp src/asp_scripts/train_assignment.asp --stats=2 | grep "assign_trip_train" | tr ' ' '\n' | sed 's/$$/./' > res/output/prova_ottimizzazione.asp