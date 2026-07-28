{{- define "ecms.labels" -}}
app.kubernetes.io/name: ecms
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end -}}
