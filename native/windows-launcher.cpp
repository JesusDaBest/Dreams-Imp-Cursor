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
    // Own the renderer tree without keeping the gallery open for its cursor.
    // Only the cursor-recovery watcher explicitly leaves this job, so it can
    // restore the Windows cursor if Task Manager terminates the launcher.
    HANDLE job = CreateJobObjectW(nullptr, nullptr);
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits{};
    limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | JOB_OBJECT_LIMIT_BREAKAWAY_OK;
    if (!job || !SetInformationJobObject(job, JobObjectExtendedLimitInformation, &limits, sizeof(limits))) {
        if (job) CloseHandle(job);
        MessageBoxW(nullptr, L"Windows could not create the app's process group.", L"Dreams Imp", MB_OK | MB_ICONERROR);
        return 1;
    }
    HANDLE exit = CreateEventW(nullptr, TRUE, FALSE, L"Local\\DreamsImp.Exit");
    const auto closedName = L"Local\\DreamsImp.PickerClosed." + std::to_wstring(GetCurrentProcessId());
    HANDLE closed = CreateEventW(nullptr, TRUE, FALSE, closedName.c_str());
    if (!exit || !closed) {
        if (exit) CloseHandle(exit);
        if (closed) CloseHandle(closed);
        CloseHandle(job);
        return 1;
    }
    SetEnvironmentVariableW(L"DREAMS_IMP_MANAGED_JOB", L"1");
    SetEnvironmentVariableW(L"DREAMS_IMP_PICKER_CLOSED", closedName.c_str());
    std::wstring args = L"\"" + python.wstring() + L"\" \"" + script.wstring() + L"\"";
    STARTUPINFOW startup{};
    startup.cb = sizeof(startup);
    PROCESS_INFORMATION child{};
    if (!CreateProcessW(python.c_str(), args.data(), nullptr, nullptr, FALSE, CREATE_NO_WINDOW | CREATE_SUSPENDED,
                        nullptr, runtime.c_str(), &startup, &child)) {
        MessageBoxW(nullptr, L"Extract the entire ZIP to a folder, then open the launcher again.",
                    L"Dreams Imp", MB_OK | MB_ICONERROR);
        CloseHandle(closed); CloseHandle(exit); CloseHandle(job); return 1;
    }
    if (!AssignProcessToJobObject(job, child.hProcess)) {
        TerminateProcess(child.hProcess, 1);
        CloseHandle(child.hThread); CloseHandle(child.hProcess);
        CloseHandle(closed); CloseHandle(exit); CloseHandle(job);
        MessageBoxW(nullptr, L"Windows could not manage the app's child processes.", L"Dreams Imp", MB_OK | MB_ICONERROR);
        return 1;
    }
    ResumeThread(child.hThread);
    CloseHandle(child.hThread);
    bool pickerFinished = false;
    ULONGLONG exitStarted = 0;
    DWORD result = 0;
    for (;;) {
        if (!pickerFinished && WaitForSingleObject(child.hProcess, 0) == WAIT_OBJECT_0) {
            pickerFinished = true;
            GetExitCodeProcess(child.hProcess, &result);
            if (WaitForSingleObject(closed, 0) != WAIT_OBJECT_0) {
                SetEvent(exit); // unexpected picker termination: stop the rest
                break;
            }
        }
        JOBOBJECT_BASIC_ACCOUNTING_INFORMATION accounting{};
        if (!QueryInformationJobObject(job, JobObjectBasicAccountingInformation, &accounting, sizeof(accounting), nullptr)) break;
        if (!accounting.ActiveProcesses) break;
        if (WaitForSingleObject(exit, 0) == WAIT_OBJECT_0) {
            if (!exitStarted) exitStarted = GetTickCount64();
            if (GetTickCount64() - exitStarted >= 6000) break;
        }
        Sleep(50);
    }
    CloseHandle(child.hProcess);
    CloseHandle(job);
    CloseHandle(closed);
    CloseHandle(exit);
    return int(result);
}
