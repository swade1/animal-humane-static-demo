from elasticsearch import Elasticsearch

es2 = Elasticsearch("http://localhost:9200")
repo_name = "usb_snapshot_repo"

repo_settings = {
  "type":"fs",
  "settings": {
    "location":"/Volumes/ElasticUSB/elasticsearch_repo",
    "compress":True
  }
}

es2.snapshot.create_repository(name=repo_name, body=repo_settings)
print("Snapshot repository registered on laptop 2.")
