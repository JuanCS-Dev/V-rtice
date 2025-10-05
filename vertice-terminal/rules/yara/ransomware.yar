/*
    YARA Rule: Ransomware Detection
    Author: Security Team
    Description: Detecta comportamentos típicos de ransomware
*/

rule Ransomware_Generic {
    meta:
        description = "Generic ransomware behavior detection"
        author = "Vertice Security Team"
        severity = "critical"
        mitre_attack = "T1486"

    strings:
        $encrypt1 = "CryptEncrypt" nocase
        $encrypt2 = "AES" nocase
        $encrypt3 = "RSA" nocase

        $ransom1 = "bitcoin" nocase
        $ransom2 = "decrypt" nocase
        $ransom3 = "ransom" nocase

        $file1 = ".encrypted"
        $file2 = ".locked"
        $file3 = ".crypted"

    condition:
        (2 of ($encrypt*)) and (1 of ($ransom*)) or (1 of ($file*))
}

rule Ransomware_WannaCry {
    meta:
        description = "WannaCry ransomware detection"
        author = "Vertice Security Team"
        severity = "critical"
        reference = "https://www.microsoft.com/security/blog/wannacry"

    strings:
        $s1 = "tasksche.exe" nocase
        $s2 = "www.iuqerfsodp9ifjaposdfjhgosurijfaewrwergwea.com"
        $s3 = "msg/m_portuguese.wnry"
        $s4 = "WNcry@2ol7"

    condition:
        2 of them
}

rule Mimikatz_Detection {
    meta:
        description = "Detecta uso de Mimikatz para credential dumping"
        author = "Vertice Security Team"
        severity = "critical"
        mitre_attack = "T1003"

    strings:
        $s1 = "sekurlsa::logonpasswords" nocase
        $s2 = "lsadump::sam" nocase
        $s3 = "privilege::debug" nocase
        $s4 = "gentilkiwi"

    condition:
        any of them
}

rule Suspicious_PowerShell {
    meta:
        description = "Detecta PowerShell suspeito"
        author = "Vertice Security Team"
        severity = "high"
        mitre_attack = "T1059.001"

    strings:
        $download1 = "Net.WebClient" nocase
        $download2 = "DownloadString" nocase
        $download3 = "DownloadFile" nocase

        $exec1 = "IEX" nocase
        $exec2 = "Invoke-Expression" nocase

        $obfusc1 = "-enc" nocase
        $obfusc2 = "FromBase64String" nocase

    condition:
        (1 of ($download*)) and (1 of ($exec*)) or (1 of ($obfusc*))
}

rule Cobalt_Strike_Beacon {
    meta:
        description = "Detecta Cobalt Strike Beacon"
        author = "Vertice Security Team"
        severity = "critical"
        reference = "https://attack.mitre.org/software/S0154/"

    strings:
        $s1 = "%c%c%c%c%c%c%c%c%cMSSE-%d-server"
        $s2 = "beacon.dll" nocase
        $s3 = "%s (admin)" fullword
        $s4 = "IEX (New-Object Net.Webclient).DownloadString"

    condition:
        any of them
}
