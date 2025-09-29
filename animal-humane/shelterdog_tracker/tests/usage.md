## **Run all tests from the shelterdog_project/ directory**
```
python3 -m unittest discover -s shelterdog_tracker/tests
```

## Run a specific test file
```
python3 -m unittest shelterdog_tracker.tests.test_elasticsearch_handler
```

## To see more detailed output
```
python3 -m unittest -v shelterdog_tracker.tests.test_elasticsearch_handler
```
## or
```
python3 -m unittest discover -s shelterdog_tracker/tests -v
```


