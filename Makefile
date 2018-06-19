# Required Variables
bearer_token=BEARER_TOKEN_TO_ACCESS_PROMETHEUS_HOST
prometheus_url=http://prometheus_host.com

block_storage_access_key=MY_ACCESS_KEY
block_storage_secret_key=MY_SECRET_KEY
block_storage_bucket_name=MY_BUCKET_NAME
block_storage_endpoint_url=http://storage_endpoint.com:8080/

# Optional Variables
cron_schedule=0 1 * * *
oc_single_job_app_name=scrape-prometheus
oc_cronjob_app_name=scrape-prometheus-cronjob-test
docker_app_name=scrape_prometheus
oc_image_name=scrape-prometheus

docker_build:
	docker build -t ${docker_app_name} .

docker_test:
	docker run ${docker_app_name}

oc_job_run:
	oc new-app --file=./scrape-prometheus-image-build-template.yaml --param APPLICATION_NAME="${oc_single_job_app_name}"
	sleep 20s	# wait for the image to build
	oc new-app --file=./scrape-prometheus-job-template.yaml --param APPLICATION_NAME="${oc_single_job_app_name}" \
			--param URL="${prometheus_url}" \
			--param BEARER_TOKEN="${bearer_token}" \
			--param BOTO_ACCESS_KEY="${block_storage_access_key}" \
			--param BOTO_SECRET_KEY="${block_storage_secret_key}" \
			--param BOTO_OBJECT_STORE="${block_storage_bucket_name}" \
			--param BOTO_STORE_ENDPOINT="${block_storage_endpoint_url}"

docker_run:
	docker run -ti --rm \
	   --env "BEARER_TOKEN=${bearer_token}" \
	   --env "PROM_BACKUP_ALL=true" \
	   --env "URL=${prometheus_url}" \
		 --env BOTO_ACCESS_KEY="${block_storage_access_key}" \
		 --env BOTO_SECRET_KEY="${block_storage_secret_key}" \
		 --env BOTO_OBJECT_STORE="${block_storage_bucket_name}" \
		 --env BOTO_STORE_ENDPOINT="${block_storage_endpoint_url}" \
	   scrape_prometheus:latest

oc_add_template:
	oc create -f ./scrape-prometheus-template.yaml
	oc replace -f ./scrape-prometheus-template.yaml

oc_cron_job_run:
	oc new-app --file=./scrape-prometheus-cronjob-template.yaml --param APPLICATION_NAME="${oc_cronjob_app_name}" \
	  	--param URL="${prometheus_url}" \
	  	--param SCHEDULE="${cron_schedule}" \
	  	--param BEARER_TOKEN="${bearer_token}" \
			--param BOTO_ACCESS_KEY="${block_storage_access_key}" \
			--param BOTO_SECRET_KEY="${block_storage_secret_key}" \
			--param BOTO_OBJECT_STORE="${block_storage_bucket_name}" \
			--param BOTO_STORE_ENDPOINT="${block_storage_endpoint_url}" \

run_list_metrics:
	BEARER_TOKEN=${bearer_token} \
	URL=${prometheus_url} \
	BOTO_ACCESS_KEY=${block_storage_access_key} \
	BOTO_SECRET_KEY=${block_storage_secret_key} \
	BOTO_OBJECT_STORE=${block_storage_bucket_name} \
	BOTO_STORE_ENDPOINT=${block_storage_endpoint_url} \
	python3 ./app.py --list-metrics

run_backup_all_metrics:
	BEARER_TOKEN=${bearer_token} \
	URL=${prometheus_url} \
	BOTO_ACCESS_KEY=${block_storage_access_key} \
	BOTO_SECRET_KEY=${block_storage_secret_key} \
	BOTO_OBJECT_STORE=${block_storage_bucket_name} \
	BOTO_STORE_ENDPOINT=${block_storage_endpoint_url} \
	python3 ./app.py --backup-all

oc_job_delete:
	oc delete all -l app=${oc_single_job_app_name}

oc_cronjob_delete:
	oc delete all -l app=${oc_cronjob_app_name}
