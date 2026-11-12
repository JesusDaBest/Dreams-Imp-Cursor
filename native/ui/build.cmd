@echo off
setlocal
if not defined VULKAN_SDK (echo Set VULKAN_SDK to your Vulkan SDK directory. & exit /b 1)
if not defined NLOHMANN_INCLUDE (echo Set NLOHMANN_INCLUDE to the folder containing nlohmann/json.hpp. & exit /b 1)
pushd "%~dp0" || exit /b 1
clang-cl /nologo /MT /EHsc /std:c++20 /O2 /arch:AVX2 /I"%VULKAN_SDK%/Include" /I"%NLOHMANN_INCLUDE%" replay_buttons.cpp /Fo"imp-ui-renderer.obj" /Fe"../../runtime/imp-ui-renderer.exe" /link "%VULKAN_SDK%/Lib/vulkan-1.lib"
exit /b %errorlevel%
