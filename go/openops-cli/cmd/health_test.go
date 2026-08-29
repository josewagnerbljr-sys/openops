package cmd

import (
	"os"
	"path/filepath"
	"testing"
)

func TestRequireFile_Present(t *testing.T) {
	dir := t.TempDir()
	if err := os.WriteFile(filepath.Join(dir, "README.md"), []byte("# hi"), 0o644); err != nil {
		t.Fatal(err)
	}

	check := requireFile(dir, "README.md", "detalhe")

	if check.Severity != "PASS" {
		t.Errorf("esperado PASS, obteve %s", check.Severity)
	}
}

func TestRequireFile_Missing(t *testing.T) {
	dir := t.TempDir()

	check := requireFile(dir, "README.md", "detalhe")

	if check.Severity != "WARNING" {
		t.Errorf("esperado WARNING, obteve %s", check.Severity)
	}
}

func TestRequireDir_Present(t *testing.T) {
	dir := t.TempDir()
	if err := os.Mkdir(filepath.Join(dir, "workflows"), 0o755); err != nil {
		t.Fatal(err)
	}

	check := requireDir(dir, "workflows", "detalhe")

	if check.Severity != "PASS" {
		t.Errorf("esperado PASS, obteve %s", check.Severity)
	}
}

func TestRunHealth_ReturnsNonZeroOnlyWhenCritical(t *testing.T) {
	dir := t.TempDir()

	exitCode := runHealth([]string{"-path", dir})

	// Ausência de arquivos hoje gera apenas WARNING, nunca CRITICAL,
	// então o exit code esperado é 0.
	if exitCode != 0 {
		t.Errorf("esperado exit code 0 (sem critical), obteve %d", exitCode)
	}
}
