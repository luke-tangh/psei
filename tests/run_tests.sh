#!/bin/bash

executable=$1
input_file=$2
actual_output=$3
expected_output=$4

# Run the program and redirect stdout to the actual output file
"$executable" "$input_file" --show-ast --show-st > "$actual_output"

# Compare the actual output with the expected output
diff -u "$actual_output" "$expected_output"
