<!-- # scrape_prometheus
Functions to scrape data from Prometheus and maybe be able to store to an object storage (like CEPH) -->

# Scrape Prometheus
This python application has been written to scrape data from Prometheus and store it to a long term block storage like CEPH or S3 as JSON objects. So the data can be used and processed at a later time more easily. It also contains templates to be run as a CronJob or as a single one time pod on OpenShift.

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
This will list all the metrics that are stored on the Prometheus host.

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
                        values are 1m, 1h, 1d default: 1h

```

## Deploying on OpenShift

* ### Deploying a single time running pod:
  In the Makefile set up the required variables, and then run the following command:
```
make oc_job_run
```
This will run a pod on openshift which will backup a day's (24 Hours) of data for all the metrics from the specified Prometheus Host to the block storage.

* ### Deploying a scheduled cronjob:
  In the Makefile set up the required variables, and also set the cron_schedule variable to your desired frequency to run the application, (if you need help with this variable see https://en.wikipedia.org/wiki/Cron), then run the following command:
  ```
  make oc_cron_job_run
  ```
  This will schedule a cronjob on openshift that will backup a day's (24 Hours) data for all the metrics from the specified prometheus host to the given block storage service.

## Built With

* [Dropwizard](http://www.dropwizard.io/1.0.2/docs/) - The web framework used
* [Maven](https://maven.apache.org/) - Dependency Management
* [ROME](https://rometools.github.io/rome/) - Used to generate RSS Feeds

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/your/project/tags).

## Authors

* **Billie Thompson** - *Initial work* - [PurpleBooth](https://github.com/PurpleBooth)

See also the list of [contributors](https://github.com/your/project/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone whose code was used
* Inspiration
* etc
