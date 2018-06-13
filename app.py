# http://jamesthom.as/blog/2017/04/27/python-packages-in-openwhisk/
import argparse
import bz2
from urllib.parse import urlparse
import boto3
import datetime
from time import sleep

import botocore
import requests
import json
import os
# requests.disable_warnings()
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
# Defining some macros
DATA_CHUNK_SIZE = 3600 # For 1 hour chunk size
NET_DATA_SIZE = 3600 * 24 # To get the data for the past 24 hours
MAX_REQUEST_RETRIES = 5
DATA_CHUNK_SIZE_STR = {
    60 : '1m',
    3600 : '1h',
    86400 : '1d'}
DATA_CHUNK_SIZE_LIST = {
    '1m' : 60,
    '1h' : 3600,
    '1d' : 86400}

CONNECTION_RETRY_WAIT_TIME = 1 # Time to wait before a retry in case of a connection error
# TOTAL_ERRORS = 0    # Count total connection errors after retries

# TODO: don't try to reconnect for each metric if initial connection to endpoint fails

class PrometheusBackup:
    def __init__(self, url='', end_time=None, token=None):
        self.headers = { 'Authorization': "bearer {}".format(token) }
        self.url = url
        self.prometheus_host = urlparse(self.url).netloc
        self._all_metrics = None
        self.connection_errors_count = 0 # Count total connection errors after retries


        if end_time:
            end_time = str(end_time)
        else:
            end_time = (datetime.date.today()-datetime.timedelta(1)).strftime("%Y%m%d") # default to previous day

        # parse 20171231 into timestamp
        if len(end_time) == 8:
            end_time = "{} 23:59:59".format(end_time) # we repeat every 24H and get previous day's data
            end_time = datetime.datetime.strptime(end_time, "%Y%m%d %H:%M:%S").timestamp()

        self.end_time = datetime.datetime.fromtimestamp(int(end_time))
        self.start_time = self.end_time - datetime.timedelta(minutes=1440)

        self.boto_settings = {
            'access_key': os.getenv('BOTO_ACCESS_KEY'),
            'secret_key': os.getenv('BOTO_SECRET_KEY'),
            'object_store': os.getenv('BOTO_OBJECT_STORE'),
            'object_store_endpoint': os.getenv('BOTO_STORE_ENDPOINT')
        }
        # print(self.boto_settings)

    def store_metric_values(self, name, values):
        '''
        Function to store metrics to ceph
        '''
        if not values:
            return "No values for {}".format(name)
        # Create a session with CEPH (or any black storage) storage with the stored credentials
        session = boto3.Session(
            aws_access_key_id=self.boto_settings['access_key'],
            aws_secret_access_key=self.boto_settings['secret_key']
        )

        s3 = session.resource('s3',
                              endpoint_url=self.boto_settings['object_store_endpoint'],
                              verify=False)

        object_path = self.metric_filename(name)
        payload = bz2.compress(values.encode('utf-8'))
        rv = s3.meta.client.put_object(Body=payload,
                                       Bucket=self.boto_settings['object_store'],
                                       Key=object_path)
        if rv['ResponseMetadata']['HTTPStatusCode'] == 200:
            return object_path
        else:
            return str(rv)

    def metric_filename(self, name):
        # Adds a timestamp to the filename before it is stored in ceph
        timestamp = self.end_time.strftime("%Y%m%d")
        object_path = self.prometheus_host + '/' + name + '/' + timestamp + '.json.bz2'
        return object_path

    def all_metrics(self):
        if not self._all_metrics:
            response = requests.get('{0}/api/v1/label/__name__/values'.format(self.url),
                                    verify=False, # Disable ssl certificate verification temporarily
                                    headers=self.headers)
            # print("Headers -> ",self.headers)
            # print("URL => ", response.url)
            if response.status_code == 200:
                self._all_metrics = response.json()['data']
            else:
                raise Exception("HTTP Status Code {} {} ({})".format(
                    response.status_code,
                    requests.status_codes._codes[response.status_code][0],
                    response.content
                ))
        return self._all_metrics

    def get_metric(self, name):
        if not name in self.all_metrics():
            raise Exception("{} is not a valid metric".format(name))
        else:
            print("Metric is valid.")
        if DATA_CHUNK_SIZE > NET_DATA_SIZE :
            print("Invalid Chunk Size")
            exit(1)

        num_chunks = int(NET_DATA_SIZE/DATA_CHUNK_SIZE) # Calculate the number of chunks using total data size and chunk size.
        # print(num_chunks)
        print("Getting metric from Prometheus")
        metrics = self.get_metrics_from_prom(name, num_chunks)
        if metrics:
            return metrics

    def get_metrics_from_prom(self, name, chunks):
        if not name in self.all_metrics():
            raise Exception("{} is not a valid metric".format(name))

        # start = self.start_time.timestamp()
        end_timestamp = self.end_time.timestamp()
        chunk_size = DATA_CHUNK_SIZE
        start = end_timestamp - NET_DATA_SIZE + chunk_size
        data = []
        for i in range(chunks):
            print("Getting chunk: ", i)
            response = requests.get('{0}/api/v1/query'.format(self.url),    # using the query API to get raw data
                                    params={'query': name+'['+DATA_CHUNK_SIZE_STR[chunk_size]+']',
                                            'time': start
                                            },
                                    verify=False, # Disable ssl certificate verification temporarily
                                    headers=self.headers)
            # print(response.url)
            tries = 0
            while tries < MAX_REQUEST_RETRIES:  # Retry code in case of errors
                tries+=1
                print("Try Count: ",tries)
                if response.status_code == 200:
                    data += response.json()['data']['result']
                    tries = MAX_REQUEST_RETRIES
                elif response.status_code == 504:
                    if tries >= MAX_REQUEST_RETRIES:
                        self.connection_errors_count+=1
                        return False
                    else:
                        print("Retry Count: ",tries)
                        sleep(CONNECTION_RETRY_WAIT_TIME)    # Wait for a second before making a new request
                else:
                    if tries >= MAX_REQUEST_RETRIES:
                        self.connection_errors_count+=1
                        raise Exception("HTTP Status Code {} {} ({})".format(
                            response.status_code,
                            requests.status_codes._codes[response.status_code][0],
                            response.content
                        ))
                    else:
                        sleep(CONNECTION_RETRY_WAIT_TIME)

            start += chunk_size

        return(json.dumps(data))

    def metric_already_stored(self, metric):
        session = boto3.Session(
            aws_access_key_id=self.boto_settings['access_key'],
            aws_secret_access_key=self.boto_settings['secret_key']
        )
        s3 = session.resource('s3',
                              endpoint_url=self.boto_settings['object_store_endpoint'],
                              verify=False)

        object_path = self.metric_filename(metric)
        try:
            s3.Object(self.boto_settings['object_store'], object_path).load()
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                return False
            else:
                raise
        else:
            return True

if __name__ == '__main__':
    # parse the required input arguments, if no arguments print help
    parser = argparse.ArgumentParser(description='Backup Prometheus metrics')
    parser.add_argument('--day', type=int,
                        help='the day to backup in YYYYMMDD (defaults to previous day)')
    parser.add_argument('--url', type=str, default="https://prometheus-openshift-devops-monitor.1b7d.free-stg.openshiftapps.com",
                        help="URL of the prometheus server default: %(default)s")
    parser.add_argument('--token', type=str,
                        help="Bearer token for prometheus")
    parser.add_argument('--backup-all', action='store_true',
                        help="Backup all metrics")
    parser.add_argument('--list-metrics', action='store_true',
                        help="List metrics from prometheus")
    parser.add_argument('metric', nargs='*',
                        help='Name of the metric, e.g. ALERTS - or --backup-all')
    parser.add_argument('--chunk-size', type=str, default='1m',
                        help='Size of the chunk downloaded at an instance. Accepted values are 1m, 1h, 1d default: %(default)s')

    args = parser.parse_args()


    # override from ENV
    backup_all = os.getenv('PROM_BACKUP_ALL', args.backup_all)
    token = os.getenv('BEARER_TOKEN', args.token)
    # print("Token => ",token)
    url = os.getenv('URL', args.url)

    p = PrometheusBackup(url=url, end_time=args.day, token=token)

    if args.chunk_size not in DATA_CHUNK_SIZE_LIST:
        print("Invalid Chunk Size.", args.chunk_size)
        exit()

    if args.list_metrics:
        metrics = p.all_metrics()
        print(metrics)
        exit()

    metrics = []
    if backup_all:
        metrics = p.all_metrics()
    else:
        metrics = args.metric

    # check for metrics in arguments
    if not metrics:
        parser.print_help()
        exit(1)


    for metric in metrics:
        try:
            print(metric)
            if p.metric_already_stored(metric):
                print("... already downloaded")
                continue
            # print("scraping metric: ",metric)
            values = p.get_metric(metric)
            print("...metric collected")
            # print("Metrics-> ",metric,json.dumps(json.loads(values), indent = 4, sort_keys = True))

            print(p.store_metric_values(metric, values))
        except Exception as ex:
            print("Error: {}".format(ex))
    print("Total number of connection errors: ", p.connection_errors_count)
