## Delete extra data from doc where extra "doc":{...} was accidentally added.c
```
curl -X POST "localhost:9200/animal-humane-20250919-1900/_update/211812422" -H 'Content-Type: application/json' -d '{"script": "ctx._source.remove(\"doc\")"}'
```
## Update location, status, and visible fields. Everything else will remain the same
```
curl -XPOST 'localhost:9200/animal-humane-20250919-1900/_update/211812422?pretty' -H 'Content-Type:application/json' -d '{"doc":{"location":"","status":"adopted"}}'
```
## Change all "location":[...] fields to "location":".." (preserving the original location)
```
curl -X POST 'localhost:9200/animal-humane-07162025-14h17m/_update_by_query' \
  -H 'Content-Type: application/json' \
  -d '{
    "script": {
      "source": "if (ctx._source.locations != null && ctx._source.locations.size() > 0) { ctx._source.location = ctx._source.locations[0]; ctx._source.remove(\"locations\"); }"
    },
    "query": {
      "exists": { "field": "locations" }
    }
  }'

```
## Update by query
"origin":"Stray" for all docs where id is 211552425

```
curl -XPOST "localhost:9200/animal-humane-*/_update_by_query?pretty" -H "Content-Type: application/json"  -d '{
  "query": {
    "term": {
       "_id": "211761473" 
    }
  },
  "script": {
     "source": "ctx._source.weight_group = \"Medium (25-59)\"","lang": "painless"
  }
}'
Medium (25-59)
curl -XPOST "localhost:9200/animal-humane-*/_update_by_query?pretty" -H "Content-Type: application/json"  -d '{
  "query": {
    "term": {
       "_id": "211510365" 
    }
  },
  "script": {
     "source": "ctx._source.origin = \"City of Las Vegas Animal Care Center\"","lang": "painless"
  }
}'
```
## Update "origin" by query using Painless
```
curl -X POST "localhost:9200/animal-humane-*/_update_by_query" -H 'Content-Type: application/json' -d '{"script": {"source": "ctx._source.origin = params.new_origin","lang": "painless","params": {"new_origin": "ABQ Animal Welfare Department"}},"query": {"bool": {"must": [{"term":{"id":211590452}},{"term":{"origin.keyword":"Unknown"}}]}}}'
```

## Find all docs where "origin" does not exist
```
curl -XGET "localhost:9200/animal-humane-*/_search?pretty" -H "Content-Type: application/json" -d '{"query":{"bool":{"should":[{"term":{"origin.keyword":""}},{"bool":{"must_not":{"exists":{"field":"origin"}}}}]}}}'
```

## List all docs with 'dog' and sorted by _index: 
```
curl -XGET 'localhost:9200/animal-humane*/_search?pretty&size=25' -H 'Content-Type:application/json' -d '{"query":{"match":{"name":"Bronx"}},"sort":[{"_index":{"order":"asc"}}]}'
```


## List all indices where given dog exists, sorted by index (date) in descending order (most recent first)
```
curl -XGET 'localhost:9200/animal-humane-*/_search?pretty&size=1' -H 'Content-Type:application/json' -d '{"query":{"match":{"name":"Luna"}},"sort":[{"_index":{"order":"desc"}}]}'
```

## Aggregation by index
```
curl -XGET 'localhost:9200/animal-humane-07172025-*/_search?pretty&size=1000' -H 'Content-Type:application/json' -d '{"size":0, "aggs":{"dogs_per_day":{"terms":{"field":"name.keyword","size":1000}}}}'
```

## Keyword search 
```
curl -XGET 'localhost:9200/your_index/_search?pretty' -H 'Content-Type: application/json' -d '{"query": {"bool": {"must":[{"wildcard":{"location.keyword":"*Trial Adoption*"} }]}}}'
```
## Push a single dog to Elasticsearch manually
```
curl -XPUT 'http://localhost:9200/animal-humane-07172025-19h00m/_doc/211208121' -H 'Content-Type: application/json' -d '{"id": 211208121,"name": "Thunder","status": "Available","url": "https://new.shelterluv.com/embed/animal/211208121","intake_date": "2025-06-06","birthdate": "2021-06-06","breed": "Shepherd, German","secondary_breed": "Mixed Breed","weight_group": "Large (60-99)","color": "Brown and White","location": "Main Kennel North, Main Campus - MKN-05"}'

```

List names of dogs whose location is not ""
```
curl -XGET 'localhost:9200/animal-humane-*/_search?pretty' -H 'Content-Type: application/json' -d '{"size": 1000, "_source": ["name"], "query": { "bool": { "must_not": [ { "term": { "location.keyword": "" }}]}}}'
```
## Snapshots

1. Update elasticsearch.yml with `path.repo: /Volumes/CRUZER`
2. Snaphot each index with the following, changing the name of the backup, the name of the snapshot and the name of the index as needed
```
curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_22 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250716-1900"}'
```
3. Check the status of the snapshot, modifying the name of the backup and snapshot as needed. The Status field (near the top) 
should read 'SUCCESS'
```
curl -X GET "localhost:9200/_snapshot/animal_humane_backup/snapshot_10/_status?pretty"
```

## Restoring Snapshots
1. Make sure USB is available at /Volumes/CRUZER
2. Edit elasticsearch.yml with path.repo: ["/Volumes/CRUZER"] if it's changed, and restart Elasticsearch
3. Register the Snapshot Repository
```
curl -X PUT "localhost:9200/_snapshot/animal_humane_backup" -H 'Content-Type: application/json' -d'
{
  "type": "fs",
  "settings": {
    "location": "/Volumes/CRUZER"
  }
}'

```
(List snapshots)
`curl -XGET 'localhost:9200/_snapshot?pretty'`

4. List Available Snapshots to see which are available
```
curl -X GET "localhost:9200/_snapshot/animal_humane_backup/_all"
```
or 
```
curl -s "localhost:9200/_cat/snapshots/animal_humane_backup?v"
```

5. Restore the desired snapshot
```
curl -X POST "localhost:9200/_snapshot/animal_humane_backup/snapshot_38/_restore" -H 'Content-Type: application/json' -d' {"indices":"animal-humane-20250719-2151"}'
```



## Reset watermarks
```
curl -X PUT "localhost:9200/_cluster/settings" -H 'Content-Type: application/json' -d '{
  "persistent": {
    "cluster.routing.allocation.disk.watermark.high": "98%",
    "cluster.routing.allocation.disk.watermark.flood_stage": "99%"
  }
}'
```

## Push .csv file to Elasticsearch
```
curl -XPOST "localhost:9200?pretty" -H "Content-Type: application/json" --data-binary @doc.json
```

## Aggregation on animal shelter origins
```
curl -XGET "localhost:9200/animal-humane-*/_search?size=0" -H "Content-Type: application/json" -d '{"size": 0,"aggs": {"shelters": {"terms": { "field": "origin.keyword", "size": 100 },"aggs": {"unique_dogs": {"cardinality":{"field": "id" }}}}}}'
```

## Retrieve the current total counts for Puppies, Seniors, and Adults currently available at the shelter
```
curl -XGET 'localhost:9200/animal-humane-20250817-*/_search?pretty' -H 'Content-Type:application/json' -d '{"query":{"bool":{"must":[{"match":{"status":"Available"}}]}},"aggs":{"age_groups":{"terms":{"field":"age_group.keyword"},"aggs": {"unique_dogs": {"cardinality":{"field": "id"}}}}}}'
```
## Retrieve lats lte 33.0 for id 211462064
```
curl -XGET 'localhost:9200/animal-humane-*/_doc/211462064/_search?pretty' -H 'Content-Type:application/json' -d '{
  "query":{
    "bool":{
      "filter":[{"range":{"latitude":{"gte":32.0,"lte":33.0}}}]
      "must":[{"match":{"id":211462064}}]
    }
  }
}'
```


## List all unique dogs in the last 7 days whose location is not "".
```
curl -XPOST "http://localhost:9200/animal-humane-*/_search?pretty" -H 'Content-Type: application/json' -d' { "size": 0, "query": { "bool": { "filter": [ { "range": { "timestamp": { "gte": "now-7d/d", "lt": "now/d" } } } ], "must_not": [ { "term": { "location": "" } } ] } }, "aggs": { "unique_ids_last_7_days": { "cardinality": { "field": "id" } } } }'

```
## Return count of unique ids in indices
Note: The cardinality aggregation provides an approximate count, but for most practical use cases it is sufficiently accurate, especially if you raise precision_threshold
```
curl -XPOST 'localhost:9200/animal-humane-*/_search?pretty' -H 'Content-Type:application/json' -d '{"size":0,"aggs":{"unique_ids":{"cardinality":{"field":"id","precision_threshold":1000}}}}'
```

## Manually push doc to Elastic
```
curl -XPOST 'localhost:9200/animal-humane-20250810-1500/_doc/208812411?pretty' -H 'Content-Type:application/json' -d '{"name":"Snoopy","location":"Main Kennel North, Main Campus - MKN-07","origin":"Owner Surrender", "status":"Available","url":"https://new.shelterluv.com/embed/animal/208812411","intake_date":"2025-03-11","length_of_stay_days":149,"birthdate":"2021-07-27","age_group":"Adult","breed":"Coonhound","secondary_breed":"","weight_group":"Extra-Large (100+)","color":"Black and Brown","bite_quarantine":0,"returned":5}'
```
## Date Histogram for Adoption Trends Line Chart
```
curl -XGET "localhost:9200/animal-humane-*/_search?size=0" -H 'Content-Type: application/json' -d '{"size": 0,"aggs": {"adoptions_over_time": {"date_histogram": {"field": "date_field","calendar_interval": "day","format":"MM/dd/yyyy","time_zone": "UTC"}}}}'
```
## Update each document with a 'timestamp' field that mirrors the datetime in the index name
```
curl -XPOST "http://localhost:9200/animal-humane-20250709-2020/_update_by_query"  -H 'Content-Type: application/json'  -d '{"script": {"source": "String idx = ctx._index; if (idx.length() >= 27) { String ymd = idx.substring(14,22); String hm = idx.substring(23,27); String ts = ymd.substring(0,4) + \"-\" + ymd.substring(4,6) + \"-\" + ymd.substring(6,8) + \"T\" + hm.substring(0,2) + \":\" + hm.substring(2,4) + \":00Z\"; ctx._source.timestamp = ts; }","lang": "painless"},"query": {"match_all": {}}}'
```

## Date Histogram for number of dogs adopted each day
```
curl -XGET 'localhost:9200/animal-humane-*/_search?pretty&size=100&_source=name' -H 'Content-Type:application/json' -d '{"query":{"match":{"status":"adopted"}},"aggs":{"adoptions":{"date_histogram":{"field":"timestamp","calendar_interval":"day","format":"MM/dd/yyyy","time_zone":"UTC"}}}}'
```

## Find the name of the dog who has been at the shelter the longest
```
curl -XGET "http://localhost:9200/animal-humane-*/_search?pretty"   -H 'Content-Type: application/json'   -d '{"size": 1,"_source": ["name", "length_of_stay_days"],"query":{"bool":{"must_not":[{"term":{"status": "adopted"}}]}},"sort":[{"length_of_stay_days":{"order":"desc"}}]}'
```
## Return the number of Seniors, Adults and Puppies (unique ids only)
```
curl -XGET 'localhost:9200/animal-humane-*/_search?pretty' -H 'Content-Type:application/json' -d '{"aggs":{"groups":{"terms":{"field":"age_group.keyword"},"aggs":{"unique_dogs":{"cardinality":{"field":"id","precision_threshold":40000}}}}}}'
```

## Return Seniors, Adults, and puppies by week that have been adopted
```
index_name = "your-index-pattern-here"  # e.g., "animal-humane-*"

query_body = {
    "size": 0,
    "query": {
        "term": {
            "status.keyword": "adopted"
        }
    },
    "aggs": {
        "weekly": {
            "date_histogram": {
                "field": "timestamp",
                "calendar_interval": "week",
                "format": "MM/dd/yyyy",
                "time_zone": "UTC"  # adjust time zone as needed
            },
            "aggs": {
                "by_age_group": {
                    "terms": {
                        "field": "age_group.keyword",
                        "size": 10  # assuming limited number of age groups
                    },
                    "aggs": {
                        "unique_dogs": {
                            "cardinality": {
                                "field": "id.keyword",
                                "precision_threshold": 10000  # increase if you expect many unique dogs
                            }
                        }
                    }
                }
            }
        }
    }
}

# Example to execute and print results
response = es.search(index=index_name, body=query_body)

# Transform the aggregation result into desired frontend format:
# [{ week: "MM/dd/yyyy", Puppy: count, Adult: count, Senior: count }, ...]
weekly_buckets = response['aggregations']['weekly']['buckets']
result = []

for week_bucket in weekly_buckets:
    week_str = week_bucket['key_as_string']
    age_buckets = week_bucket['by_age_group']['buckets']
    week_data = {"week": week_str}
    # Initialize counts to zero for all age groups if needed
    for age_group in ["Puppy", "Adult", "Senior"]:
        week_data[age_group] = 0
    # Fill in the counts from the buckets
    for age_bucket in age_buckets:
        age_group = age_bucket['key']
        count = age_bucket['unique_dogs']['value']
        week_data[age_group] = count
    result.append(week_data)

# 'result' now holds data in the correct format to return from your API
print(result)

## Sort a csv file by the id (column 2)
`sort -t',' -k2,2n dogs.csv > dogs_sorted.csv`

## Update origin from ABQ Welfare Department to ABQ Animal Welfare Department
```
curl -XPOST "localhost:9200/animal-humane-*/_update_by_query" -H 'Content-Type: application/json' -d '{"script": {"source": "ctx._source.origin = params.new_origin","lang": "painless","params": {"new_origin": "ABQ Animal Welfare Department"}},"query": {"term": {"origin.keyword": "ABQ Welfare Department"}}}'
```
## Update "latitude":[35.2378] to "latitude":35.2378.
```
curl -XPOST "http://localhost:9200/animal-humane-20250813-1100/_update_by_query?pretty" -H 'Content-Type: application/json' -d '{"script":{"source":"if (ctx._source.latitude instanceof List) { ctx._source.latitude = ctx._source.latitude[0] }","lang":"painless"},"query":{"exists":{"field":"latitude"}}}'
```
## Update multiple fields when using update_by_query

```
curl -XPOST 'localhost:9200/animal-humane-*/_update_by_query?pretty' -H 'Content-Type: application/json' -d '{
  "script": {
    "source": "ctx._source.latitude = params.new_latitude; ctx._source.longitude = params.new_longitude; ctx._source.origin=params.new_origin",
    "lang": "painless",
    "params": {
        "new_latitude": 35.0561,
        "new_longitude": -106.6646,
        "new_origin":"Bernalillo County Animal Care"
    }
  },
  "query": {
    "term": { 
      "id":211812176
    }
  }
}'
```
{"name":"Elton","id":,"origin":"Bernalillo County Animal Care","bite_quarantine":0,"returned":0,"latitude":35.0561,"longitude":-106.6646}

## Remove latitude and longitude when they are both equal to 0
```
curl -XPOST "http://localhost:9200/animal-humane-20250813-1100/_update_by_query?pretty" -H 'Content-Type: application/json' -d '{ "script": { "source": "if (ctx._source.containsKey(\"latitude\") && ctx._source.latitude == 0) { ctx._source.remove(\"latitude\"); } if (ctx._source.containsKey(\"longitude\") && ctx._source.longitude == 0) { ctx._source.remove(\"longitude\"); }", "lang": "painless" }, "query": { "bool": { "should": [ { "term": { "latitude": 0 } }, { "term": { "longitude": 0 } } ] } } }'

```
## Update all docs where "origin":"ABQ Animal Welfare Department" with the relevant lat/long
```
curl -XPOST "http://localhost:9200/animal-humane-*/_update_by_query?pretty" -H 'Content-Type: application/json' -d '{ "script": { "source": "ctx._source.latitude = 35.1102; ctx._source.longitude = -106.5823;", "lang": "painless" }, "query": { "term": { "origin.keyword": "ABQ Animal Welfare Department" } } }'
```

## Identify percentage of dogs adopted from each origin
```
curl -XGET 'localhost:9200/animal-humane-*/_search?pretty' -H 'Content-Type:application/json' -d '{
  "size": 0,
  "aggs": {
    "origins": {
      "terms": {
        "field": "origin.keyword",
        "size": 10000
      },
      "aggs": {
        "total_count": {
          "cardinality": {
            "field": "id",
            "precision_threshold": 10000
          }
        },
        "adopted_count": {
          "filter": {
            "term": {
              "status.keyword": "adopted"
            }
          },
          "aggs": {
            "unique_adopted": {
              "cardinality": {
                "field": "id",
                "precision_threshold": 10000
              }
            }
          }
        },
        "adoption_rate": {
          "bucket_script": {
            "buckets_path": {
              "adopted": "adopted_count>unique_adopted",
              "total": "total_count"
            },
            "script": "params.total > 0 ? (params.adopted / params.total) * 100 : 0"
          }
        }
      }
    }
  }
}'

```

## Retrieve the names of the 2 dogs from Torrance County
```
curl -XGET "localhost:9200/animal-humane-*/_search?pretty" -H 'Content-Type: application/json' -d '{
    "size": 0,
    "query": {
      "term": {
        "origin.keyword": "Torrance County Animal Shelter"
      }
    },
    "aggs": {
      "unique_dogs": {
        "terms": {
          "field": "id",
          "size": 2
        },
        "aggs": {
          "dog_name": {
            "terms": {
              "field": "name.keyword",
              "size": 1
            }
          }
        }
      }
    }
  }'

```

## Update mapping

```
curl -XPUT 'localhost:9200/animal-humane-20250818-0845/_mapping?pretty' -H 'Content-Type:application/json' -d '{
  "properties": {
    "latitude": {
      "type": "float",
      "fields": {
        "lat_double":{
           "type":"double"
        }
      } 
   }
}'
```

## Reindex with new mapping
```
curl -XPOST animal-humane-20250818-0845/_update_by_query?wait_for_completion=false' -H 'Content-Type:application/json' -d '{
  "query": { 
    "bool": { 
      "must": { 
        "exists": { "field": "user_ip" } 
      }, 
      "must_not": { "exists": { "field": "user_ip.ip" } } 
    }
  } 
}'
```

## Update by query
```
curl -XPOST "localhost:9200/animal-humane-20250818-0845/_update_by_query?pretty" -H "Content-Type: application/json"  -d '{
  "query": {
    "term": {
       "_id": "211462064"
    }
  },
  "script": {
     "source": "ctx._source.lat_double = 33.331749","lang": "painless"
  }
}'
```
## Print total number of dogs who have been 'Stray'
```
curl -XGET 'localhost:9200/animal-humane-*/_search?pretty&size=0' -H 'Content-Type:application/json' -d '{"query":{"match":{"origin":"Stray"}},"aggs":{"unique_ids":{"cardinality":{"field":"id"}}}}'
```

## Print total number of dogs who have been surrendered by the owner
```
curl -XGET 'localhost:9200/animal-humane-*/_search?pretty&size=0' -H 'Content-Type:application/json' -d '{"query":{"match":{"origin":"Owner Surrender"}},"aggs":{"unique_ids":{"cardinality":{"field":"id"}}}}'
```

## Print number of dogs that have spent some time in a foster home
```
curl -XGET 'localhost:9200/animal-humane-*/_search?pretty&size=0' -H 'Content-Type:application/json' -d '{"query":{"match":{"location":"Foster Home"}},"aggs":{"unique_ids":{"cardinality":{"field":"id"}}}}'
```

## Find the dog that has been at AH the longest
```
curl -XGET 'localhost:9200/animal-humane-*/_search?pretty&_source=name,length_of_stay_days&size=1' -H 'Content-Type:application/json' -d '{"query":{"match":{"status":"available"}},"sort":[{"_index":{"order":"desc"}},{"length_of_stay_days":{"order":"desc"}}]}'
```
## update_by_query,  weight_group
Categories:
Small (0-24)
Medium (25-59)
Large (60-99)
Extra-Large (100+)
```
curl -XPOST "localhost:9200/animal-humane-*/_update_by_query?pretty" -H 'Content-Type: application/json' -d '{"script": {"source": "ctx._source.weight_group = params.new_weight_group","lang": "painless","params": {"new_weight_group": "Medium (25-59"}},"query": {"match": {"id":210061291}}}'
```

## Status by month
```
curl -X POST "http://localhost:9200/animal-humane-*/_search?pretty" -H 'Content-Type: application/json' -d '{
  "size": 0,
  "aggs": {
    "months": {
      "date_histogram": {
        "field": "timestamp",
        "calendar_interval": "month"
      },
      "aggs": {
        "status_categories": {
          "terms": {
            "field": "status.keyword"
          },"aggs":{"uids":{"terms":{"field":"id","size":500}}}
        }
      }
    }
  }
}'
```

### Delete keys from document
```
curl -XPOST 'localhost:9200/animal-humane-20250716-1103/_update/211159999?pretty' -H 'Content-Type:application/json' -d '{
     "script": {
       "source": "ctx._source.remove(\"primary_color\");ctx._source.remove(\"secondary_color\")"
     }
   }'
```
curl -XGET 'localhost:9200/animal-humane-*/_search?pretty' -H 'Content-Type:application/json' -d '{
  "size": 0,
  "query": {
    "range": {
      "timestamp": {
        "lt": "now/w"
      }
    }
  },
  "aggs": {
    "dogs_per_week": {
      "date_histogram": {
        "field": "timestamp",
        "calendar_interval": "week",
        "format": "yyyy-MM-dd",
        "time_zone": "UTC"
      }
    }
  }
}'

curl -XGET 'localhost:9200/animal-humane-*/_search?pretty' -H 'Content-Type:application/json' -d '{"size": 0, "query":{"range":{"timestamp":{"lt":"now/d"}}}, "aggs": { "weeks": { "date_histogram": { "field": "timestamp", "calendar_interval": "week", "format": "yyyy-MM-dd", "time_zone": "UTC" }, "aggs":{ "id_filter":{"filter":{"term":{ "id": "211761683" }}}}}}}'

