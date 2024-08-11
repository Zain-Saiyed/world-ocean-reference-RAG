import json

# Read the input JSON data from the file
with open('cluster_output.json', 'r') as file:
    data = json.load(file)

# Initialize the hierarchical structure
output = {
    "name": "clusters",
    "children": []
}

# Convert the input JSON to the hierarchical structure
for cluster in data:
    cluster_dict = {
        "name": cluster["cluster_name"],
        "children": []
    }
    
    for abstract_id in cluster["abstract_ids"]:
        cluster_dict["children"].append({
            "name": abstract_id,
            "value": 1
        })
    
    output["children"].append(cluster_dict)

# Write the hierarchical JSON to an output file
with open('hierarchical_output.json', 'w') as file:
    json.dump(output, file, indent=4)
