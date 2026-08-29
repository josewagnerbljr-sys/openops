package cmd

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestCollectSourceFiles_FindsAndSkipsCorrectly(t *testing.T) {
	dir := t.TempDir()

	mustWrite(t, filepath.Join(dir, "main.py"), "print('oi')")
	mustWrite(t, filepath.Join(dir, "README.txt"), "sem linguagem reconhecida, mas ainda texto")

	skipDir := filepath.Join(dir, "node_modules")
	if err := os.Mkdir(skipDir, 0o755); err != nil {
		t.Fatal(err)
	}
	mustWrite(t, filepath.Join(skipDir, "lib.js"), "não deveria aparecer")

	files, err := collectSourceFiles(dir)
	if err != nil {
		t.Fatalf("erro inesperado: %v", err)
	}

	if len(files) != 2 {
		t.Fatalf("esperado 2 arquivos, obteve %d: %+v", len(files), files)
	}

	for _, f := range files {
		if strings.Contains(f.RelPath, "node_modules") {
			t.Errorf("node_modules não deveria ter sido incluído: %s", f.RelPath)
		}
	}
}

func TestCollectSourceFiles_SkipsBinaryContent(t *testing.T) {
	dir := t.TempDir()

	binPath := filepath.Join(dir, "image.bin")
	if err := os.WriteFile(binPath, []byte{0x00, 0x01, 0x02, 0x03}, 0o644); err != nil {
		t.Fatal(err)
	}
	mustWrite(t, filepath.Join(dir, "ok.go"), "package main")

	files, err := collectSourceFiles(dir)
	if err != nil {
		t.Fatalf("erro inesperado: %v", err)
	}

	if len(files) != 1 || files[0].RelPath != "ok.go" {
		t.Errorf("esperado apenas ok.go, obteve: %+v", files)
	}
}

func TestRunDocgen_GeneratesValidHTMLFile(t *testing.T) {
	srcDir := t.TempDir()
	mustWrite(t, filepath.Join(srcDir, "main.go"), "package main\n\nfunc main() {}\n")

	outFile := filepath.Join(t.TempDir(), "report.html")

	exitCode := runDocgen([]string{"-path", srcDir, "-out", outFile, "-title", "Teste"})

	if exitCode != 0 {
		t.Fatalf("esperado exit code 0, obteve %d", exitCode)
	}

	content, err := os.ReadFile(outFile)
	if err != nil {
		t.Fatalf("arquivo de saída não foi criado: %v", err)
	}

	html := string(content)
	if !strings.Contains(html, "<!DOCTYPE html>") {
		t.Error("saída não parece um documento HTML válido")
	}
	if !strings.Contains(html, "main.go") {
		t.Error("nome do arquivo-fonte não aparece no relatório")
	}
	if !strings.Contains(html, "Teste") {
		t.Error("título customizado não aparece no relatório")
	}
}

func mustWrite(t *testing.T, path, content string) {
	t.Helper()
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatalf("falha ao escrever arquivo de teste %s: %v", path, err)
	}
}
