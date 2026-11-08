#ifndef AppVersion
  #error AppVersion is required
#endif
#define Publisher "Seyed Mohammad Saleh Ghotbani"

[Setup]
AppId={{4CD29712-8CCB-4E55-85E5-1D9295313A97}
AppName=Persian Typo Fixer
AppVersion={#AppVersion}
AppMutex=Local\PersianTypoFixer.Singleton
AppPublisher={#Publisher}
AppPublisherURL=https://github.com/salehghotbani/PersianTypeFixer
AppSupportURL=https://github.com/salehghotbani/PersianTypeFixer/issues
VersionInfoCompany={#Publisher}
VersionInfoProductName=Persian Typo Fixer
VersionInfoDescription=Persian Typo Fixer Windows Installer
VersionInfoVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\PersianTypoFixer
DefaultGroupName=Persian Typo Fixer
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763
OutputDir=..\dist\release
OutputBaseFilename=PersianTypoFixer-v{#AppVersion}-windows-x64-setup
SetupIconFile=..\build\assets\app.ico
UninstallDisplayIcon={app}\PersianTypoFixer.exe
LicenseFile=..\LICENSE
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "autostart"; Description: "اجرا هنگام روشن کردن سیستم"; Flags: unchecked

[Files]
Source: "..\dist\PersianTypoFixer\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Persian Typo Fixer"; Filename: "{app}\PersianTypoFixer.exe"; IconFilename: "{app}\PersianTypoFixer.exe"

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "PersianTypoFixer"; ValueData: """{app}\PersianTypoFixer.exe"""; Tasks: autostart; Flags: uninsdeletevalue

[Run]
Filename: "{app}\PersianTypoFixer.exe"; Description: "Run Persian Typo Fixer"; Flags: nowait postinstall skipifsilent
Filename: "{app}\PersianTypoFixer.exe"; Flags: nowait skipifnotsilent; Check: IsAppUpdate

[Code]
function IsAppUpdate(): Boolean;
begin
  Result := ExpandConstant('{param:PTFUPDATE|0}') = '1';
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssPostInstall) and not WizardIsTaskSelected('autostart') then
    RegDeleteValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Run', 'PersianTypoFixer');
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
    RegDeleteValue(HKCU, 'Software\Microsoft\Windows\CurrentVersion\Run', 'PersianTypoFixer');
end;
