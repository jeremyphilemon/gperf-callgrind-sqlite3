# gperf-callgrind-sqlite3

The `script.py` processes the output of an already compiled callgrind format profile data, creates an SQLITE database with the schema mentioned in https://github.com/igprof/igprof/blob/master/src/igpython-analyse, and inject the profile data into the said database.
