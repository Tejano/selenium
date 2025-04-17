param (
    [string]$SqlServer = "SQLDEV01",
    [string]$CatalogFolder = "TeamXYZ",
    [string]$OutputPath = "C:\\ssis-projects\\develop",
    [string]$ConfigDbServer = "CONFIGSQL01",
    [string]$ConfigDbName = "SSIS_Config"
)

# Create output folders
$multiProjectJobFolder = Join-Path $OutputPath "multi-project-jobs"
$configFolder = Join-Path $OutputPath "ssis-config"
$schemaFolder = Join-Path $configFolder "schema"
$sprocFolder = Join-Path $configFolder "sprocs"

foreach ($folder in @($OutputPath, $multiProjectJobFolder, $schemaFolder, $sprocFolder)) {
    if (!(Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder | Out-Null
    }
}

# Load SSIS assemblies
Add-Type -AssemblyName "Microsoft.SqlServer.SMO"
Add-Type -AssemblyName "Microsoft.SqlServer.Management.IntegrationServices"

# Connect to SSISDB
$server = New-Object Microsoft.SqlServer.Management.Smo.Server $SqlServer
$ssisDb = New-Object Microsoft.SqlServer.Management.IntegrationServices.IntegrationServices $server
$catalog = $ssisDb.Catalogs["SSISDB"]
$folder = $catalog.Folders[$CatalogFolder]

if (-not $folder) {
    Write-Host "SSISDB folder '$CatalogFolder' not found."
    exit 1
}

# Export SSIS projects
foreach ($project in $folder.Projects) {
    $projectName = $project.Name
    $projectFolder = Join-Path $OutputPath $projectName
    if (!(Test-Path $projectFolder)) {
        New-Item -ItemType Directory -Path $projectFolder | Out-Null
    }

    $ispacFile = Join-Path $projectFolder "$projectName.ispac"
    [System.IO.File]::WriteAllBytes($ispacFile, $project.GetProjectBytes())

    Write-Host "Exported project '$projectName' to $ispacFile"
}

# Export SQL Agent jobs that reference this SSISDB folder
$connectionString = "Server=$SqlServer;Database=msdb;Integrated Security=SSPI;"
$catalogPattern = "\\\\SSISDB\\\\$CatalogFolder\\\\"

$query = @"
SELECT j.name AS JobName, s.step_id, s.step_name, s.command
FROM msdb.dbo.sysjobs j
JOIN msdb.dbo.sysjobsteps s ON j.job_id = s.job_id
WHERE s.command LIKE '%$catalogPattern%'
ORDER BY j.name, s.step_id
"@

$jobs = Invoke-Sqlcmd -ConnectionString $connectionString -Query $query
$jobsGrouped = $jobs | Group-Object JobName

foreach ($job in $jobsGrouped) {
    $jobName = $job.Name -replace '[\\/:*?"<>|]', '_'
    $commands = $job.Group.command
    $referencedProjects = @()

    foreach ($cmd in $commands) {
        if ($cmd -match "\\\\SSISDB\\\\$CatalogFolder\\\\([a-zA-Z0-9_]+)\\\\") {
            $referencedProjects += $matches[1]
        }
    }

    $uniqueProjects = $referencedProjects | Sort-Object -Unique

    if ($uniqueProjects.Count -eq 1) {
        $targetProject = $uniqueProjects[0]
        $projectJobsFolder = Join-Path $OutputPath "$targetProject\\jobs"
        if (!(Test-Path $projectJobsFolder)) {
            New-Item -ItemType Directory -Path $projectJobsFolder | Out-Null
        }
        $filePath = Join-Path $projectJobsFolder "$jobName.sql"
    } else {
        $filePath = Join-Path $multiProjectJobFolder "$jobName.sql"
    }

    $lines = @("-- Job: $jobName")
    foreach ($step in $job.Group) {
        $lines += ""
        $lines += "-- Step $($step.step_id): $($step.step_name)"
        $lines += $step.command
    }

    $lines | Set-Content -Path $filePath -Encoding UTF8
    Write-Host "Saved job script: $filePath"
}

# Export SSIS_Config schema and procs
$schemaFolder = Join-Path $configFolder "schema"
$sprocFolder = Join-Path $configFolder "sprocs"

$tableNames = @("config_run", "properties")
foreach ($table in $tableNames) {
    $ddlOutput = Invoke-Sqlcmd -ServerInstance $ConfigDbServer -Database $ConfigDbName -Query "EXEC sp_helptext '$table'" -ErrorAction SilentlyContinue
    if ($ddlOutput) {
        $ddlScript = $ddlOutput | ForEach-Object { $_.Text } | Out-String
        $ddlScript | Set-Content -Path (Join-Path $schemaFolder "$table.sql") -Encoding UTF8
        Write-Host "Exported table: $table"
    }
}

$procQuery = "SELECT name FROM sys.objects WHERE type = 'P' AND is_ms_shipped = 0"
$procs = Invoke-Sqlcmd -ServerInstance $ConfigDbServer -Database $ConfigDbName -Query $procQuery

foreach ($proc in $procs) {
    $name = $proc.name
    $definition = Invoke-Sqlcmd -ServerInstance $ConfigDbServer -Database $ConfigDbName -Query "EXEC sp_helptext '$name'"
    $content = $definition | ForEach-Object { $_.Text } | Out-String
    $path = Join-Path $sprocFolder "$name.sql"
    $content | Set-Content -Path $path -Encoding UTF8
    Write-Host "Exported proc: $name"
}