This enables automation of a suitable power supply to turn on/off and measure 
current and voltage of a connnected load. Development used a BK Precision 1687B
power supply - https://www.bkprecision.com/products/power-supplies/1687B

Creates a serial-over USB connection to the power supply and runs a current test
on a connected piece of LED. Sends results to a local sqlite3 database.
A locally-hosted Grafana (https://grafana.com/grafana/) instance can then display
the test data as a time-series graph. A PDF of the test results is also generated.
