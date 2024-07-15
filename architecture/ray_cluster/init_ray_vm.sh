#!/bin/bash
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
export OPENAI_API_KEY="openai-api-key"
ray start --head --dashboard-host 0.0.0.0 --metrics-export-port=8080 --num-cpus=12

