[Setup]
AppName=Notepd
AppVersion=1.0
AppVerName=Notepd 1.0
AppId={{1D5C3E42-6E97-4C94-B9A6-NotepdApp}}
DefaultDirName={pf}\Notepd
DefaultGroupName=Notepd
OutputBaseFilename=NotepdInstaller
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
Uninstallable=yes
CreateUninstallRegKey=yes
UninstallDisplayName=Notepd
UninstallDisplayIcon={app}\Notepd.ico
UsePreviousAppDir=yes
DisableWelcomePage=no
SetupLogging=yes
ArchitecturesInstallIn64BitMode=x64

[Registry]
Root: HKCU; Subkey: "Software\Notepd"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletekey

[Tasks]
Name: desktopicon; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "notepd.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "Notepd.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "tkdnd-2.9.5-windows-tcl8.6-x64.zip"; DestDir: "{tmp}"; Flags: ignoreversion
Source: "install_tkdnd.ps1"; DestDir: "{app}"; Flags: ignoreversion

[Run]
Filename: "{cmd}"; Parameters: "/c python -m pip show tkinterdnd2 >nul 2>nul || python -m pip install tkinterdnd2"; StatusMsg: "Installing tkinterdnd2..."; Flags: runhidden
Filename: "{cmd}"; Parameters: "/c python -m pip show pywin32 >nul 2>nul || python -m pip install pywin32"; StatusMsg: "Installing pywin32..."; Flags: runhidden
Filename: "{cmd}"; Parameters: "/c powershell -NoProfile -ExecutionPolicy Bypass -File ""{app}\install_tkdnd.ps1"""; StatusMsg: "Installing tkdnd..."; Flags: runhidden

[Icons]
Name: "{group}\Notepd"; Filename: "{code:GetPythonw}"; Parameters: """{app}\notepd.py"""; WorkingDir: "{app}"; IconFilename: "{app}\Notepd.ico"
Name: "{commondesktop}\Notepd"; Filename: "{code:GetPythonw}"; Parameters: """{app}\notepd.py"""; WorkingDir: "{app}"; IconFilename: "{app}\Notepd.ico"; Tasks: desktopicon

[Code]
function GetPythonExecutable(): string;
var
  OutputLines: TArrayOfString;
  TmpPath: string;
  ExitCode: Integer;
  I: Integer;
begin
  Result := '';
  TmpPath := ExpandConstant('{tmp}') + '\pywhere.txt';

  if Exec('cmd.exe', '/C where python > "' + TmpPath + '"', '', SW_HIDE, ewWaitUntilTerminated, ExitCode) and (ExitCode = 0) then
  begin
    if LoadStringsFromFile(TmpPath, OutputLines) then
    begin
      for I := 0 to GetArrayLength(OutputLines) - 1 do
      begin
        if Pos('WindowsApps', OutputLines[I]) = 0 then
        begin
          Result := OutputLines[I];
          DeleteFile(TmpPath);
          Exit;
        end;
      end;
    end;
  end;

  MsgBox('❌ Python is not properly installed.'#13#10 +
         'Please install Python 3.11 or newer before continuing.', mbCriticalError, MB_OK);
  Result := '';
end;

function GetPythonw(Param: string): string;
var
  ResultStr, Version, Key, BestMatch: string;
  Versions: TArrayOfString;
  I: Integer;
begin
  BestMatch := '';
  if RegGetSubkeyNames(HKEY_CURRENT_USER, 'Software\Python\PythonCore', Versions) then
  begin
    for I := 0 to GetArrayLength(Versions)-1 do
      if Versions[I] > BestMatch then BestMatch := Versions[I];
    if BestMatch <> '' then
    begin
      Key := 'Software\Python\PythonCore\' + BestMatch + '\InstallPath';
      if RegQueryStringValue(HKEY_CURRENT_USER, Key, '', ResultStr) then
      begin
        Result := ResultStr + 'pythonw.exe';
        Exit;
      end;
    end;
  end;

  if RegGetSubkeyNames(HKEY_LOCAL_MACHINE, 'Software\Python\PythonCore', Versions) then
  begin
    for I := 0 to GetArrayLength(Versions)-1 do
      if Versions[I] > BestMatch then BestMatch := Versions[I];
    if BestMatch <> '' then
    begin
      Key := 'Software\Python\PythonCore\' + BestMatch + '\InstallPath';
      if RegQueryStringValue(HKEY_LOCAL_MACHINE, Key, '', ResultStr) then
      begin
        Result := ResultStr + 'pythonw.exe';
        Exit;
      end;
    end;
  end;

  Result := 'pythonw.exe';  // fallback
end;

function InitializeSetup(): Boolean;
var
  InstallPath: string;
begin
  // Detect prior install via registry (optional check)
  if RegQueryStringValue(HKEY_CURRENT_USER, 'Software\Notepd', 'InstallPath', InstallPath) then
  begin
    // You could show a custom warning here if needed
    // For now, let setup continue and Inno will handle repair/remove
  end;

  Result := (GetPythonExecutable() <> '');
end;
