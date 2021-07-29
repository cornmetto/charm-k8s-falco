# charm-k8s-falco

## Description

Falco is a cloud-native runtime security tool designed to detect unexpected application behavior and alerts on threats at runtime. Falco consumes events from either system calls or Kubernetes Audit Events, applies rules to detect abnormal behavior and alerts based on the configured alerting rules.

## Installation

### Charm Installtion
This charm is designed to capture kubernetes audit logs only. It excusively uses
userspace instrumentation and ingests kubernetes audit events. To achieve this, the charm installs falco based on the `krisnova/falco-trace`
image which does not require installation of the kernel module to work. Installation is therefore as in other Juju charms:

    $ git clone https://github.com/cornmetto/charm-k8s-falco.git
    $ cd charm-k8s-falco
    $ charmcraft build
    $ juju deploy ./falco.charm --resource falco-image=krisnova/falco-trace

### Kubernetes Webhook Backend Configuration

Since dynamic audit sink configuration is deprecated as of v1.19 of Kubernetes,
the installation depends on changes to kube-apiserver. The service needs to be started with options for the audit policy file and the webhook configuration.

    --audit-policy-file=/var/snap/microk8s/current/args/kube-api-audit-policy
    --audit-webhook-config-file=/var/snap/microk8s/current/var/lib/falco/webhook-config.yaml

Here are examples of the files above:
#### webhook-config.yaml

    # webhook-config.yaml
    apiVersion: v1
    kind: Config
    clusters:
    - name: falco
    cluster:
        server: http://$FALCO_SERVICE_CLUSTERIP:8765/k8s-audit
    contexts:
    - context:
        cluster: falco
        user: ""
    name: default-context
    current-context: default-context
    preferences: {}
    users: []

#### kube-api-audit-policy (Captures all events. Only for development)
    apiVersion: audit.k8s.io/v1beta1
    kind: Policy
    rules:
    # Default level for all other requests.
    - level: RequestResponse


## Usage

### Actions
The charm implements show-rules, a very simple action that is useful both during development and after deployment. It displays the falco rules against which kubernetes audit events are processed.

    juju run-action falco show-rules

### Configuration
We also have a configuration option to set an HTTP endpoint for submission of alerts. This is `http_output`. By default, this is empty and falco defaults to only file logging. When set, falco
submits alerts to both this http endpoint and the default log file at `/var/log/falco.log` in the charm container.

### Relations
At the moment, the charm has not implemented a relation but an alerting relation is needed to for completeness. 

## Developing

Create and activate a virtualenv with the development requirements:

    virtualenv -p python3 venv
    source venv/bin/activate
    pip install -r requirements-dev.txt

## Testing

This version of the charm has not implemented tests. 

## Future work

- Testing
- Relation to Graylog
