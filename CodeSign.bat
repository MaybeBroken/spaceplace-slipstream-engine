signtool.exe sign /a /tr http://timestamp.digicert.com /td SHA256 /fd SHA256 /v /d "David Sponseller" ./"SlipstreamEngineInstaller.exe"
signtool.exe sign /a /tr http://timestamp.digicert.com /td SHA256 /fd SHA256 /v /d "David Sponseller" ./"SlipstreamEngine.exe"
pause