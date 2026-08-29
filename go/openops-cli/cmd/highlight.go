package cmd

import (
	"html"
	"path/filepath"
	"regexp"
	"strings"
)

// languageSpec descreve as regras de realce de uma linguagem: um único
// regexp combinado, com grupos nomeados (comment/string/number/keyword),
// compilado uma vez e reutilizado.
type languageSpec struct {
	Label string
	regex *regexp.Regexp
}

var extensionToLanguage = map[string]string{
	".py":   "python",
	".go":   "go",
	".rs":   "rust",
	".js":   "javascript",
	".jsx":  "javascript",
	".ts":   "typescript",
	".tsx":  "typescript",
	".json": "json",
}

var languages = map[string]*languageSpec{
	"python":     buildLanguage("Python", pyKeywords, `#[^\n]*`),
	"go":         buildLanguage("Go", goKeywords, `//[^\n]*`),
	"rust":       buildLanguage("Rust", rustKeywords, `//[^\n]*`),
	"javascript": buildLanguage("JavaScript", jsKeywords, `//[^\n]*`),
	"typescript": buildLanguage("TypeScript", jsKeywords, `//[^\n]*`),
	"json":       buildLanguage("JSON", jsonKeywords, ``),
}

var pyKeywords = []string{
	"def", "class", "import", "from", "return", "if", "elif", "else", "for",
	"while", "try", "except", "finally", "with", "as", "pass", "break",
	"continue", "lambda", "yield", "global", "nonlocal", "assert", "raise",
	"in", "is", "not", "and", "or", "None", "True", "False", "self",
	"async", "await", "del", "match", "case",
}

var goKeywords = []string{
	"func", "package", "import", "return", "if", "else", "for", "range",
	"switch", "case", "default", "break", "continue", "struct", "interface",
	"map", "chan", "go", "defer", "select", "var", "const", "type", "nil",
	"true", "false", "iota", "fallthrough", "goto",
}

var rustKeywords = []string{
	"fn", "let", "mut", "struct", "enum", "impl", "trait", "pub", "use",
	"mod", "match", "if", "else", "for", "while", "loop", "return", "break",
	"continue", "self", "Self", "true", "false", "None", "Some", "Ok", "Err",
	"async", "await", "unsafe", "where", "dyn", "static", "const", "move",
}

var jsKeywords = []string{
	"function", "const", "let", "var", "return", "if", "else", "for",
	"while", "switch", "case", "break", "continue", "class", "extends",
	"new", "this", "typeof", "instanceof", "true", "false", "null",
	"undefined", "async", "await", "import", "export", "default", "try",
	"catch", "finally", "interface", "type", "enum", "implements",
}

var jsonKeywords = []string{"true", "false", "null"}

// buildLanguage compila o regexp combinado de uma linguagem. lineComment
// vazio omite o grupo de comentário (ex.: JSON não tem comentários).
func buildLanguage(label string, keywords []string, lineComment string) *languageSpec {
	stringPattern := `"(?:[^"\\\n]|\\.)*"|'(?:[^'\\\n]|\\.)*'`
	numberPattern := `\b\d+(?:\.\d+)?\b`
	keywordPattern := `\b(?:` + strings.Join(keywords, "|") + `)\b`

	parts := []string{}
	if lineComment != "" {
		parts = append(parts, `(?P<comment>`+lineComment+`)`)
	}
	parts = append(parts,
		`(?P<string>`+stringPattern+`)`,
		`(?P<number>`+numberPattern+`)`,
		`(?P<keyword>`+keywordPattern+`)`,
	)

	combined := strings.Join(parts, "|")
	return &languageSpec{Label: label, regex: regexp.MustCompile(combined)}
}

// detectLanguage retorna a chave de linguagem (ver `languages`) a partir
// da extensão do arquivo, ou "" se não houver realce disponível para ela.
func detectLanguage(filename string) string {
	ext := strings.ToLower(filepath.Ext(filename))
	return extensionToLanguage[ext]
}

// highlight converte código-fonte em HTML com <span> de realce. Texto
// fora de qualquer token reconhecido é apenas escapado (nunca perdido).
// Para linguagens sem regras (fallback "plaintext"), apenas escapa.
func highlight(source string, langKey string) string {
	spec, ok := languages[langKey]
	if !ok {
		return html.EscapeString(source)
	}

	var out strings.Builder
	lastEnd := 0

	matches := spec.regex.FindAllStringSubmatchIndex(source, -1)
	names := spec.regex.SubexpNames()

	for _, m := range matches {
		start, end := m[0], m[1]

		// texto entre o fim do match anterior e o início deste
		out.WriteString(html.EscapeString(source[lastEnd:start]))

		class := "hl-token"
		for i := 1; i < len(names); i++ {
			if names[i] == "" {
				continue
			}
			groupStart, groupEnd := m[2*i], m[2*i+1]
			if groupStart == -1 {
				continue
			}
			if groupStart == start && groupEnd == end {
				class = "hl-" + names[i]
				break
			}
		}

		out.WriteString(`<span class="` + class + `">`)
		out.WriteString(html.EscapeString(source[start:end]))
		out.WriteString(`</span>`)

		lastEnd = end
	}

	out.WriteString(html.EscapeString(source[lastEnd:]))
	return out.String()
}

// languageLabel devolve um nome de exibição amigável para a linguagem
// detectada, ou "Texto simples" quando não há regras de realce.
func languageLabel(langKey string) string {
	if spec, ok := languages[langKey]; ok {
		return spec.Label
	}
	return "Texto simples"
}
