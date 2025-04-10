SELECT 
    j.job_id,
    j.name AS job_name,
    j.owner_sid,
    SUSER_SNAME(j.owner_sid) AS owner_name,
    js.step_id,
    js.step_name,
    js.command AS step_command,
    js.subsystem,
    CASE 
        WHEN sp.sid IS NULL THEN 'INVALID OR MISSING OWNER'
        ELSE 'OK'
    END AS owner_status
FROM 
    msdb.dbo.sysjobs AS j
LEFT JOIN 
    sys.syslogins AS sp ON j.owner_sid = sp.sid
INNER JOIN 
    msdb.dbo.sysjobsteps AS js ON j.job_id = js.job_id
WHERE 
    js.subsystem = 'SSIS'
    AND js.command LIKE '%\SSISDB\folderName\%'  -- packages under folder
    AND (j.owner_sid IS NULL OR sp.sid IS NULL) -- null or orphaned owner
ORDER BY 
    j.name;



DECLARE @NewOwnerSID VARBINARY(85);

-- Set this to the SID you retrieved in Step 1
SELECT @NewOwnerSID = sid 
FROM sys.syslogins 
WHERE name = 'your_domain\new_owner_login';  -- change this

-- Update jobs with NULL or invalid owner SID that use packages in 'commission'
UPDATE j
SET j.owner_sid = @NewOwnerSID
FROM msdb.dbo.sysjobs AS j
LEFT JOIN sys.syslogins AS sp ON j.owner_sid = sp.sid
INNER JOIN msdb.dbo.sysjobsteps AS js ON j.job_id = js.job_id
WHERE 
    js.subsystem = 'SSIS'
    AND js.command LIKE '%\SSISDB\folderName\%'  -- targeting  folder
    AND (j.owner_sid IS NULL OR sp.sid IS NULL);
