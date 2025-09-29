

**Issues**: 
* Charmy (211510059) did not get returned by diff.py code as in a trial adoption
* Questions - when do 'Adopted Dogs' drop off? Answer: When their location and status fields are updated.
* Updates are not automatically made. I'm still doing them manually based on the info returned from diffs script.
* I missed Smooch all together. She was never captured so I don't have a doc for her (https://new.shelterluv.com/embed/animal/211530732). Intake was 7/25 and she's gone on 7/26. As long as I'm saving the url and I have captured the transfer info  at the shelter, I shouldn't be missing anyone. She needs to be added manually.
* Milo was returned on the 22nd but has not been back on the site yet since he's in BMOD.
* Increment 'returned' field if dog returns after being absent for awhile
* Increment 'returned' field if dog is new and id number is in the 208... range.
* Possible AI idea: Increment 'returned' field if pictures include a 'baby' photo.
* Check the archived_data directory to verify that all those docs are in the ElasticUSB Elastisearch instance
* The snapshot storage on CRUZER makes me a little itchy since everything is saved in the main directory in multiple files. Figure out how to organize the files better and what changes need to be made to elasticsearch.yml.
* Figure out how to save AH_adoptables somewhere other than in a text file.
* Organize my notes better. Queries and commands that should be in useful_queries are spread all over the place, etc.
* I've noticed that updates I make on my laptop are not part of the snapshots. Dogs I've marked as adopted in my laptop elasticsearch instance are not marked as adopted on the ElasticUSB instance. (??)

**TODOs** and Ideas for my AH App

* Output a table showing all dogs at shelter a month at a time

| July 20 | July 21 | July 22 | July 23 | July 24 |
| Jasper  |         | Jasper  |         |         | (indicates adoption, return, and re-adoption)
| Thunder | Thunder | Thunder | Thunder | Thunder | (current resident)
|         |         | Ahsoka  | Ashoka  | Ahsoka  | (new resident)


Corner case: A dog gets listed and adopted before a second document is created. Thus, dog only appears once. I'm not sure my code picks up that dog as adopted. I might have to search for ids that appear only once.  A dog that gets listed and adopted between runs will not be captured at all. 

* Diffing of two indices only provided Athena's id and not Leela's although they were both new to the same index.
  * Can the "unlisted" results skip (or note) the dogs whose locations are now ""? 
* 


