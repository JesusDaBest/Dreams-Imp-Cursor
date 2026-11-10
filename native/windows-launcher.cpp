#include <windows.h>
#include <filesystem>
#include <string>

int WINAPI wWinMain(HINSTANCE, HINSTANCE, LPWSTR, int) {
    wchar_t executable[32768];
    const auto length = GetModuleFileNameW(nullptr, executable, 32768);
    if (!length || length == 32768) return 1;
    const std::filesystem::path path(executable);
    const auto runtime = path.parent_path() / L"runtime";
    const auto python = runtime / L"python" / L"pythonw.exe";
    const auto script = runtime / L"app.py";
    std::wstring args = L"\"" + python.wstring() + L"\" \"" + script.wstring() + L"\"";
    STARTUPINFOW startup{};
    startup.cb = sizeof(startup);
    PROCESS_INFORMATION child{};
    if (!CreateProcessW(python.c_str(), args.data(), nullptr, nullptr, FALSE, CREATE_NO_WINDOW,
                        nullptr, runtime.c_str(), &startup, &child)) {
        MessageBoxW(nullptr, L"Extract the entire ZIP to a folder, then open the launcher again.",
                    L"Dreams Imp", MB_OK | MB_ICONERROR);
        return 1;
    }
    CloseHandle(child.hThread);
    WaitForSingleObject(child.hProcess, INFINITE);
    DWORD result = 1;
    GetExitCodeProcess(child.hProcess, &result);
    CloseHandle(child.hProcess);
    if (result) {
        MessageBoxW(nullptr, L"The app could not start. Its log is in %LOCALAPPDATA%\\Dreams Imp\\last-error.txt.\nSee README.txt for the GPU requirements.",
                    L"Dreams Imp", MB_OK | MB_ICONERROR);
    }
    return int(result);
}
