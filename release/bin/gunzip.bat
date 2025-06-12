@echo off
REM gunzip wrapper - calls gzip with decompression flag
"%~dp0gzip.exe" -d %*

