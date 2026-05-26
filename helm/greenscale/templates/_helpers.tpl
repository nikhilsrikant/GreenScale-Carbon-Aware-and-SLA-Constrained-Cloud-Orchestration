{{- define "greenscale.name" -}}greenscale{{- end -}}
{{- define "greenscale.namespace" -}}{{ default .Release.Namespace .Values.namespaceOverride }}{{- end -}}
{{- define "greenscale.orchestratorImage" -}}{{ .Values.images.orchestrator.repository }}:{{ .Values.images.orchestrator.tag }}{{- end -}}
{{- define "greenscale.workerImage" -}}{{ .Values.images.worker.repository }}:{{ .Values.images.worker.tag }}{{- end -}}
{{- define "greenscale.regionEndpoints" -}}
[
{{- $ns := include "greenscale.namespace" . -}}
{{- range $i, $r := .Values.regions }}
  {{- if $i }},{{ end }}{"name":"{{ $r.name }}","provider":"{{ $r.provider }}","url":"http://{{ $r.serviceName }}.{{ $ns }}.svc.cluster.local:9000","zone":"{{ $r.zone }}","base_latency_ms":{{ $r.baseLatencyMs }},"carbon_gco2_kwh":{{ $r.carbonGco2Kwh }},"cost_per_million_requests":{{ $r.costPerMillionRequests }},"cold_start_ms":{{ $r.coldStartMs }},"capacity_weight":1.0}
{{- end }}
]
{{- end -}}
