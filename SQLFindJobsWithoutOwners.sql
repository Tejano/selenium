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


SELECT 
    j.name AS job_name,
    j.job_id,
    j.owner_sid,
    SUSER_SNAME(j.owner_sid) AS owner_name,
    js.step_id,
    js.step_name,
    js.command AS step_command,
    CASE 
        WHEN sp.sid IS NULL THEN 'ORPHANED OWNER'
        ELSE 'VALID OWNER'
    END AS owner_status
FROM 
    msdb.dbo.sysjobs AS j
LEFT JOIN 
    sys.server_principals AS sp ON j.owner_sid = sp.sid
INNER JOIN 
    msdb.dbo.sysjobsteps AS js ON j.job_id = js.job_id
WHERE 
    js.subsystem = 'SSIS'
    AND js.command LIKE '%\SSISDB\commission\%' 
    AND sp.sid IS NULL  -- means the login no longer exists in the server
ORDER BY 
    j.name;


-- Set new valid owner SID
DECLARE @NewOwnerSID VARBINARY(85);

SELECT @NewOwnerSID = sid
FROM sys.server_principals 
WHERE name = 'your_domain\new_owner_login';  -- replace with your login

-- Update orphaned job owners
UPDATE j
SET j.owner_sid = @NewOwnerSID
FROM msdb.dbo.sysjobs AS j
LEFT JOIN sys.server_principals AS sp ON j.owner_sid = sp.sid
INNER JOIN msdb.dbo.sysjobsteps AS js ON j.job_id = js.job_id
WHERE 
    js.subsystem = 'SSIS'
    AND js.command LIKE '%\SSISDB\commission\%' 
    AND sp.sid IS NULL;

--///////////////////////////////////////
-- [ STEP 1: CONFIGURATION ]
-- Replace with the login that should become the new owner
DECLARE @NewOwnerName SYSNAME = N'MYDOMAIN\your_user';  -- <-- CHANGE THIS
DECLARE @NewOwnerSID VARBINARY(85);

-- [ STEP 2: GET THE SID OF THE NEW OWNER ]
SELECT @NewOwnerSID = sid
FROM sys.server_principals
WHERE name = @NewOwnerName;

IF @NewOwnerSID IS NULL
BEGIN
    RAISERROR('❌ ERROR: Login [%s] not found in sys.server_principals. Aborting.', 16, 1, @NewOwnerName);
    RETURN;
END

-- [ STEP 3: START TRANSACTION ]
BEGIN TRANSACTION;

-- [ STEP 4: SHOW JOBS THAT WILL BE UPDATED ]
PRINT '🔍 Preview: The following jobs will be updated to use owner [' + @NewOwnerName + ']';

SELECT 
    j.name AS job_name,
    j.job_id,
    SUSER_SNAME(j.owner_sid) AS current_owner,  -- NULL if orphaned
    js.step_id,
    js.step_name,
    js.command AS step_command,
    'Will be reassigned to: ' + @NewOwnerName AS new_owner
FROM 
    msdb.dbo.sysjobs AS j
LEFT JOIN 
    sys.server_principals AS sp ON j.owner_sid = sp.sid
INNER JOIN 
    msdb.dbo.sysjobsteps AS js ON j.job_id = js.job_id
WHERE 
    js.subsystem = 'SSIS'
    -- [ STEP 1: CONFIGURATION ]
-- Replace with the login that should become the new owner
DECLARE @NewOwnerName SYSNAME = N'MYDOMAIN\your_user';  -- <-- CHANGE THIS
DECLARE @NewOwnerSID VARBINARY(85);

-- [ STEP 2: GET THE SID OF THE NEW OWNER ]
SELECT @NewOwnerSID = sid
FROM sys.server_principals
WHERE name = @NewOwnerName;

IF @NewOwnerSID IS NULL
BEGIN
    RAISERROR('❌ ERROR: Login [%s] not found in sys.server_principals. Aborting.', 16, 1, @NewOwnerName);
    RETURN;
END

-- [ STEP 3: START TRANSACTION ]
BEGIN TRANSACTION;

-- [ STEP 4: SHOW JOBS THAT WILL BE UPDATED ]
PRINT '🔍 Preview: The following jobs will be updated to use owner [' + @NewOwnerName + ']';

SELECT 
    j.name AS job_name,
    j.job_id,
    SUSER_SNAME(j.owner_sid) AS current_owner,  -- NULL if orphaned
    js.step_id,
    js.step_name,
    js.command AS step_command,
    'Will be reassigned to: ' + @NewOwnerName AS new_owner
FROM 
    msdb.dbo.sysjobs AS j
LEFT JOIN 
    sys.server_principals AS sp ON j.owner_sid = sp.sid
INNER JOIN 
    msdb.dbo.sysjobsteps AS js ON j.job_id = js.job_id
WHERE 
    js.subsystem = 'SSIS'
    AND js.command LIKE '%\SSISDB\commission\%'
    AND sp.sid IS NULL;

-- [ STEP 5: APPLY THE UPDATE ]
-- COMMENT THIS OUT IF YOU WANT A DRY RUN ONLY
UPDATE j
SET j.owner_sid = @NewOwnerSID
FROM msdb.dbo.sysjobs AS j
LEFT JOIN sys.server_principals AS sp ON j.owner_sid = sp.sid
INNER JOIN msdb.dbo.sysjobsteps AS js ON j.job_id = js.job_id
WHERE 
    js.subsystem = 'SSIS'
    AND js.command LIKE '%\SSISDB\commission\%'
    AND sp.sid IS NULL;

PRINT '✅ Job owner_sid has been updated in the transaction.';

-- [ STEP 6: WAIT FOR DBA TO COMMIT OR ROLLBACK ]
-- 🛑 DBA must manually run one of the following:

-- COMMIT TRANSACTION;   -- <--- to apply the change
-- ROLLBACK TRANSACTION; -- <--- to cancel the change

    AND sp.sid IS NULL;

-- [ STEP 5: APPLY THE UPDATE ]
-- COMMENT THIS OUT IF YOU WANT A DRY RUN ONLY
UPDATE j
SET j.owner_sid = @NewOwnerSID
FROM msdb.dbo.sysjobs AS j
LEFT JOIN sys.server_principals AS sp ON j.owner_sid = sp.sid
INNER JOIN msdb.dbo.sysjobsteps AS js ON j.job_id = js.job_id
WHERE 
    js.subsystem = 'SSIS'
    AND js.command LIKE '%\SSISDB\ssisdbfolder\%'
    AND sp.sid IS NULL;

PRINT '✅ Job owner_sid has been updated in the transaction.';

-- [ STEP 6: WAIT FOR DBA TO COMMIT OR ROLLBACK ]
-- 🛑 DBA must manually run one of the following:

-- COMMIT TRANSACTION;   -- <--- to apply the change
-- ROLLBACK TRANSACTION; -- <--- to cancel the change
