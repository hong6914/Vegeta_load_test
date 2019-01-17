# Vegeta-based Load Testing Automation
Python scripts to automate load testing with Vegeta. With sample web server and client.

Been simple enough, Vegeta is good for starting the load testing for quick verifications.
When doing load tests manually, we may choose a start rate and run it for certain length of time. When the failure rate is above the expected, we drop the rate and continue. It may get passed or failed in the next run, and we update the rate again to try to make it the next time. The script tries to mimic the behavior and get the steps automated.

## Requirements
  
###Install Vegeta
Please be sure to
- follow [this link](https://github.com/tsenart/vegeta) to get Vegeta installed properly on your machine.
- add Vegeta's location to your ${PATH}, either temporarily in the shell or permanently in the shell config file.

Vegeta supports all the major platforms. Please [go here](https://github.com/tsenart/vegeta/releases) to get the latest bits. 

### Install Python 3
Typical location of the bits are under `/usr/local/bin/python3/` on Mac and Linux.

## Features of the script
- Keep adjusting the load test rate to meet the target failure rate.
    Vegeta deals with one-time run. It is the tester's job to check the results and decides on continuing with a new rate.
    The script uses simple convergence function logics to be adpative to the passes and failures, and adjust the rate to get closer to the highest acceptable rate.
- Environment settings check on Python interpreter, Vegeta etc.
- Saves all test results to timestamp-named files for further analysis.
    Original vegeta json results
    test settings such as start rate, bump-up rate and warm-up time etc.
    Sorted result CSV file for easier charting
- Properly handles Ctrl-C that if we need to terminate the execution at some point, the partial results are still saved to files.

## List of files
- loadtest_vegeta.py - script that automates the load testing
- testserver.py - sample Flask-based web server for testing vegeta locally
- test_local_erquests.txt - sample vegeta target file

## Command-line Parameters
- `--target_file`, or `-f`
    Vegeta target file that stores all the HTTP requests to attack the web service.
- `--failure_threshold`, or `-t`
    The EXPECTED failure threshold. We'll adjust the load rate to meet it. Default = 5.0%.
- `--start_rate`, or `-s`
    Number of requests/second to start the load test. Optional. Default is 50.
- `--test_time`, or `-e`
    Number of seconds to run one load test. Optional. Default is 10 seconds.
- `--step_rate`, or `-p`
    Number of requests/second to add to the rate for the next run, if it goes well. Optional. Default is 50.
- `--warm_up_rate`, or `-u`
    Number of requests/second to warm up target service before load tests. Optional. Default is 20. Set to 0 to skip it.
- `--warm_up_time`, or `-w`
    Number of seconds to warm up target service. Optional. Default is 10 seconds.
- `--rest_time`, or `-r`
    Number of seconds to rest between two load runs. Optional. Default is 5 seconds. Set to 0 to skip it.

## Sample command
- `python3 loadtest_vegeta.py`
    To get the help on how to use it.
- `python3 loadtest_vegeta.py -f <my_target_file>`
    Run the load test with the target file that stores all the HTTP requests via vegeta, and all the default settings.
- `python3 loadtest_vegeta.py -f ./test_local_requests.txt -t 2 -s 200 -e 10 -p 50 -u 50 -w 5 -r 3`
    Run the load tests with
        target file set to `./test_local_requests.txt`,
        failure threshold to 2%,
        start rate set to 200 requests/second,
        each test runs for 10 seconds,
        add 50 more requests/second if the previous run goes well,
        warm-up rate set to 50/s and for 5 seconds,
        rest for 3 seconds between two load runs

## Sample output
```
$ python3 loadtest_vegeta.py -f ./test_local_requests.txt -t 2 -s 200 -e 10 -p 50 -u 50 -w 5 -r 3

Vegeta is installed at /usr/local/bin/vegeta


Warming up target service for 50 requests/s and run for 5 seconds ...

	vegeta attack -rate=50 -duration=5s -targets=./test_local_requests.txt | vegeta report
	Rest for 3 seconds ...
	Done


Executing:  vegeta attack -rate=200 -duration=10s -targets=./test_local_requests.txt | vegeta report -type json
	Response: {...}
	Expected Failure Rate: 2.0%		Actual: 0%

	Adjust new rate to 250 requests/second
	Rest for 3 seconds ...

Executing:  vegeta attack -rate=250 -duration=10s -targets=./test_local_requests.txt | vegeta report -type json
	Response: {...}
	Expected Failure Rate: 2.0%		Actual: 0%

	Adjust new rate to 300 requests/second
	Rest for 3 seconds ...

Executing:  vegeta attack -rate=300 -duration=10s -targets=./test_local_requests.txt | vegeta report -type json
	Response: {...}
	Expected Failure Rate: 2.0%		Actual: 0.20000000000000284%

	Adjust new rate to 350 requests/second
	Rest for 3 seconds ...

Executing:  vegeta attack -rate=350 -duration=10s -targets=./test_local_requests.txt | vegeta report -type json
	Response: {...}
	Expected Failure Rate: 2.0%		Actual: 1.3714285714285666%

	Adjust new rate to 400 requests/second
	Rest for 3 seconds ...

Executing:  vegeta attack -rate=400 -duration=10s -targets=./test_local_requests.txt | vegeta report -type json
	Response: {...}
	Expected Failure Rate: 2.0%		Actual: 2.325000000000003%

	Adjust new rate to 450 requests/second
	Rest for 3 seconds ...

Executing:  vegeta attack -rate=450 -duration=10s -targets=./test_local_requests.txt | vegeta report -type json
	Response: {...}

	Expected Failure Rate: 2.0%		Actual: 4.333333333333329%

	Adjust new rate to 424 requests/second
	Rest for 3 seconds ...

Executing:  vegeta attack -rate=424 -duration=10s -targets=./test_local_requests.txt | vegeta report -type json
	Response: {...}
	Expected Failure Rate: 2.0%		Actual: 6.415094339622641%

	Adjust new rate to 390 requests/second
	Rest for 3 seconds ...

Executing:  vegeta attack -rate=390 -duration=10s -targets=./test_local_requests.txt | vegeta report -type json
	Response: {...}
	Expected Failure Rate: 2.0%		Actual: 2.589743589743591%

	Adjust new rate to 379 requests/second
	Rest for 3 seconds ...

Executing:  vegeta attack -rate=379 -duration=10s -targets=./test_local_requests.txt | vegeta report -type json
	Response: {...}
	Expected Failure Rate: 2.0%		Actual: 5.118733509234829%

	Adjust new rate to 349 requests/second
	Rest for 3 seconds ...

Executing:  vegeta attack -rate=349 -duration=10s -targets=./test_local_requests.txt | vegeta report -type json
	Response: {...}
	Expected Failure Rate: 2.0%		Actual: 1.232091690544408%

	Adjust new rate to 359 requests/second
	Rest for 3 seconds ...

Executing:  vegeta attack -rate=359 -duration=10s -targets=./test_local_requests.txt | vegeta report -type json
	Response: {...}
	Expected Failure Rate: 2.0%		Actual: 12.033426183844014%

	Failure rate is too high, and we tried for 5 times. Stop the load test.
Finished load testing.


Test result        is saved to /Users/<my name>/code_path/load_test_vegeta_<my name>_2018_10_10_17_41_03.log

Test settings     are saved to /Users/<my name>/code_path/load_test_vegeta_<my name>_2018_10_10_17_41_03_setting.log

Sorted test result is saved to /Users/<my name>/code_path/load_test_vegeta_<my name>_2018_10_10_17_41_03.csv


----- Vegeta Load Test Summary -----

	Target Failure Threshold: 2.0%
	Vegeta Target File      : ./test_local_requests.txt
	Start Request Rate      : 200/second
	Bump-up Rate            : 50/second
	Each Load Test Time     : 10 seconds
	Break between two runs  : 3 seconds
	Service Warm-up Rate    : 50/second
	        Warm-up Time    : 5 seconds

	Total Runs: 11


Requests                                         Latencies
ID  Total   Rate   Success%  Failure%  Time      Mean      50th      95th      99th      Max
==  ======  =====  ========  ========  ========  ========  ========  ========  ========  ========
 1    2000    200  100.0000  0         9.995s    1.800s    1.170s    5.650s   10.915s   12.369s 
 2    2500    250  100.0000  0         9.996s    4.359s    2.448s   12.929s   15.003s   15.004s 
 3    3000    300  99.80000  0         9.997s    5.781s    4.742s   15.002s   15.004s   15.015s 
 4    3500    350  98.62857  1.371429  9.997s    7.069s    6.211s   15.003s   15.012s   15.027s 
 5    4000    400  97.67500  2.325000  9.998s    7.932s    7.493s   15.073s   15.220s   15.376s 
 6    4500    450  95.66667  4.333333  9.998s    8.619s    9.049s   15.004s   15.053s   15.128s 
 7    4240    424  93.58491  6.415094  9.997s    8.134s    8.847s   15.056s   15.116s   15.170s 
 8    3900    390  97.41026  2.589744  9.997s    7.751s    6.523s   15.004s   15.034s   15.079s 
 9    3790    379  94.88127  5.118734  9.997s    7.357s    6.271s   15.022s   15.116s   15.145s 
10    3490    349  98.76791  1.232092  9.997s    6.823s    6.192s   15.003s   15.035s   15.067s 
11    3590    359  87.96657  12.03343  9.997s    6.013s    3.945s   15.041s   15.142s   15.159s 

Process finished with exit code 0
```
