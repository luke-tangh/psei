# Locate test input files from the examples directory
file(GLOB TEST_INPUT_FILES "${CMAKE_SOURCE_DIR}/examples/*.pse")

foreach(INPUT_FILE ${TEST_INPUT_FILES})
  # Derive test name from input file name
  get_filename_component(TEST_NAME ${INPUT_FILE} NAME_WE)

  # Define expected output file path in the tests directory
  set(EXPECTED_OUTPUT_FILE "${CMAKE_SOURCE_DIR}/tests/${TEST_NAME}.out")
  
  # Define where to store actual output from the test in the build directory
  set(ACTUAL_OUTPUT_FILE "${CMAKE_CURRENT_BINARY_DIR}/${TEST_NAME}.actual")

  # Add a test case
  add_test(NAME ${TEST_NAME}
  COMMAND bash ${CMAKE_SOURCE_DIR}/tests/run_tests.sh
            $<TARGET_FILE:PseI> ${INPUT_FILE} ${ACTUAL_OUTPUT_FILE} ${EXPECTED_OUTPUT_FILE})
  set_tests_properties(${TEST_NAME} PROPERTIES TIMEOUT 10)
endforeach()
