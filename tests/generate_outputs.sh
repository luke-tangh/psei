#!/bin/bash

# Path to the PseI executable
executable="../build/PseI"

# Define directories relative to the script location
examples_dir="../examples"
output_dir="."

# Ensure the output directory exists
mkdir -p "$output_dir"

# Process each .pse file in the examples directory
for input_file in "$examples_dir"/*.pse; do
  # Derive the output file name
  file_name=$(basename "$input_file" .pse)
  expected_output="$output_dir/$file_name.out"

  # Run the program and redirect stdout to the expected output file
  "$executable" "$input_file" --show-ast --show-st > "$expected_output"
done

echo "Expected output files generated."
