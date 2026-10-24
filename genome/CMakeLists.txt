cmake_minimum_required(VERSION 3.20)
project(genome CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()
# The simulator and the policy interpreter (opponents), unchanged.
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/../interp ${CMAKE_BINARY_DIR}/interp)

add_executable(genome_eval tools/genome_eval.cpp)
target_include_directories(genome_eval PRIVATE runtime)
# whole archive: every simulator symbol must be there for the loaded genome to call
target_link_libraries(genome_eval interp pthread dl)
target_link_options(genome_eval PRIVATE "LINKER:--whole-archive" $<TARGET_FILE:cbs> "LINKER:--no-whole-archive")
# genomes are loaded as shared objects that call back into the simulator
set_target_properties(genome_eval PROPERTIES ENABLE_EXPORTS ON)
