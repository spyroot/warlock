#!/bin/bash

num_pods=3

for i in $(seq 0 $((num_pods - 1)))
do
    server_name="server$i"
    client_name="client$i"
    sed "s/{{server-name}}/$server_name/g" pod-server-template.yaml > "pod-$server_name.yaml"
    sed "s/{{client-name}}/$client_name/g" pod-client-template.yaml > "pod-$client_name.yaml"
    kubectl apply -f "pod-$server_name.yaml"
    kubectl apply -f "pod-$client_name.yaml"
done
