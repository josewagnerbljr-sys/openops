// Comando secscan: varre um diretório em busca de segredos vazados
// (chaves de API, tokens, chaves privadas) usando padrões de alta
// confiança. Serve tanto para uso local (antes de um `git push`) quanto
// para o workflow de validação de PR no GitHub Actions.
//
// Filosofia: apenas padrões com formato muito específico (ex.: prefixo
// "ghp_" de 36 caracteres, cabeçalho de chave privada PEM) são
// classificados como CRITICAL — o suficiente para justificar rejeição
// automática de PR. Padrões genéricos ("password=", "api_key=") viram
// WARNING: sinalizados, nunca usados para rejeitar automaticamente,
// porque geram falsos positivos com facilidade demais.
package cmd

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

type secretRule struct {
	Name     string
	Severity string // "CRITICAL" ou "WARNING"
	Pattern  *regexp.Regexp
}

var secretRules = []secretRule{
	{"AWS Access Key ID", "CRITICAL", regexp.MustCompile(`AKIA[0-9A-Z]{16}`)},
	{"GitHub Personal Access Token (classic)", "CRITICAL", regexp.MustCompile(`ghp_[A-Za-z0-9]{36}`)},
	{"GitHub Fine-grained Token", "CRITICAL", regexp.MustCompile(`github_pat_[A-Za-z0-9_]{82}`)},
	{"Chave privada PEM", "CRITICAL", regexp.MustCompile(`-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----`)},
	{"Stripe Live Secret Key", "CRITICAL", regexp.MustCompile(`sk_live_[0-9a-zA-Z]{20,}`)},
	{"Slack Token", "CRITICAL", regexp.MustCompile(`xox[baprs]-[0-9A-Za-z-]{10,}`)},
	{"Google API Key", "CRITICAL", regexp.MustCompile(`AIza[0-9A-Za-z_-]{35}`)},
	{"Possível segredo genérico (variável de ambiente)", "WARNING", regexp.MustCompile(`(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*["'][A-Za-z0-9+/_=-]{12,}["']`)},
}

type secretFinding struct {
	File     string `json:"file"`
	Line     int    `json:"line"`
	Rule     string `json:"rule"`
	Severity string `json:"severity"`
}

type secscanResult struct {
	CriticalCount int             `json:"critical_count"`
	WarningCount  int             `json:"warning_count"`
	Findings      []secretFinding `json:"findings"`
}

func init() {
	Register(&Command{
		Name:        "secscan",
		Description: "Varre um diretório em busca de segredos vazados (chaves, tokens, credenciais)",
		Run:         runSecscan,
	})
}

func runSecscan(args []string) int {
	fs := newFlagSet("secscan")
	target := fs.String("path", ".", "diretório raiz a ser varrido")
	jsonOut := fs.String("json-out", "", "caminho opcional para salvar o resultado em JSON")
	_ = fs.Parse(args)

	result, err := scanForSecrets(*target)
	if err != nil {
		fmt.Fprintf(os.Stderr, "erro ao varrer %s: %v\n", *target, err)
		return 1
	}

	for _, f := range result.Findings {
		fmt.Printf("%-8s %-45s %s:%d\n", f.Severity, f.Rule, f.File, f.Line)
	}
	fmt.Printf("\nCRITICAL %d | WARNING %d\n", result.CriticalCount, result.WarningCount)

	if *jsonOut != "" {
		data, _ := json.MarshalIndent(result, "", "  ")
		if err := os.WriteFile(*jsonOut, data, 0o644); err != nil {
			fmt.Fprintf(os.Stderr, "erro ao escrever %s: %v\n", *jsonOut, err)
			return 1
		}
	}

	if result.CriticalCount > 0 {
		return 1
	}
	return 0
}

func scanForSecrets(root string) (*secscanResult, error) {
	result := &secscanResult{Findings: []secretFinding{}}

	err := filepath.Walk(root, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if info.IsDir() {
			if excludedDirs[info.Name()] {
				return filepath.SkipDir
			}
			return nil
		}
		if info.Size() > maxFileSize || info.Size() == 0 {
			return nil
		}

		data, readErr := os.ReadFile(path)
		if readErr != nil || looksBinary(data) {
			return nil
		}

		rel, relErr := filepath.Rel(root, path)
		if relErr != nil {
			rel = path
		}
		rel = filepath.ToSlash(rel)

		lines := strings.Split(string(data), "\n")
		for lineNum, line := range lines {
			if strings.Contains(line, "secscan:ignore") {
				continue
			}
			for _, rule := range secretRules {
				if rule.Pattern.MatchString(line) {
					finding := secretFinding{
						File:     rel,
						Line:     lineNum + 1,
						Rule:     rule.Name,
						Severity: rule.Severity,
					}
					result.Findings = append(result.Findings, finding)
					if rule.Severity == "CRITICAL" {
						result.CriticalCount++
					} else {
						result.WarningCount++
					}
				}
			}
		}
		return nil
	})

	return result, err
}
