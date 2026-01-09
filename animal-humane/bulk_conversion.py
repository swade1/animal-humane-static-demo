
# ...existing code before...
import json
import sys

def convert_to_bulk(input_path, output_path, index_name):
    with open(input_path, 'r', encoding='utf-8') as infile:
        data = json.load(infile)

    # If the file is a dict with a 'hits' key (from ES _search), get the hits
    if isinstance(data, dict) and 'hits' in data and 'hits' in data['hits']:
        hits = data['hits']['hits']
        with open(output_path, 'w', encoding='utf-8') as outfile:
            for hit in hits:
                action = {"index": {"_index": index_name}}
                if '_id' in hit:
                    action["index"]["_id"] = hit['_id']
                outfile.write(json.dumps(action) + '\n')
                outfile.write(json.dumps(hit['_source']) + '\n')
        return
    # If the file is a dict with a 'data' key (custom export)
    elif isinstance(data, dict) and 'data' in data:
        docs = data['data']
    # If the file is a list of docs
    elif isinstance(data, list):
        docs = data
    else:
        raise ValueError('Unrecognized input format')

    with open(output_path, 'w', encoding='utf-8') as outfile:
        for doc in docs:
            action = {"index": {"_index": index_name}}
            outfile.write(json.dumps(action) + '\n')
            outfile.write(json.dumps(doc) + '\n')

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python bulk_conversion.py input.json output.jsonl index_name")
        sys.exit(1)
    convert_to_bulk(sys.argv[1], sys.argv[2], sys.argv[3])
