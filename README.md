# gperf-callgrind-sqlite3

The `script.py` processes the output of an already compiled callgrind format profile data, creates an SQLite database with the schema mentioned in https://github.com/igprof/igprof/blob/master/src/igpython-analyse, and injects the profile data into the said database.

### Tested workflow
1) Create an executable file from the example payload `test.cpp`. The `-g` flag is important to produce a meaningful callgrind output as it requests the compiler and linker to generate and retain symbol information in the executable itself.
```
➜ g++ -std=c++11 test.cpp -lprofiler -g 
```
2) Turn on CPU profiling for the given run of the executable by defining environment variable CPUPROFILE to the filename to dump the profile to.
```
➜ CPUPROFILE=dump.prof ./a.out
```
3) `pprof` is the script used to analyze a profile and hence convert the `dump.prof` into a callgrind format.
```
➜ pprof --callgrind ./a.out dump.prof  > ls.callgrind
```
4) Run `script.py` to process the said `ls.callgrind` file. Since SQLite can read commands from stdin, the script simply prints out the SQL statements on stdout which can be later piped into SQLite.
```
➜ python script.py ls.callgrind | sqlite3 final.db
```

### Debugging notes
* If you see function addresses instead of the function names, or question marks such as "??" in your callgrind output, then a possible fix would be installing and using the `gdb` debugger during compile time.
