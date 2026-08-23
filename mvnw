#!/bin/sh

set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
wrapper_jar="$project_dir/.mvn/wrapper/maven-wrapper.jar"
wrapper_url="https://repo.maven.apache.org/maven2/org/apache/maven/wrapper/maven-wrapper/3.3.4/maven-wrapper-3.3.4.jar"
wrapper_sha256="4e2fbf6554bc8a4702cdfdd3bef464f423393d784ddbb037216320ce55d5e4e1"

verify_wrapper() {
    if command -v sha256sum >/dev/null 2>&1; then
        actual_sha256=$(sha256sum "$wrapper_jar" | awk '{print $1}')
    elif command -v shasum >/dev/null 2>&1; then
        actual_sha256=$(shasum -a 256 "$wrapper_jar" | awk '{print $1}')
    else
        echo "Cannot verify Maven Wrapper: install sha256sum or shasum." >&2
        exit 1
    fi
    if [ "$actual_sha256" != "$wrapper_sha256" ]; then
        echo "Maven Wrapper checksum verification failed." >&2
        exit 1
    fi
}

if [ ! -r "$wrapper_jar" ]; then
    temporary_jar="$wrapper_jar.tmp.$$"
    trap 'rm -f "$temporary_jar"' EXIT HUP INT TERM
    if command -v curl >/dev/null 2>&1; then
        curl --fail --location --silent --show-error "$wrapper_url" --output "$temporary_jar"
    elif command -v wget >/dev/null 2>&1; then
        wget --quiet "$wrapper_url" --output-document="$temporary_jar"
    else
        echo "Cannot download Maven Wrapper: install curl or wget." >&2
        exit 1
    fi
    mv "$temporary_jar" "$wrapper_jar"
    trap - EXIT HUP INT TERM
fi

verify_wrapper

if [ -n "${JAVA_HOME:-}" ]; then
    java_command="$JAVA_HOME/bin/java"
else
    java_command="java"
fi

exec "$java_command" \
    -Dmaven.multiModuleProjectDirectory="$project_dir" \
    -classpath "$wrapper_jar" \
    org.apache.maven.wrapper.MavenWrapperMain "$@"
