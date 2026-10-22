#include <windows.h>
#include <tlhelp32.h>

#include <ctime>
#include <cwchar>
#include <fstream>
#include <iostream>
#include <string>

namespace {

std::wstring timestamp() {
    const std::time_t now = std::time(nullptr);
    std::tm local{};
    localtime_s(&local, &now);
    wchar_t buffer[32]{};
    std::wcsftime(buffer, sizeof(buffer) / sizeof(buffer[0]), L"%Y-%m-%d %H:%M:%S", &local);
    return buffer;
}

void inventoryProcesses(std::wofstream& report) {
    report << L"\n[Running processes]\n";
    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snapshot == INVALID_HANDLE_VALUE) {
        report << L"Unable to enumerate processes. Windows error: " << GetLastError() << L"\n";
        return;
    }

    PROCESSENTRY32W entry{};
    entry.dwSize = sizeof(entry);
    if (Process32FirstW(snapshot, &entry)) {
        do {
            report << L"PID=" << entry.th32ProcessID << L"  Name=" << entry.szExeFile << L"\n";
        } while (Process32NextW(snapshot, &entry));
    } else {
        report << L"Process enumeration failed. Windows error: " << GetLastError() << L"\n";
    }
    CloseHandle(snapshot);
}

void inventoryRunKey(std::wofstream& report, HKEY root, const wchar_t* subkey, const wchar_t* label) {
    report << L"\n[" << label << L"]\n";
    HKEY key = nullptr;
    const LONG status = RegOpenKeyExW(root, subkey, 0, KEY_READ, &key);
    if (status != ERROR_SUCCESS) {
        report << L"(Not available or absent; registry status " << status << L")\n";
        return;
    }

    for (DWORD index = 0;; ++index) {
        wchar_t name[512]{};
        BYTE data[4096]{};
        DWORD nameLength = static_cast<DWORD>(sizeof(name) / sizeof(name[0]));
        DWORD dataLength = sizeof(data);
        DWORD type = 0;
        const LONG result = RegEnumValueW(key, index, name, &nameLength, nullptr, &type, data, &dataLength);
        if (result == ERROR_NO_MORE_ITEMS) break;
        if (result != ERROR_SUCCESS) {
            report << L"(Stopped reading entries; registry status " << result << L")\n";
            break;
        }

        report << L"Name=" << name << L"  Data=";
        if ((type == REG_SZ || type == REG_EXPAND_SZ) && dataLength >= sizeof(wchar_t)) {
            const auto* value = reinterpret_cast<const wchar_t*>(data);
            const size_t chars = dataLength / sizeof(wchar_t);
            for (size_t i = 0; i < chars && value[i] != L'\0'; ++i) report << value[i];
        } else {
            report << L"[non-string registry data]";
        }
        report << L"\n";
    }
    RegCloseKey(key);
}

bool createReport() {
    std::wofstream report("security_report.txt", std::ios::out | std::ios::trunc);
    if (!report) {
        std::wcerr << L"Could not create security_report.txt in the current folder.\n";
        return false;
    }

    report << L"DualDesktopSecurityMonitor - Local Inventory Report\n";
    report << L"Generated: " << timestamp() << L"\n";
    report << L"Scope: read-only process and startup-entry inventory\n";
    report << L"Review this file before sharing; it may contain personal system details.\n";

    inventoryProcesses(report);
    inventoryRunKey(report, HKEY_CURRENT_USER,
        L"Software\\Microsoft\\Windows\\CurrentVersion\\Run",
        L"Current-user startup Run entries");
    inventoryRunKey(report, HKEY_LOCAL_MACHINE,
        L"Software\\Microsoft\\Windows\\CurrentVersion\\Run",
        L"Machine startup Run entries");

    report.flush();
    if (!report) {
        std::wcerr << L"An error occurred while writing the report.\n";
        return false;
    }
    std::wcout << L"Report saved to security_report.txt\n";
    return true;
}

void testInputDemo() {
    std::wcout << L"\nTEST-INPUT DEMO (console prompt only)\n";
    std::wcout << L"Enter fictional test text. Nothing is captured outside this prompt.\n";
    std::wcout << L"Test text: ";

    std::wstring input;
    std::getline(std::wcin, input);

    std::wofstream report("security_report.txt", std::ios::out | std::ios::app);
    if (report) {
        report << L"\n[Explicit test-input demo]\n";
        report << L"Time: " << timestamp() << L"\n";
        report << L"Input length: " << input.size() << L" characters\n";
        report << L"Input content is intentionally not stored.\n";
    }
    std::wcout << L"Demo complete. The entered text was not saved.\n";
}

} // namespace

int main() {
    for (;;) {
        std::wcout << L"\n=== DualDesktopSecurityMonitor ===\n"
                   << L"1. Create local inventory report\n"
                   << L"2. Test-input demo (this console only)\n"
                   << L"0. Exit\n"
                   << L"Choose an option: ";

        std::wstring choice;
        if (!std::getline(std::wcin, choice)) return 0;

        if (choice == L"1") {
            createReport();
        } else if (choice == L"2") {
            testInputDemo();
        } else if (choice == L"0") {
            return 0;
        } else {
            std::wcout << L"Invalid option. Please enter 1, 2, or 0.\n";
        }
    }
}
