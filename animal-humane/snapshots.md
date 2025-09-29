Register the snapshot registry in the new cluster (the new instance on ElasticUSB)
```
curl -X PUT "localhost:9200/_snapshot/usb_repo" -H "Content-Type: application/json" -d '{
  "type": "fs",
  "settings": {
    "location": "/Volumes/CRUZER",
    "readonly": true
  }
}'
```

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_2 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250714-1034"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_3 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250714-1134"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_4 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250714-1209"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_5 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250714-1213"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_6 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250714-1411"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_7 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250714-1422"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_8 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250714-1429"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_9 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250714-1500"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_10 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250714-1900"}'

**July 15**

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_11 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250715-0845"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_12 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250715-0937"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_13 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250715-0944"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_14 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250715-1334"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_15 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250715-1500"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_16 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250715-2050"}'

**July 16** 
curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_17 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250716-1103"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_18 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250716-1417"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_19 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250716-1427"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_20 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250716-1500"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_21 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250716-1514"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_22 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250716-1900"}'

**July 17** 
curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_23 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250717-0852"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_24 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250717-1133"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_25 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250717-1215"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_26 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250717-1351"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_27 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250717-1500"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_28 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250717-1656"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_29 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250717-1900"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_30 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250718-0945"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_31 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250718-1616"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_32 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250718-1900"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_33 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250719-0845"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_34 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250719-1150"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_35 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250719-1500"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_36 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250719-1705"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_37 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250719-1900"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_38 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250719-2151"}'

(new..........)

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_39 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250720-0845"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_40 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250720-1003"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_41 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250720-1500"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_42 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250720-1900"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_43 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250720-2038"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_44 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250721-0849"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_45 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250721-0945"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_46 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250721-1532"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_47 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250721-1900"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_48 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250722-0845"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_49 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250722-0925"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_50 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250722-1022"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_51 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250722-1051"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_52 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250722-1531"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_53 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250723-1415"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_54 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250723-1424"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_55 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250723-1500"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_56 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250723-1717"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_57 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250723-1900"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_58 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250724-0845"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_59 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250724-0959"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_60 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250724-1210"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_61 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250724-1409"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_62 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250724-1500"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_63 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250724-1657"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_64 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250724-1900"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_65 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250725-0911"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_66 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250725-1651"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_67 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250725-1900"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_68 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250726-0859"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_69 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250727-0948"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_70 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250727-1010"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_71 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250727-1100"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_72 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250727-1557"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_73 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250727-1900"}'

(I accidentally overwrote snapshot_74 which was originally animal-humane-20250727-2033. That index is in the elasticsearch-9.0.4 instance on ElasticUSB)

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_74 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250728-0845"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_75 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250728-1100"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_76 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250728-1300"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_77 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250728-1500"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_78 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250728-1700"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_79 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250728-1900"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_80 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250729-0845"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_81 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250729-1104"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_82 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250729-1300"}'

(no 3pm index was generated)

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_83 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250729-1700"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_84 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250730-0845"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_85 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250730-1100"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_86 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250730-1504"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_87 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250730-1700"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_88 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250730-1900"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_89 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250731-0845"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_90 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250731-1100"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_91 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250731-1300"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_92 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250731-1500"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_93 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250731-1700"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_94 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250731-1900"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_95 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250801-0852"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_96 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250801-1100"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_97 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250801-1500"}'

curl -XPUT http://localhost:9200/_snapshot/animal_humane_backup/snapshot_98 -H 'Content-Type: application/json' -d '{"indices": "animal-humane-20250801-1900"}'

Force recent changes to be written to disk before creating a snapshot to insure the document updates are included in the snapshot.
curl -XPOST "http://localhost:9200/index_name/_refresh"





Restore snapshot
curl -XPOST 'localhost:9200/_snapshot/usb_repo/snapshot_89/_restore?pretty' -H 'Content-Type:application/json' -d '{"indices":"*","ignore_unavailable":true,"include_global_state":true}'


Elasticsearch.yml content

path.repo on ElasticUSB (elasticsearch-9.0.4, there is no elasticsearch_repo directory so this probably isn't needed)
path.repo: ["/Volumes/CRUZER", "/Volumes/CRUZER/*", "/Volumes/ElasticUSB/elasticsearch_repo"]

path.repo on laptop (elasticsearch-9.0.3)
`path.repo: ["/Volumes/CRUZER"]`

Verify Snapshot (status field should say "SUCCESS")
curl -X GET "localhost:9200/_snapshot/animal_humane_backup/snapshot_10/_status?pretty"


