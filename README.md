# munin-dash

This is a proof of concept alternative web interface for [munin](https://munin-monitoring.org/). Instead of the generated static png pictures it uses interactive graphs. It is based python and plotly.

As it is a proof of concept it is totally not suitable for production use. It has many issues, it only able to show your graphs, so you can get the concept how it could look like.

I am not a web developer, so the web interface it's not very nice. Focus on the graphs please.


## Installation

Just clone the git repo on the host where you have your munin RRD files (where you have the munin web interface) and run the python scripts directly from the repo dir. You may mis some python packages what you can install with pip. Eg:
```
python3 -m pip install dash sqlite3 rrdtool pandas 
```


## Usage

First run the `rrd2sqlite.py` script, this generates all the sqlite files what the web interface gonna use. This script may run for long.

As soon as you have all the sqllite files you can start the web interface from the repo:
```
./munin-dash-web.py
```

The URL of the new web interface is printed out on the screen, copy that to your browser.

