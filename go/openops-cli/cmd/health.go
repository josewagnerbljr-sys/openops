package cmd

import (
	"fmt"
	"os"
	"path/filepath"
)

// healthCheck representa uma verificação individual do Structural Health
// Engine. Esta é a primeira fatia real (Fase 0/1) do motor completo
// descrito no item 12 do documento mestre — cresce incrementalmente nas
// fases seguintes (imports, dependências, AST, migrations, etc.).
type healthCheck struct {
	Name     string
	Severity string // "PASS", "WARNING" ou "CRITICAL"
	Detail   string
}

func init() {
	Register(&Command{
		Name:        "health",
		Description: "Executa um check-up estrutural básico do repositório",
		Run:         runHealth,
	})
}

func runHealth(args []string) int {
	fs := newFlagSet("health")
	target := fs.String("path", ".", "diretório raiz do repositório a analisar")
	_ = fs.Parse(args)

	checks := []healthCheck{
		requireFile(*target, "README.md", "Documentação de entrada do projeto"),
		requireFile(*target, "LICENSE", "Licença open source explícita"),
		requireFile(*target, "SECURITY.md", "Processo público de reporte de vulnerabilidades"),
		requireFile(*target, "THREAT_MODEL.md", "Análise formal de ameaças (STRIDE)"),
		requireFile(*target, "MANUAL_DE_USO_API.md", "Guia passo a passo de uso da API"),
		requireFile(*target, "CONTRIBUTING.md", "Guia de contribuição"),
		requireDir(*target, ".github/workflows", "Pipeline de CI configurado"),
	}

	critical, warnings := 0, 0
	for _, c := range checks {
		fmt.Printf("%-10s %-40s %s\n", c.Severity, c.Name, c.Detail)
		switch c.Severity {
		case "CRITICAL":
			critical++
		case "WARNING":
			warnings++
		}
	}

	total := len(checks)
	passed := total - critical - warnings
	score := 0
	if total > 0 {
		score = (passed * 100) / total
	}

	fmt.Println()
	fmt.Printf("CRITICAL %d | WARNINGS %d | HEALTH %d%%\n", critical, warnings, score)

	if critical > 0 {
		return 1
	}
	return 0
}

func requireFile(root, relPath, detail string) healthCheck {
	full := filepath.Join(root, relPath)
	info, err := os.Stat(full)
	if err != nil || info.IsDir() {
		return healthCheck{Name: relPath, Severity: "WARNING", Detail: detail + " (ausente)"}
	}
	return healthCheck{Name: relPath, Severity: "PASS", Detail: detail}
}

func requireDir(root, relPath, detail string) healthCheck {
	full := filepath.Join(root, relPath)
	info, err := os.Stat(full)
	if err != nil || !info.IsDir() {
		return healthCheck{Name: relPath, Severity: "WARNING", Detail: detail + " (ausente)"}
	}
	return healthCheck{Name: relPath, Severity: "PASS", Detail: detail}
}
