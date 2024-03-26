#!/bin/bash
# Generate trafgen config per pod
# Mus mbayramov@vmware.com

DEST_IPS=($(kubectl get pods -o wide | grep 'client' | awk '{print $6}'))
server_pods=($(kubectl get pods | grep 'server' | awk '{print $1}'))

if [ ${#server_pods[@]} -ne ${#DEST_IPS[@]} ]; then
    echo "The number of server pods and destination IPs do not match."
    exit 1
fi

# Loop  each server generate cpp spec and run
for i in "${!server_pods[@]}"
do
    pod="${server_pods[$i]}"
    dest_ip="${DEST_IPS[$i]}"

    echo "Copying script to $pod"
    kubectl cp traff_spec.sh "$pod":/tmp/generate_per_pod.sh
    kubectl exec "$pod" -- chmod +x /tmp/generate_per_pod.sh

    echo "Executing script on $pod with DEST_IP=$dest_ip"
    kubectl exec "$pod" -- sh -c "env DEST_IP='$dest_ip' /tmp/generate_per_pod.sh > /tmp/udp.trafgen"
    echo "Contents of /tmp/udp.trafgen on $pod:"
    kubectl exec "$pod" -- cat /tmp/udp.trafgen
done