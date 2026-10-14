package cmd

import (
	"os"
	"path/filepath"
	"testing"
)

func TestScanForSecrets_DetectsGitHubToken(t *testing.T) {
	dir := t.TempDir()
	mustWrite(t, filepath.Join(dir, "config.py"), `TOKEN = "ghp_abcdefghijklmnopqrstuvwxyz0123456789"`) // secscan:ignore (segredo falso, usado só para testar a detecção)

	result, err := scanForSecrets(dir)
	if err != nil {
		t.Fatalf("erro inesperado: %v", err)
	}

	if result.CriticalCount != 1 {
		t.Fatalf("esperado 1 finding CRITICAL, obteve %d: %+v", result.CriticalCount, result.Findings)
	}
	if result.Findings[0].Rule != "GitHub Personal Access Token (classic)" {
		t.Errorf("regra inesperada: %s", result.Findings[0].Rule)
	}
}

func TestScanForSecrets_DetectsPrivateKeyHeader(t *testing.T) {
	dir := t.TempDir()
	mustWrite(t, filepath.Join(dir, "id_rsa"), "-----BEGIN RSA PRIVATE KEY-----\nMIIExx...\n-----END RSA PRIVATE KEY-----") // secscan:ignore (chave falsa, usada só para testar a detecção)

	result, err := scanForSecrets(dir)
	if err != nil {
		t.Fatalf("erro inesperado: %v", err)
	}

	if result.CriticalCount != 1 {
		t.Fatalf("esperado 1 finding CRITICAL, obteve %d", result.CriticalCount)
	}
}

func TestScanForSecrets_GenericPatternIsOnlyWarning(t *testing.T) {
	dir := t.TempDir()
	mustWrite(t, filepath.Join(dir, "settings.py"), `password = "umaSenhaQualquer123"`) // secscan:ignore (senha falsa, usada só para testar a detecção)

	result, err := scanForSecrets(dir)
	if err != nil {
		t.Fatalf("erro inesperado: %v", err)
	}

	if result.CriticalCount != 0 {
		t.Errorf("padrão genérico não deveria contar como CRITICAL, obteve %d", result.CriticalCount)
	}
	if result.WarningCount != 1 {
		t.Errorf("esperado 1 WARNING, obteve %d", result.WarningCount)
	}
}

func TestScanForSecrets_CleanCodeHasNoFindings(t *testing.T) {
	dir := t.TempDir()
	mustWrite(t, filepath.Join(dir, "main.go"), "package main\n\nfunc main() {}\n")

	result, err := scanForSecrets(dir)
	if err != nil {
		t.Fatalf("erro inesperado: %v", err)
	}

	if len(result.Findings) != 0 {
		t.Errorf("esperado nenhum finding, obteve: %+v", result.Findings)
	}
}

func TestRunSecscan_ReturnsNonZeroOnCritical(t *testing.T) {
	dir := t.TempDir()
	mustWrite(t, filepath.Join(dir, "leak.txt"), "AKIAABCDEFGHIJKLMNOP") // secscan:ignore (chave falsa, usada só para testar a detecção)

	exitCode := runSecscan([]string{"-path", dir})

	if exitCode != 1 {
		t.Errorf("esperado exit code 1 com CRITICAL presente, obteve %d", exitCode)
	}
}

func TestScanForSecrets_IgnoreMarkerSuppressesLine(t *testing.T) {
	dir := t.TempDir()
	mustWrite(t, filepath.Join(dir, "example.py"),
		`FAKE_TOKEN = "ghp_abcdefghijklmnopqrstuvwxyz0123456789"  # secscan:ignore`)

	result, err := scanForSecrets(dir)
	if err != nil {
		t.Fatalf("erro inesperado: %v", err)
	}

	if len(result.Findings) != 0 {
		t.Errorf("linha marcada com secscan:ignore não deveria gerar finding, obteve: %+v", result.Findings)
	}
}

func TestRunSecscan_JSONOutput(t *testing.T) {
	dir := t.TempDir()
	mustWrite(t, filepath.Join(dir, "clean.go"), "package main")
	jsonPath := filepath.Join(t.TempDir(), "result.json")

	exitCode := runSecscan([]string{"-path", dir, "-json-out", jsonPath})

	if exitCode != 0 {
		t.Fatalf("esperado exit code 0, obteve %d", exitCode)
	}

	if _, err := os.Stat(jsonPath); err != nil {
		t.Fatalf("arquivo JSON não foi criado: %v", err)
	}
}
