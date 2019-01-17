"""
This script takes care of

1. Warm up the service JVM with a small set of HTTP/HTTPS calls
2. Execute load tests via Vegeta with initial request rates and other settings,
3. Parse the test result and adjust the rate according to the target pass/fail threshold,
4. re-run step 2 till the time the failure rate exceeds the threshold the 5th time
5. record all the run results
6. Result report

Note:
    1. Assume Vegeta is properly installed according to https://github.com/tsenart/vegeta
    2. Python 3 and all the dependent libraries are pip-ed

Environment:
    Mac, Windows, Linux

"""

import os
import json
import platform
import subprocess
import sys
import signal
import time
import getpass
import argparse
import traceback
from enum import Enum
from error_code import ErrorCode
from utils import *
from load_test import *

#from test.testtest import TestTest


# Global variables -----
test_run = None


##############################################################################
def signal_handler(sig, frame):
    global test_run

    if sig == signal.SIGINT:
        print('\n----- Ctrl-C is pressed. Stop the test run. -----\n')

        # If we have executed some tests already, save them.
        if len(test_run.result_set) > 0:
            test_run.tests_summary()

        sys.exit(ErrorCode.processAbnormalExit)


###############################################################################
class VegetaLoadTest(LoadTest):
    target_file = None
    failure_threshold = 5.0
    service_warm_up_rate = 20                                                   # per second
    service_warm_up_time = 10                                                   # in seconds
    load_start_rate = 50                                                        # per second
    load_test_time = 10                                                         # in seconds
    load_rest_time = 5                                                          # in seconds
    load_step_rate = 50                                                         # per second
    result_set = []

    # --------------------------------------------------------------------------
    def __init__(self, target_file, failure_threshold, start_rate, test_time, step_rate,
                 warm_up_rate, warm_up_time, rest_time):
        # check the parameters
        if not os.path.exists(target_file):
            raise Exception(ErrorCode.fileNotExist, "Cannot find target file {}".format(target_file))
        else:
            self.target_file = target_file

        if failure_threshold:
            if failure_threshold < 0.0 or failure_threshold > 10.0:
                raise Exception(ErrorCode.valueOutOfRange)
            else:
                self.failure_threshold = failure_threshold

        if start_rate:
            if start_rate <= 0 or start_rate > 5000:                            # No more than 5000 requests/second
                raise Exception(ErrorCode.valueOutOfRange)
            else:
                self.load_start_rate = start_rate

        if test_time:
            if test_time < 0 or test_time > 3600:                               # We do not run for more than one hour
                raise Exception(ErrorCode.valueOutOfRange)
            else:
                self.load_test_time = test_time

        if step_rate:
            if step_rate <= 0 or step_rate > 500:                               # Do NOT increment by 500 requests/s
                raise Exception(ErrorCode.valueOutOfRange)
            else:
                self.load_step_rate = step_rate

        if warm_up_rate:
            if warm_up_rate <= 0 or warm_up_rate > 5000:                        # No more than 5000 requests/second
                raise Exception(ErrorCode.valueOutOfRange)
            else:
                self.service_warm_up_rate = warm_up_rate

        if warm_up_time:
            if warm_up_time < 0 or warm_up_time > 600:                          # We do not run for more than 10 minutes
                raise Exception(ErrorCode.valueOutOfRange)
            else:
                self.service_warm_up_time = warm_up_time

        if rest_time:
            if rest_time < 0 or rest_time > 60:                                 # We do not rest for more than 1 minute
                raise Exception(ErrorCode.valueOutOfRange)
            else:
                self.load_rest_time = rest_time

    # --------------------------------------------------------------------------
    def __del__(self):
        pass

    # --------------------------------------------------------------------------
    def execute_tests(self):
        ret = self.check_vegeta_settings()
        if ret == 0:
            ret = self.warm_up_load_test()
            if ret == 0:
                ret = self.execute_load_test()
                if ret == 0:
                    ret = self.tests_summary()

        return ret

    # --------------------------------------------------------------------------
    def check_vegeta_settings(self):
        return super.check_load_tool_settings('vegeta', 2)

    # --------------------------------------------------------------------------
    '''
    To warm up the target service/JVM, we will execute the target file for a short time. Things
    will get more stable after its run.
    Skip it if the warm up time is set to zero.
    '''
    def warm_up_load_test(self):
        if self.service_warm_up_time == 0:
            print('\n\nSkip on warming up target service\'s JVM\n\n')
            return 0

        print('\n\nWarming up target service for {} requests/s and run for {} seconds ...\n'.format(
            self.service_warm_up_rate, self.service_warm_up_time))
        cmd = "vegeta attack -rate={} -duration={}s -targets={} | vegeta report".format(
            self.service_warm_up_rate, self.service_warm_up_time, self.target_file)
        print('\t{}'.format(cmd))

        ret, result = self.execute_multiple_commands(cmd)
        if self.load_rest_time > 0:
            print('\tRest for {} seconds ...'.format(self.load_rest_time))
            time.sleep(self.load_rest_time)
        print("\tDone\n")
        return ret

    # --------------------------------------------------------------------------
    def execute_load_test(self):
        self.result_set = []
        attack_rate = self.load_start_rate
        attack_time = self.load_test_time
        fail_count = 0

        while True:
            cmd = "vegeta attack -rate={} -duration={}s -targets={} | vegeta report -type json".format(
                attack_rate, attack_time, self.target_file)
            print('\nExecuting:  {}'.format(cmd))

            ret, result = self.execute_multiple_commands(cmd)

            ''' Vegeta uses single-quotes in json object. It will fail typical json parsers to validate the objects.
                Convert to use double-quotes instead. '''
            entry = json.loads(result[0].replace("\'", "\""))

            self.result_set.append(entry)
            print('\tResponse: {}'.format(entry))

            ret, new_rate, fail_count = self.result_analysis_adaptive_adjustments(entry, attack_rate, fail_count)
            if ret != 0 or fail_count >= 5:
                break

            if self.load_rest_time > 0:
                print('\tRest for {} seconds ...'.format(self.load_rest_time))
                time.sleep(self.load_rest_time)
            attack_rate = new_rate

        print("Finished load testing.\n")
        return 0

    # --------------------------------------------------------------------------
    def result_analysis_adaptive_adjustments(self, entry, current_rate, fail_count):
        success_rate = entry['success'] * 100
        current_failure_rate = 100 - success_rate
        print('\tExpected Failure Rate: {}%\t\tActual: {}%\n'.format(self.failure_threshold, current_failure_rate))

        continue_test = (current_failure_rate / self.failure_threshold - 1) < 0.2

        if continue_test:
            new_rate = current_rate + self.load_step_rate if fail_count == 0 else \
                current_rate + int(self.load_step_rate / 5)

        else:
            fail_count += 1
            if fail_count >= 5:
                print('\tFailure rate is too high, and we tried for {} times. Stop the load test.'.format(fail_count))
                return ErrorCode.requestRateTooHigh, current_rate, fail_count

            if current_failure_rate < self.failure_threshold:
                new_rate = current_rate + self.load_step_rate
            else:
                ratio = (1 - self.failure_threshold / current_failure_rate)
                new_rate = current_rate - int(self.load_step_rate * ratio)

            if abs(new_rate - current_rate) < 5:                                    # No need to continue
                print('\tThe expected new rate {} is too close to existing rate {} - stop the load test.'.format(
                    new_rate, current_rate))
                return ErrorCode.requestRateTooHigh, None, fail_count

        print('\tAdjust new rate to {} requests/second'.format(new_rate))
        return 0, new_rate, fail_count

    # --------------------------------------------------------------------------
    def tests_summary(self):
        if len(self.result_set) == 0:
            return 0

        result_name = '{}/load_test_vegeta_{}_{}'.format(
            TestUtils. get_absolute_path(), getpass.getuser(), time.strftime('%Y_%m_%d_%H_%M_%S'))

        # The original results are saved to the log file
        result_log_file = '{}.log'.format(result_name)
        result_setting_file = '{}_setting.log'.format(result_name)
        result_csv_file = '{}.csv'.format(result_name)

        print('\nTest result        is saved to {}'.format(result_log_file))
        print('\nTest settings     are saved to {}'.format(result_setting_file))
        print('\nSorted test result is saved to {}'.format(result_csv_file))

        with open(result_log_file, 'w')as f:
            f.writelines(list('%s\n' % item for item in self.result_set))

        # The test settings are saved to the xxx_settings.log file
        summary_str = '\n\n----- Vegeta Load Test Summary -----\n\n\
\tTarget Failure Threshold: {}%\n\
\tVegeta Target File      : {}\n\
\tStart Request Rate      : {}/second\n\
\tBump-up Rate            : {}/second\n\
\tEach Load Test Time     : {} seconds\n\
\tBreak between two runs  : {} seconds\n\
\tService Warm-up Rate    : {}/second\n\
\t        Warm-up Time    : {} seconds\n\n\
\tTotal Runs: {}\n\
'.format(self.failure_threshold, self.target_file, self.load_start_rate, self.load_step_rate, self.load_test_time,
         self.load_rest_time, self.service_warm_up_rate, self.service_warm_up_time, len(self.result_set))
        print(summary_str)
        with open(result_setting_file, 'w')as f:
            f.write(summary_str)

        # The sorted results are saved to one CSV file for later processing
        with open(result_csv_file, 'w')as f:
            f.write('ID,Total_Requests,Request_Rate,Success%,Failure%,Time(s),Latency_Mean(s),Latency_50th(s),\
Latency_95th(s),Latency_99th(s),Latency_Max(s)\n')

            print('\n\
Requests                                         Latencies\n\
ID  Total   Rate   Success%  Failure%  Time      Mean      50th      95th      99th      Max\n\
==  ======  =====  ========  ========  ========  ========  ========  ========  ========  ========')
            i = 1
            for one_test in self.result_set:
                success_rate = one_test['success'] * 100.0
                failure_rate = 100.0 - success_rate
                total_time, total_time_unit = self.evalute_time(one_test['duration'])
                time_mean, time_unit_mean = self.evalute_time(one_test['latencies']['mean'])
                time_50th, time_unit_50th = self.evalute_time(one_test['latencies']['50th'])
                time_95th, time_unit_95th = self.evalute_time(one_test['latencies']['95th'])
                time_99th, time_unit_99th = self.evalute_time(one_test['latencies']['99th'])
                time_max,  time_unit_max  = self.evalute_time(one_test['latencies']['max'])

                test_result = (i, one_test['requests'], int(one_test['rate']), success_rate, failure_rate,
                        total_time, total_time_unit, time_mean, time_unit_mean,
                        time_50th, time_unit_50th, time_95th, time_unit_95th,
                        time_99th, time_unit_99th, time_max, time_unit_max)

                format_str = '{0:2d}   {1:5d}  {2:5d}  '
                format_str += '{3:3.4f}  ' if int(success_rate) == 100 else '{3:2.5f}  '

                if int(failure_rate) == 0:
                    format_str += '{4:<8.0f}  '
                elif int(failure_rate) < 10:
                    format_str += '{4:<1.6f}  '
                else:
                    format_str += '{4:<2.5f}  '

                csv_format_str = ','.join(format_str.split())

                format_str += '{5:>5.3f}{6:2}  {7:>6.3f}{8:2}  {9:>6.3f}{10:2}  {11:>6.3f}{12:2}  {13:>6.3f}{14:2}  {15:>6.3f}{16:2}'

                print(format_str.format(*test_result))

                csv_result = (i, one_test['requests'], int(one_test['rate']), success_rate, failure_rate,
                        total_time, time_mean, time_50th, time_95th, time_99th, time_max)

                csv_format_str += '{5:5.3f},{6:6.3f},{7:6.3f},{8:6.3f},{9:6.3f},{10:6.3f}\n'
                # print(csv_format_str)
                f.write(csv_format_str.format(*csv_result))

                i += 1

        return 0

    # --------------------------------------------------------------------------
    # Evaluate time values
    def evalute_time(self, time_value):
        total_time = time_value / 1000000.0
        time_unit = 'ms'
        if total_time > 1000:
            total_time /= 1000.0
            time_unit = 's'
        return total_time, time_unit


###############################################################################
# MAIN
#
def main(argv):
    global test_run

    signal.signal(signal.SIGINT, signal_handler)

    args = argparse.ArgumentParser(description='Load Testing Tool --- Vegeta Based')
    args.add_argument('--target_file',  "-f", type=str, action="store", dest="target_file", default=None,
                      help="The file that stores all the HTTP requests to attack the web service.")
    args.add_argument('--failure_threshold', "-t", type=float, action="store", dest="failure_threshold", default=5.0,
                      help="The EXPECTED failure threshold. We'll adjust the load rate to meet it. Default = 5%%")
    args.add_argument('--start_rate',   "-s", type=int, action="store", dest="start_rate", default=50, nargs='?',
                      help="Number of requests/second to start load test. Optional. Default is 50.")
    args.add_argument('--test_time',    "-e", type=int, action="store", dest="test_time", default=10, nargs='?',
                      help="Number of seconds to run one load test. Optional. Default is 10 seconds.")
    args.add_argument('--step_rate',    "-p", type=int, action="store", dest="step_rate", default=50, nargs='?',
                      help="Number of requests/second to add to each load test. Optional. Default is 50.")
    args.add_argument('--warm_up_rate', "-u", type=int, action="store", dest="warm_up_rate", default=20, nargs='?',
                      help="Number of requests/second to warm up target service. Optional. Default is 20. Set to 0 to skip it.")
    args.add_argument('--warm_up_time', "-w", type=int, action="store", dest="warm_up_time", default=10, nargs='?',
                      help="Number of seconds to warm up target service. Optional. Default is 10 seconds.")
    args.add_argument('--rest_time',    "-r", type=int, action="store", dest="rest_time", default=5, nargs='?',
                      help="Number of seconds to rest between two load runs. Optional. Default is 5 seconds. Set to 0 to skip it.")

    if len(argv) == 1:
        args.print_help()
        return ErrorCode.emptyCommandLineParameters

    given_args = args.parse_args()
    test_run = VegetaLoadTest(given_args.target_file, given_args.failure_threshold,
                              given_args.start_rate, given_args.test_time, given_args.step_rate,
                              given_args.warm_up_rate, given_args.warm_up_time, given_args.rest_time)

    return test_run.execute_tests()


###############################################################################
if __name__ == '__main__':
    sys.exit(main(sys.argv))
