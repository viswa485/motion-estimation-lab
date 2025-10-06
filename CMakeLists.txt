cmake_minimum_required(VERSION 3.16)
project(motion_estimation_lab VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(me_core cpp/src/motion_estimation.cpp)
target_include_directories(me_core PUBLIC cpp/include)
target_compile_options(me_core PRIVATE
    $<$<CXX_COMPILER_ID:GNU,Clang>:-Wall;-Wextra;-Wpedantic;-Wconversion>
)

add_executable(me_bench cpp/src/main.cpp)
target_link_libraries(me_bench PRIVATE me_core)
target_compile_options(me_bench PRIVATE
    $<$<CXX_COMPILER_ID:GNU,Clang>:-Wall;-Wextra;-Wpedantic;-Wconversion>
)

include(CTest)
if(BUILD_TESTING)
    add_executable(me_unit_tests cpp/tests/test_motion_estimation.cpp)
    target_link_libraries(me_unit_tests PRIVATE me_core)
    add_test(NAME me_unit_tests COMMAND me_unit_tests)
endif()
