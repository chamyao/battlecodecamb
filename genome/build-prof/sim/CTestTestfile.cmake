# CMake generated Testfile for 
# Source directory: /home/user/battlecodecamb/sim
# Build directory: /home/user/battlecodecamb/genome/build-prof/sim
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
add_test([=[geom_00elkring]=] "sh" "-c" "zcat /home/user/battlecodecamb/sim/../oracle/fixtures/geom/00elkring.txt.gz | /home/user/battlecodecamb/genome/build-prof/sim/geomtest /home/user/battlecodecamb/sim/../maps/00elkring.map26a")
set_tests_properties([=[geom_00elkring]=] PROPERTIES  _BACKTRACE_TRIPLES "/home/user/battlecodecamb/sim/CMakeLists.txt;21;add_test;/home/user/battlecodecamb/sim/CMakeLists.txt;0;")
add_test([=[geom_00great-wall]=] "sh" "-c" "zcat /home/user/battlecodecamb/sim/../oracle/fixtures/geom/00great-wall.txt.gz | /home/user/battlecodecamb/genome/build-prof/sim/geomtest /home/user/battlecodecamb/sim/../maps/00great-wall.map26a")
set_tests_properties([=[geom_00great-wall]=] PROPERTIES  _BACKTRACE_TRIPLES "/home/user/battlecodecamb/sim/CMakeLists.txt;21;add_test;/home/user/battlecodecamb/sim/CMakeLists.txt;0;")
add_test([=[geom_01islands]=] "sh" "-c" "zcat /home/user/battlecodecamb/sim/../oracle/fixtures/geom/01islands.txt.gz | /home/user/battlecodecamb/genome/build-prof/sim/geomtest /home/user/battlecodecamb/sim/../maps/01islands.map26a")
set_tests_properties([=[geom_01islands]=] PROPERTIES  _BACKTRACE_TRIPLES "/home/user/battlecodecamb/sim/CMakeLists.txt;21;add_test;/home/user/battlecodecamb/sim/CMakeLists.txt;0;")
add_test([=[geom_00lanes]=] "sh" "-c" "zcat /home/user/battlecodecamb/sim/../oracle/fixtures/geom/00lanes.txt.gz | /home/user/battlecodecamb/genome/build-prof/sim/geomtest /home/user/battlecodecamb/sim/../maps/00lanes.map26a")
set_tests_properties([=[geom_00lanes]=] PROPERTIES  _BACKTRACE_TRIPLES "/home/user/battlecodecamb/sim/CMakeLists.txt;21;add_test;/home/user/battlecodecamb/sim/CMakeLists.txt;0;")
add_test([=[maps]=] "python3" "/home/user/battlecodecamb/sim/tests/check_maps.py" "/home/user/battlecodecamb/genome/build-prof/sim/maptest" "/home/user/battlecodecamb/sim/..")
set_tests_properties([=[maps]=] PROPERTIES  _BACKTRACE_TRIPLES "/home/user/battlecodecamb/sim/CMakeLists.txt;25;add_test;/home/user/battlecodecamb/sim/CMakeLists.txt;0;")
add_test([=[replay_00elkring-100]=] "sh" "-c" "xz -dc /home/user/battlecodecamb/sim/../oracle/fixtures/traces/00elkring-100.txt.xz | /home/user/battlecodecamb/genome/build-prof/sim/replay /home/user/battlecodecamb/sim/../maps/00elkring.map26a /dev/stdin --quiet")
set_tests_properties([=[replay_00elkring-100]=] PROPERTIES  _BACKTRACE_TRIPLES "/home/user/battlecodecamb/sim/CMakeLists.txt;31;add_test;/home/user/battlecodecamb/sim/CMakeLists.txt;0;")
add_test([=[replay_01islands-12]=] "sh" "-c" "xz -dc /home/user/battlecodecamb/sim/../oracle/fixtures/traces/01islands-12.txt.xz | /home/user/battlecodecamb/genome/build-prof/sim/replay /home/user/battlecodecamb/sim/../maps/01islands.map26a /dev/stdin --quiet")
set_tests_properties([=[replay_01islands-12]=] PROPERTIES  _BACKTRACE_TRIPLES "/home/user/battlecodecamb/sim/CMakeLists.txt;31;add_test;/home/user/battlecodecamb/sim/CMakeLists.txt;0;")
add_test([=[replay_00contest-13]=] "sh" "-c" "xz -dc /home/user/battlecodecamb/sim/../oracle/fixtures/traces/00contest-13.txt.xz | /home/user/battlecodecamb/genome/build-prof/sim/replay /home/user/battlecodecamb/sim/../maps/00contest.map26a /dev/stdin --quiet")
set_tests_properties([=[replay_00contest-13]=] PROPERTIES  _BACKTRACE_TRIPLES "/home/user/battlecodecamb/sim/CMakeLists.txt;31;add_test;/home/user/battlecodecamb/sim/CMakeLists.txt;0;")
