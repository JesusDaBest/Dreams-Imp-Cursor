@echo off
setlocal
if not defined VULKAN_SDK (echo Set VULKAN_SDK to your Vulkan SDK directory. & exit /b 1)
if not defined NLOHMANN_INCLUDE (echo Set NLOHMANN_INCLUDE to the folder containing nlohmann/json.hpp. & exit /b 1)
pushd "%~dp0" || exit /b 1
if not defined IMP_OUTPUT set "IMP_OUTPUT=%~dp0.."
if not exist "%IMP_OUTPUT%\runtime" mkdir "%IMP_OUTPUT%\runtime"
clang-cl /nologo /MT /EHsc /std:c++20 /O2 /arch:AVX2 /I"%VULKAN_SDK%\Include" /I"%NLOHMANN_INCLUDE%" /LD /Fe"%IMP_OUTPUT%\runtime\imp-renderer.dll" /Fo"imp-renderer.obj" "dreams-native-cursor\verify-native-imp-draw.cpp" /link "%VULKAN_SDK%\Lib\vulkan-1.lib"
if errorlevel 1 exit /b 1
clang-cl /nologo /MT /EHsc /std:c++20 /O2 /arch:AVX2 /fp:strict /LD /Fe"%IMP_OUTPUT%\runtime\imp-frame-helpers.dll" /Fo"frame-helpers.obj" frame-helpers.cpp
if errorlevel 1 exit /b 1
rc /nologo /fo app.res app.rc
if errorlevel 1 exit /b 1
clang-cl /nologo /MT /EHsc /std:c++20 /O2 /Fe"%IMP_OUTPUT%\Imp Carousel.exe" /Fo"windows-launcher.obj" "windows-launcher.cpp" /link app.res /SUBSYSTEM:WINDOWS user32.lib
if errorlevel 1 exit /b 1
exit /b 0
