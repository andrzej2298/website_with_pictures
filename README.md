# Website with pictures

This is a toy app written using web technologies 
which enable (horizontal) scalability.

The app enables:
- uploading images
- adding filters to the uploaded images (*Add image*)
- viewing the uploaded images (*All*, *Top 3*)
- liking the uploaded images

The *Top 3* page is cached for one minute.

## Usage

```
docker-compose up --scale web=2 --scale worker=2
```

## Services
Service instances are managed using `docker-compose`.

There are six container images used:
- **Flask** web **server** &mdash; handles the user requests
- **Python worker** connected to the server using `rq`
(a message queue for Python, implemented with Redis) &mdash;
workers asynchronously process and upload the images to the cloud
- **MongoDB** &mdash; the database, stores info about images
- **Redis** &mdash; used for cache and by the message queue
- **Nginx** &mdash; provides round robin load balancing
- **Elasticsearch** and **Kibana** &mdash; log collection and visualization

![demo](static/recording.gif)
