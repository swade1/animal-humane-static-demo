import os
import json
from elasticsearch import Elasticsearch

def list_indices(es, prefix="animal-humane-*"):
    indices_info = es.cat.indices(index=prefix, h="index,docs.count", s="index:desc", format="json")
    return indices_info

def prompt_indices(indices_info):
    print("Available indices (descending order):")
    for i, idx in enumerate(indices_info):
        print(f"{i+1}: {idx['index']} (docs: {idx['docs.count']})")
    print("Enter 'q' to quit.")
    selected = input("Enter comma-separated numbers of indices to dump (e.g. 1,3,5): ")
    if selected.strip().lower() == 'q':
        return []
    selected_indices = []
    for num in selected.split(","):
        num = num.strip()
        if num.isdigit() and 1 <= int(num) <= len(indices_info):
            selected_indices.append(indices_info[int(num)-1]['index'])
    return selected_indices

def dump_index(es, index_name, output_dir):
    res = es.search(index=index_name, size=500, body={}, pretty=True)
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{index_name}_dump.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    print(f"Dumped {index_name} to {output_file}")

def main():
    es = Elasticsearch("http://localhost:9201")
    indices_info = list_indices(es)
    if not indices_info:
        print("No indices found.")
        return
    selected_indices = prompt_indices(indices_info)
    for idx in selected_indices:
        dump_index(es, idx, "backups")

if __name__ == "__main__":
    main()
