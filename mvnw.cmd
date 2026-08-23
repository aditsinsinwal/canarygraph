@ECHO OFF
SETLOCAL
SET "PROJECT_DIR=%~dp0"
SET "WRAPPER_JAR=%PROJECT_DIR%.mvn\wrapper\maven-wrapper.jar"
SET "WRAPPER_URL=https://repo.maven.apache.org/maven2/org/apache/maven/wrapper/maven-wrapper/3.3.4/maven-wrapper-3.3.4.jar"
SET "WRAPPER_SHA256=4e2fbf6554bc8a4702cdfdd3bef464f423393d784ddbb037216320ce55d5e4e1"

IF NOT EXIST "%WRAPPER_JAR%" (
  WHERE curl >NUL 2>NUL
  IF ERRORLEVEL 1 (
    ECHO Cannot download Maven Wrapper: install curl. 1>&2
    EXIT /B 1
  )
  curl --fail --location --silent --show-error "%WRAPPER_URL%" --output "%WRAPPER_JAR%"
  IF ERRORLEVEL 1 EXIT /B 1
)

FOR /F "tokens=*" %%H IN ('powershell -NoProfile -Command "(Get-FileHash -Algorithm SHA256 '%WRAPPER_JAR%').Hash.ToLower()"') DO SET "ACTUAL_SHA256=%%H"
IF /I NOT "%ACTUAL_SHA256%"=="%WRAPPER_SHA256%" (
  ECHO Maven Wrapper checksum verification failed. 1>&2
  EXIT /B 1
)

IF DEFINED JAVA_HOME (
  SET "JAVA_COMMAND=%JAVA_HOME%\bin\java.exe"
) ELSE (
  SET "JAVA_COMMAND=java.exe"
)

"%JAVA_COMMAND%" -Dmaven.multiModuleProjectDirectory="%PROJECT_DIR%" -classpath "%WRAPPER_JAR%" org.apache.maven.wrapper.MavenWrapperMain %*
EXIT /B %ERRORLEVEL%
