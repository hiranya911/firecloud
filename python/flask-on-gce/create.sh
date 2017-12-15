#!/bin/bash
curl -v -X POST -d @spiderman.json -H "Content-type: application/json" http://$1/heroes