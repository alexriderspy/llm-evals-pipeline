#!/bin/bash
name="$1"; shift
out="media/terminal/$name.log"
{ echo "sreemanti@MacBook-Pro llm-evals-pipeline % $*"; "$@" 2>&1; } | tee "$out"
