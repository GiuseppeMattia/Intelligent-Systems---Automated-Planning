-include .env

export

.PHONY: rimuovi_input crea_input

crea_cartelle:
	mkdir -p res/asp_encoding
	mkdir -p res/output
	mkdir -p res/sanitized
	mkdir -p res/pendolarismo


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


init_pendolarismo:
	rm -f $(PATH_TO_MATRICE_PULITA_TXT)
	rm -f $(PATH_TO_MATRICE_PULITA_CSV)
	rm -f $(PATH_TO_MATRICE_COMUNI_SOSTITUITI_CSV)
	python3 src/scripts/parser.py
	python3 src/scripts/counter.py


ottimizzazione_number:
	rm -f res/output/ottimizzazione_number.asp
	python3 -m clingo $(PATH_TO_TRIP_ID_ASP) $(PATH_TO_ARR_DEP_ASP) $(PATH_TO_ENCODED_TIME_TABLE_ASP) $(PATH_TO_CALENDAR_DATES_ASP) $(PATH_TO_FATTI_PENDOLARISMO) src/asp_scripts/train_types.asp $(PATH_TO_PREVIOUS_STATION_ASP) src/asp_scripts/optimizations/number_of_trains.asp --stats=2 --quiet=1 --time-limit=300 | awk '/^Answer: /{getline; print}' | tr ' ' '\n' | sed 's/$$/./' > $(PATH_TO_OPT_NUM)

ottimizzazione_number_stats:
	rm -f res/output/ottimizzazione_number_stats.asp
	python3 -m clingo $(PATH_TO_TRIP_ID_ASP) $(PATH_TO_ARR_DEP_ASP) $(PATH_TO_ENCODED_TIME_TABLE_ASP) $(PATH_TO_CALENDAR_DATES_ASP) $(PATH_TO_FATTI_PENDOLARISMO) src/asp_scripts/train_types.asp $(PATH_TO_PREVIOUS_STATION_ASP) src/asp_scripts/optimizations/number_of_trains.asp --stats=2 --quiet=1 --time-limit=300 > $(PATH_TO_OPT_NUM_STATS)

ottimizzazione_fermate:
	rm -f res/output/ottimizzazione_fermate.asp
	python3 -m clingo $(PATH_TO_TRIP_ID_ASP) $(PATH_TO_ARR_DEP_ASP) $(PATH_TO_ENCODED_TIME_TABLE_ASP) $(PATH_TO_CALENDAR_DATES_ASP) $(PATH_TO_FATTI_PENDOLARISMO) src/asp_scripts/train_types.asp $(PATH_TO_PREVIOUS_STATION_ASP) src/asp_scripts/optimizations/train_assignment.asp --stats=2 --quiet=1 --time-limit=300 | awk '/^Answer: /{getline; print}' | tr ' ' '\n' | sed 's/$$/./' > $(PATH_TO_OPT_FER)

ottimizzazione_fermate_stats:
	rm -f res/output/ottimizzazione_fermate_stats.asp
	python3 -m clingo $(PATH_TO_TRIP_ID_ASP) $(PATH_TO_ARR_DEP_ASP) $(PATH_TO_ENCODED_TIME_TABLE_ASP) $(PATH_TO_CALENDAR_DATES_ASP) $(PATH_TO_FATTI_PENDOLARISMO) src/asp_scripts/train_types.asp $(PATH_TO_PREVIOUS_STATION_ASP) src/asp_scripts/optimizations/train_assignment.asp --stats=2 --quiet=1 --time-limit=300 > $(PATH_TO_OPT_FER_STATS)





