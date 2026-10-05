#!/bin/sh
set -eu
cd "$(dirname "$0")/../../.."
BUILD=$(mktemp -d)
trap 'rm -rf "$BUILD"' EXIT HUP INT TERM
javac -encoding UTF-8 -d "$BUILD" \
  software/core/src/main/java/org/qulay/core/Model.java \
  software/core/src/main/java/org/qulay/core/ContactModel.java \
  software/core/src/main/java/org/qulay/core/Geometry.java \
  software/agent/src/main/java/org/qulay/agent/Wire.java \
  software/agent/src/main/java/org/qulay/agent/WireV2.java \
  docs/sensors/tools/SensorGuideCheck.java
java -cp "$BUILD" SensorGuideCheck docs/sensors/generated
