// Package tokenizer - Language dictionaries
//
// Lead Architect: Juan Carlos
// Co-Author: Claude (MAXIMUS)
package tokenizer

import "github.com/verticedev/vcli-go/pkg/nlp"

// getVerbDictionary returns verb mappings for language
// Maps natural language verbs to canonical English verbs
func getVerbDictionary(lang nlp.Language) map[string]string {
	switch lang {
	case nlp.LanguagePTBR:
		return map[string]string{
			// Query verbs
			"mostra":   "show",
			"lista":    "list",
			"exibe":    "show",
			"ver":      "show",
			"busca":    "get",
			"obter":    "get",
			"pega":     "get",
			"describe": "describe",
			"descreve": "describe",

			// Action verbs
			"cria":     "create",
			"criar":    "create",
			"deleta":   "delete",
			"deletar":  "delete",
			"remove":   "delete",
			"remover":  "delete",
			"escala":   "scale",
			"escalar":  "scale",
			"escalona": "scale",
			"aplica":   "apply",
			"aplicar":  "apply",
			"atualiza": "update",
			"patch":    "patch",

			// Investigation
			"investiga":  "investigate",
			"investigar": "investigate",
			"analisa":    "analyze",
			"analisar":   "analyze",
			"debuga":     "debug",

			// Orchestration
			"executa":  "execute",
			"executar": "execute",
			"roda":     "run",
			"rodar":    "run",
			"inicia":   "start",
			"iniciar":  "start",
		}
	case nlp.LanguageEN:
		return map[string]string{
			"show":        "show",
			"list":        "list",
			"get":         "get",
			"describe":    "describe",
			"create":      "create",
			"delete":      "delete",
			"remove":      "delete",
			"scale":       "scale",
			"apply":       "apply",
			"update":      "update",
			"patch":       "patch",
			"investigate": "investigate",
			"analyze":     "analyze",
			"debug":       "debug",
			"execute":     "execute",
			"run":         "run",
			"start":       "start",
		}
	default:
		return make(map[string]string)
	}
}

// getNounDictionary returns noun mappings for language
// Maps natural language resource names to Kubernetes resource types
func getNounDictionary(lang nlp.Language) map[string]string {
	switch lang {
	case nlp.LanguagePTBR:
		return map[string]string{
			// K8s resources
			"pod":          "pods",
			"pods":         "pods",
			"deployment":   "deployments",
			"deployments":  "deployments",
			"service":      "services",
			"services":     "services",
			"servico":      "services",
			"servicos":     "services",
			"namespace":    "namespaces",
			"namespaces":   "namespaces",
			"configmap":    "configmaps",
			"configmaps":   "configmaps",
			"secret":       "secrets",
			"secrets":      "secrets",
			"segredo":      "secrets",
			"segredos":     "secrets",
			"node":         "nodes",
			"nodes":        "nodes",
			"no":           "nodes",
			"nos":          "nodes",
			"ingress":      "ingresses",
			"ingresses":    "ingresses",
			"statefulset":  "statefulsets",
			"statefulsets": "statefulsets",
			"daemonset":    "daemonsets",
			"daemonsets":   "daemonsets",
			"job":          "jobs",
			"jobs":         "jobs",
			"cronjob":      "cronjobs",
			"cronjobs":     "cronjobs",
		}
	case nlp.LanguageEN:
		return map[string]string{
			"pod":          "pods",
			"pods":         "pods",
			"deployment":   "deployments",
			"deployments":  "deployments",
			"service":      "services",
			"services":     "services",
			"namespace":    "namespaces",
			"namespaces":   "namespaces",
			"configmap":    "configmaps",
			"configmaps":   "configmaps",
			"secret":       "secrets",
			"secrets":      "secrets",
			"node":         "nodes",
			"nodes":        "nodes",
			"ingress":      "ingresses",
			"ingresses":    "ingresses",
			"statefulset":  "statefulsets",
			"statefulsets": "statefulsets",
			"daemonset":    "daemonsets",
			"daemonsets":   "daemonsets",
			"job":          "jobs",
			"jobs":         "jobs",
			"cronjob":      "cronjobs",
			"cronjobs":     "cronjobs",
		}
	default:
		return make(map[string]string)
	}
}

// getFilterDictionary returns filter keywords
// Maps natural language status/condition words to K8s field selectors
func getFilterDictionary(lang nlp.Language) map[string]string {
	switch lang {
	case nlp.LanguagePTBR:
		return map[string]string{
			"problema":  "error",
			"problemas": "error",
			"erro":      "error",
			"erros":     "error",
			"falha":     "failed",
			"falhas":    "failed",
			"falhando":  "failing",
			"quebrado":  "failed",
			"quebrados": "failed",
			"rodando":   "running",
			"pausado":   "paused",
			"pendente":  "pending",
			"completo":  "completed",
			"completos": "completed",
		}
	case nlp.LanguageEN:
		return map[string]string{
			"problem":   "error",
			"problems":  "error",
			"error":     "error",
			"errors":    "error",
			"failed":    "failed",
			"failing":   "failing",
			"broken":    "failed",
			"running":   "running",
			"paused":    "paused",
			"pending":   "pending",
			"completed": "completed",
		}
	default:
		return make(map[string]string)
	}
}

// getPrepositionDictionary returns prepositions
func getPrepositionDictionary(lang nlp.Language) map[string]string {
	switch lang {
	case nlp.LanguagePTBR:
		return map[string]string{
			"com":  "with",
			"pra":  "to",
			"para": "to",
			"em":   "in",
			"por":  "by",
		}
	case nlp.LanguageEN:
		return map[string]string{
			"with": "with",
			"to":   "to",
			"in":   "in",
			"by":   "by",
		}
	default:
		return make(map[string]string)
	}
}
