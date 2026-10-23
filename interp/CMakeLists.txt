cmake_minimum_required(VERSION 3.20)
project(interp CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

# The simulator, built as part of this project.
add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/../sim ${CMAKE_BINARY_DIR}/sim)

add_library(interp STATIC src/policy.cpp)
target_include_directories(interp PUBLIC include)
target_link_libraries(interp PUBLIC cbs)
target_compile_options(interp PRIVATE -Wall -Wextra -Wno-unused-parameter)

add_executable(interp_eval tools/interp_eval.cpp)
target_link_libraries(interp_eval interp pthread)

add_executable(fuel_turns tools/fuel_turns.cpp)
target_link_libraries(fuel_turns interp pthread)
