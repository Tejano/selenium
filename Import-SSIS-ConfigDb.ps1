$ConfigDb = "SSIS_Config"
$Server = "CONFIGSQL01"
$schemaDir = "ssis-config/schema"
$sprocDir = "ssis-config/sprocs"

# Deploy tables
Get-ChildItem $schemaDir -Filter *.sql | ForEach-Object {
    Invoke-Sqlcmd -ServerInstance $Server -Database $ConfigDb -InputFile $_.FullName
}

# Deploy stored procs
Get-ChildItem $sprocDir -Filter *.sql | ForEach-Object {
    Invoke-Sqlcmd -ServerInstance $Server -Database $ConfigDb -InputFile $_.FullName
}

✅ TL;DR: What You Can Do

Task	How
Export everything manually	Use the modular scripts you just downloaded
Automate with GitHub	Use GitHub Actions + self-hosted runner
Restore everything later	Write matching import scripts for .ispac, jobs, and config DB
Make it production-grade	Add logging, error capture, version tags, emails, etc.