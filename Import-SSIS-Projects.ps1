$SqlServer = "SQLDEV01"
$CatalogFolder = "TeamXYZ"
$ProjectRoot = "C:\ssis-projects\develop"

Get-ChildItem -Path $ProjectRoot -Filter *.ispac -Recurse | ForEach-Object {
    $projectPath = $_.FullName
    $projectName = $_.BaseName
    $catalogPath = "\SSISDB\$CatalogFolder\$projectName"

    & "C:\Program Files\Microsoft SQL Server\160\DTS\Binn\ISDeploymentWizard.exe" `
        /Silent `
        /SourcePath:$projectPath `
        /DestinationServer:$SqlServer `
        /DestinationPath:$catalogPath
}


✅ TL;DR: What You Can Do

Task	How
Export everything manually	Use the modular scripts you just downloaded
Automate with GitHub	Use GitHub Actions + self-hosted runner
Restore everything later	Write matching import scripts for .ispac, jobs, and config DB
Make it production-grade	Add logging, error capture, version tags, emails, etc.