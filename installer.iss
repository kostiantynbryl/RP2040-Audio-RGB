#define MyAppName "RP2040 Audio RGB"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Kostiantyn Bryl"
#define MyAppExeName "RP2040AudioRGB.exe"

[Setup]
AppId={{C9B73F4F-29BD-4F68-8F47-3D5E46944B42}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\RP2040 Audio RGB
DefaultGroupName={#MyAppName}
OutputDir=dist\installer
OutputBaseFilename=RP2040AudioRGB-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
Source: "dist\RP2040AudioRGB\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
