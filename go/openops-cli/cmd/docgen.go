// Comando docgen: gera um relatório HTML autocontido (sem dependências
// externas, sem CDN) a partir do código-fonte de um diretório, detectando
// a linguagem de cada arquivo pela extensão e aplicando realce de
// sintaxe. Pensado para demonstrações, portfólio e documentação rápida
// de qualquer projeto — não só do próprio OpenOps.
package cmd

import (
	"bytes"
	"fmt"
	"html"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

var excludedDirs = map[string]bool{
	".git": true, "target": true, "node_modules": true,
	"__pycache__": true, ".pytest_cache": true, "dist": true,
	"build": true, ".venv": true, "venv": true,
}

const maxFileSize = 300 * 1024 // 300 KB por arquivo

func init() {
	Register(&Command{
		Name:        "docgen",
		Description: "Gera um relatório HTML com realce de sintaxe a partir de um diretório de código",
		Run:         runDocgen,
	})
}

type sourceFile struct {
	RelPath string
	Lang    string
	Content string
}

func runDocgen(args []string) int {
	fs := newFlagSet("docgen")
	src := fs.String("path", ".", "diretório raiz do código-fonte a documentar")
	out := fs.String("out", "openops-docs.html", "caminho do arquivo HTML de saída")
	title := fs.String("title", "Relatório de Código", "título do documento gerado")
	_ = fs.Parse(args)

	files, err := collectSourceFiles(*src)
	if err != nil {
		fmt.Fprintf(os.Stderr, "erro ao ler %s: %v\n", *src, err)
		return 1
	}

	if len(files) == 0 {
		fmt.Println("nenhum arquivo de código-fonte reconhecido foi encontrado.")
		return 0
	}

	report := renderReport(*title, files)

	if err := os.WriteFile(*out, []byte(report), 0o644); err != nil {
		fmt.Fprintf(os.Stderr, "erro ao escrever %s: %v\n", *out, err)
		return 1
	}

	fmt.Printf("Relatório gerado: %s (%d arquivo(s))\n", *out, len(files))
	return 0
}

// collectSourceFiles percorre root recursivamente, ignora diretórios
// irrelevantes e arquivos grandes/binários, e devolve os arquivos em
// ordem alfabética estável.
func collectSourceFiles(root string) ([]sourceFile, error) {
	var files []sourceFile

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

		lang := detectLanguage(path)

		files = append(files, sourceFile{
			RelPath: filepath.ToSlash(rel),
			Lang:    lang,
			Content: string(data),
		})
		return nil
	})

	sort.Slice(files, func(i, j int) bool { return files[i].RelPath < files[j].RelPath })

	return files, err
}

// looksBinary usa uma heurística simples: presença de byte nulo nos
// primeiros 512 bytes indica conteúdo não-textual.
func looksBinary(data []byte) bool {
	limit := len(data)
	if limit > 512 {
		limit = 512
	}
	return bytes.IndexByte(data[:limit], 0) != -1
}

func renderReport(title string, files []sourceFile) string {
	var b strings.Builder

	b.WriteString("<!DOCTYPE html>\n<html lang=\"pt-BR\">\n<head>\n<meta charset=\"UTF-8\">\n")
	b.WriteString("<title>" + html.EscapeString(title) + "</title>\n")
	b.WriteString("<style>\n" + reportCSS + "\n</style>\n</head>\n<body>\n")

	b.WriteString("<header><h1>" + html.EscapeString(title) + "</h1>")
	b.WriteString(fmt.Sprintf("<p class=\"meta\">%d arquivo(s) — gerado por openops-cli docgen</p></header>\n", len(files)))

	b.WriteString("<nav><h2>Arquivos</h2><ul>\n")
	for i, f := range files {
		b.WriteString(fmt.Sprintf(
			"<li><a href=\"#file-%d\">%s</a> <span class=\"lang-badge\">%s</span></li>\n",
			i, html.EscapeString(f.RelPath), html.EscapeString(languageLabel(f.Lang)),
		))
	}
	b.WriteString("</ul></nav>\n<main>\n")

	for i, f := range files {
		b.WriteString(fmt.Sprintf("<section id=\"file-%d\">\n", i))
		b.WriteString(fmt.Sprintf(
			"<h2>%s <span class=\"lang-badge\">%s</span></h2>\n",
			html.EscapeString(f.RelPath), html.EscapeString(languageLabel(f.Lang)),
		))
		b.WriteString("<pre><code>")
		b.WriteString(highlight(f.Content, f.Lang))
		b.WriteString("</code></pre>\n</section>\n")
	}

	b.WriteString("</main>\n</body>\n</html>\n")
	return b.String()
}

const reportCSS = `
:root { color-scheme: dark; }
body { background:#0d1117; color:#c9d1d9; font-family: -apple-system, Segoe UI, sans-serif; margin:0; }
header { padding: 2rem; border-bottom: 1px solid #21262d; }
header h1 { margin:0; color:#58a6ff; }
.meta { color:#8b949e; }
nav { padding: 1rem 2rem; background:#161b22; }
nav ul { list-style:none; padding:0; display:flex; flex-wrap:wrap; gap:.5rem 1rem; }
nav a { color:#58a6ff; text-decoration:none; }
nav a:hover { text-decoration:underline; }
.lang-badge { font-size:.75rem; background:#21262d; color:#8b949e; padding:.15rem .5rem; border-radius:999px; margin-left:.4rem; }
main { padding: 1rem 2rem 3rem; }
section { margin-bottom: 2.5rem; }
section h2 { border-bottom:1px solid #21262d; padding-bottom:.5rem; font-family: monospace; }
pre { background:#161b22; border:1px solid #21262d; border-radius:8px; padding:1rem; overflow-x:auto; }
code { font-family: "Fira Code", Consolas, monospace; font-size:.9rem; line-height:1.5; white-space:pre; }
.hl-comment { color:#8b949e; font-style:italic; }
.hl-string { color:#a5d6ff; }
.hl-number { color:#f2cc60; }
.hl-keyword { color:#ff7b72; font-weight:600; }
`
