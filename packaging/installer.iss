#ifndef AppVersion
  #error AppVersion is required
#endif
#define Publisher "Seyed Mohammad Saleh Ghotbani"

[Setup]
AppId={{4CD29712-8CCB-4E55-85E5-1D9295313A97}
AppName=Persian Typo Fixer
AppVersion={#AppVersion}
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
ShowLanguageDialog=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "persian"; MessagesFile: "languages\Farsi.isl"

[LangOptions]
persian.LanguageName=فارسی

[CustomMessages]
english.StartWithSystem=Start when the system starts
persian.StartWithSystem=اجرا هنگام روشن کردن سیستم
english.LaunchApplication=Run Persian Typo Fixer
persian.LaunchApplication=اجرای Persian Typo Fixer

[Messages]
english.ApplicationsFound=Persian Typo Fixer is running. Setup will close the applications listed below to update their files, then reopen Persian Typo Fixer when installation finishes.
persian.ApplicationsFound=برنامه در حال اجراست. نصاب برای به‌روزرسانی فایل‌ها، برنامه‌های فهرست زیر را می‌بندد و پس از پایان نصب، Persian Typo Fixer را دوباره باز می‌کند.

[Tasks]
Name: "autostart"; Description: "{cm:StartWithSystem}"; Flags: unchecked

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
Filename: "{app}\PersianTypoFixer.exe"; Description: "{cm:LaunchApplication}"; Flags: nowait postinstall skipifsilent; Check: OfferLaunchApplication
Filename: "{app}\PersianTypoFixer.exe"; Flags: nowait; Check: ResumeApplication

[Code]
var
  AppWasRunning: Boolean;

function IsAppUpdate(): Boolean;
begin
  Result := ExpandConstant('{param:PTFUPDATE|0}') = '1';
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  AppWasRunning := AppWasRunning or CheckForMutexes('Local\PersianTypoFixer.Singleton');
  Result := '';
end;

function OfferLaunchApplication(): Boolean;
begin
  Result := not (AppWasRunning or IsAppUpdate());
end;

function ResumeApplication(): Boolean;
begin
  Result := (AppWasRunning or IsAppUpdate()) and
    not CheckForMutexes('Local\PersianTypoFixer.Singleton');
end;

function InitializeUninstall(): Boolean;
begin
  Result := True;
  while CheckForMutexes('Local\PersianTypoFixer.Singleton') do
    if SuppressibleMsgBox(FmtMessage(SetupMessage(msgUninstallAppRunningError), ['Persian Typo Fixer']),
      mbError, MB_OKCANCEL, IDCANCEL) = IDCANCEL then
    begin
      Result := False;
      Exit;
    end;
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
