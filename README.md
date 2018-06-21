# Scrape Prometheus
This python application has been written to scrape data from Prometheus and store it to a long term block storage like CEPH or S3 as json.bz2 objects. So the data can be used and processed at a later time more easily. It also contains templates to be run as a scheduled cronjob or as a single one time pod on OpenShift.

## Getting Started



### Installing prerequisites

To run this application you will need to install several libraries listed in the requirements.txt.

To install all the dependencies at once, run the following command when inside the directory:
```
pip install -r requirements.txt
```
After all the prequisites have been installed, open the Makefile and you will see a list of required and optional variables in the beginning.
The required variables will be used to communicate with the Prometheus and Storage end points.

Populating the Makefile is the most important step, as you can use this run the application on OpenShift, Docker or your local machine.

### Running on a local machine

After setting up the credentials in your Makefile, to test if Prometheus credentials are correct, run the following command:
```
make run_list_metrics
```
This will list all the metrics that are stored on the Prometheus host. If it doesn't check your credentials.

Next, to backup the previous day's metrics data to a long term block storage, run the following command:
```
make run_backup_all_metrics
```
## Running on Docker
After populating all the required variables, set the name for your docker app by changing the docker_app_name variable. Then run the following command to build the docker image.
```
make docker_build
```
This command uses the Dockerfile included in the repository to build an image. So you can use it to customize how the image is built.

Run the following command to test if the docker image is functional:
```
make docker_test
```
Your output should be something like below:
```
usage: app.py [-h] [--day DAY] [--url URL] [--token TOKEN] [--backup-all]
              [--list-metrics] [--chunk-size CHUNK_SIZE]
              [--stored-data-range STORED_DATA_RANGE] [--debug] [--replace]
              [metric [metric ...]]

Backup Prometheus metrics

positional arguments:
  metric                Name of the metric, e.g. ALERTS - or --backup-all

optional arguments:
  -h, --help            show this help message and exit
  --day DAY             the day to backup in YYYYMMDD (defaults to previous
                        day)
  --url URL             URL of the prometheus server default:
                        https://prometheus-openshift-devops-monitor.1b7d.free-
                        stg.openshiftapps.com
  --token TOKEN         Bearer token for prometheus
  --backup-all          Backup all metrics
  --list-metrics        List metrics from prometheus
  --chunk-size CHUNK_SIZE
                        Size of the chunk downloaded at an instance. Accepted
                        values are 30m, 1h, 6h, 12h, 1d default: 1h. This
                        value cannot be bigger than stored-data-range.
  --stored-data-range STORED_DATA_RANGE
                        Size of the data stored to the storage endpoint. For
                        example, 6h will divide the 24 hour data in 4 parts of
                        6 hours. Accepted values are 30m, 1h, 6h, 12h, 1d
                        default: 6h
  --debug               Enable Debug Mode
  --replace             Replace existing file with the current

```
If the docker image is functional, you can run the following command:
```
make docker_run
```
and this will start backing up all of your metrics.

## Deploying on OpenShift

* ### Deploying a single time running pod:
  In the Makefile set up the required variables, and then run the following command:
```
make oc_build_image
```
  This will create an image for this application on openshift, which you can use with different sets of credentials.
  Then run:
```
make oc_run_job
```
This will run a pod on openshift which will backup a day's (24 Hours) of data for all the metrics from the specified Prometheus Host to the block storage.

* ### Deploying a scheduled cronjob:
  In the Makefile set up the required variables, and also set the cron_schedule variable to your desired frequency to run the application, (if you need help with this variable see https://en.wikipedia.org/wiki/Cron), then run the following command:
  ```
  make oc_cron_job_run
  ```
  This will schedule a cronjob on openshift that will backup a day's (24 Hours) data for all the metrics from the specified prometheus host to the given block storage service.

## Built With

* [Requests](http://docs.python-requests.org/en/master/) - HTTP Library for python
* [Boto3](https://boto3.readthedocs.io/en/latest/reference/core/session.html) - AWS sdk for python
