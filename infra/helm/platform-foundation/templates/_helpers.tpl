{{- /*
Sprint 1 foundation chart helpers.
*/ -}}
{{- define "platform-foundation.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "platform-foundation.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "platform-foundation.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
