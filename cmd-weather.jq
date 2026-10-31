#!/bin/bash

cat weather.json | jq .properties.timeseries[].data.instant.details | less