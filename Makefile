-include .env

export

.PHONY: rimuovi_input crea_input

crea_cartelle:
	mkdir -p res/asp_encoding
	mkdir -p res/output
	mkdir -p res/sanitized


rimuovi_input:
	rm -f $(PATH_TO_CALENDAR_DATES_ASP)
	rm -f $(PATH_TO_TRIP_ID_ASP)
	rm -f $(PATH_TO_ARR_DEP_ASP)
	rm -f $(PATH_TO_STOP_ASP)
	rm -f $(PATH_TO_ENCODED_TIME_TABLE_ASP)
	rm -f $(PATH_TO_PREVIOUS_STATION_ASP)


crea_input:
	python3 src/scripts/generate_calendar_dates_encoding.py
	python3 src/scripts/generate_trip_id.py
	python3 src/scripts/generate_arr_dep.py
	python3 src/scripts/generate_stoptimes_input.py
	python3 -m clingo $(PATH_TO_STOP_ASP) src/asp_scripts/encode_time_table.asp | grep "station" | tr ' ' '\n' | sed 's/$$/./' > $(PATH_TO_ENCODED_TIME_TABLE_ASP)
	python3 -m clingo $(PATH_TO_STOP_ASP) src/asp_scripts/previous_station_generator.asp -V0 | tr ' ' '\n' | grep '^previous_station' | sed 's/$$/./' > $(PATH_TO_PREVIOUS_STATION_ASP)


ottimizzazione_number:
	rm -f res/output/ottimizzazione_number.asp
	python3 -m clingo $(PATH_TO_TRIP_ID_ASP) $(PATH_TO_ARR_DEP_ASP) $(PATH_TO_ENCODED_TIME_TABLE_ASP) $(PATH_TO_CALENDAR_DATES_ASP) $(PATH_TO_FATTI_PENDOLARISMO) src/asp_scripts/train_types.asp $(PATH_TO_PREVIOUS_STATION_ASP) src/asp_scripts/optimizations/number_of_trains.asp --stats=2 --quiet=1 --time-limit=300 | grep -E "assign_trip_train|allowed_next_station|salta|new_station" | tr ' ' '\n' | sed 's/$$/./' > $(PATH_TO_OPT_NUM)

ottimizzazione_number_stats:
	rm -f res/output/ottimizzazione_number_stats.asp
	python3 -m clingo $(PATH_TO_TRIP_ID_ASP) $(PATH_TO_ARR_DEP_ASP) $(PATH_TO_ENCODED_TIME_TABLE_ASP) $(PATH_TO_CALENDAR_DATES_ASP) $(PATH_TO_FATTI_PENDOLARISMO) src/asp_scripts/train_types.asp $(PATH_TO_PREVIOUS_STATION_ASP) src/asp_scripts/optimizations/number_of_trains.asp --stats=2 --quiet=1 --time-limit=300 > $(PATH_TO_OPT_NUM_STATS)

ottimizzazione_fermate:
	rm -f res/output/ottimizzazione_fermate.asp
	python3 -m clingo $(PATH_TO_TRIP_ID_ASP) $(PATH_TO_ARR_DEP_ASP) $(PATH_TO_ENCODED_TIME_TABLE_ASP) $(PATH_TO_CALENDAR_DATES_ASP) $(PATH_TO_FATTI_PENDOLARISMO) src/asp_scripts/train_types.asp $(PATH_TO_PREVIOUS_STATION_ASP) src/asp_scripts/optimizations/train_assignment.asp --stats=2 --quiet=1 --time-limit=300 | grep "assign_trip_train" | tr ' ' '\n' | sed 's/$$/./' > $(PATH_TO_OPT_FER)

ottimizzazione_fermate_stats:
	rm -f res/output/ottimizzazione_fermate_stats.asp
	python3 -m clingo $(PATH_TO_TRIP_ID_ASP) $(PATH_TO_ARR_DEP_ASP) $(PATH_TO_ENCODED_TIME_TABLE_ASP) $(PATH_TO_CALENDAR_DATES_ASP) $(PATH_TO_FATTI_PENDOLARISMO) src/asp_scripts/train_types.asp $(PATH_TO_PREVIOUS_STATION_ASP) src/asp_scripts/optimizations/train_assignment.asp --stats=2 --quiet=1 --time-limit=300 > $(PATH_TO_OPT_FER_STATS)








prova_ottimizzazione: 
	clear && python3 -m clingo $(PATH_TO_TRIP_ID_ASP) res/output/arrival_departure.asp res/output/encoded_time_table.asp $(PATH_TO_CALENDAR_DATES_ASP) src/asp_scripts/train_assignment.asp --stats=2 | grep "assign_trip_train" | tr ' ' '\n' | sed 's/$$/./' > res/output/prova_ottimizzazione.asp