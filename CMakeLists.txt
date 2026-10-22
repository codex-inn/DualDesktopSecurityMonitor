cmake_minimum_required(VERSION 3.20)
project(DualDesktopSecurityMonitor LANGUAGES CXX)

if(NOT WIN32)
  message(FATAL_ERROR "DualDesktopSecurityMonitor currently targets Windows 10/11.")
endif()

add_executable(DualDesktopSecurityMonitor src/sensor.cpp)
target_compile_features(DualDesktopSecurityMonitor PRIVATE cxx_std_17)
target_compile_definitions(DualDesktopSecurityMonitor PRIVATE UNICODE _UNICODE WIN32_LEAN_AND_MEAN NOMINMAX)
target_link_libraries(DualDesktopSecurityMonitor PRIVATE advapi32)
