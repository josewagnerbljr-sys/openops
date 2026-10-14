package cmd

import "testing"

func TestDetectLanguage(t *testing.T) {
	cases := map[string]string{
		"main.py":       "python",
		"lib.rs":        "rust",
		"cmd/root.go":   "go",
		"index.js":      "javascript",
		"app.tsx":       "typescript",
		"data.json":     "json",
		"README.md":     "",
		"noextension":   "",
	}

	for filename, want := range cases {
		got := detectLanguage(filename)
		if got != want {
			t.Errorf("detectLanguage(%q) = %q, esperado %q", filename, got, want)
		}
	}
}

func TestHighlight_PythonKeywordAndString(t *testing.T) {
	source := `def hello():\n    return "oi"`

	out := highlight(source, "python")

	if !contains(out, `<span class="hl-keyword">def</span>`) {
		t.Errorf("esperava span de keyword 'def', obteve: %s", out)
	}
	if !contains(out, `<span class="hl-keyword">return</span>`) {
		t.Errorf("esperava span de keyword 'return', obteve: %s", out)
	}
	if !contains(out, `<span class="hl-string">&#34;oi&#34;</span>`) {
		t.Errorf("esperava span de string, obteve: %s", out)
	}
}

func TestHighlight_GoComment(t *testing.T) {
	source := "// isto é um comentário\nfunc main() {}"

	out := highlight(source, "go")

	if !contains(out, `hl-comment`) {
		t.Errorf("esperava span de comentário, obteve: %s", out)
	}
	if !contains(out, `<span class="hl-keyword">func</span>`) {
		t.Errorf("esperava span de keyword 'func', obteve: %s", out)
	}
}

func TestHighlight_NumberToken(t *testing.T) {
	out := highlight("let x = 42;", "javascript")

	if !contains(out, `<span class="hl-number">42</span>`) {
		t.Errorf("esperava span de número, obteve: %s", out)
	}
}

func TestHighlight_UnknownLanguageOnlyEscapes(t *testing.T) {
	out := highlight("<script>alert(1)</script>", "")

	if contains(out, "<script>") {
		t.Errorf("HTML não deveria ter sido injetado sem escape: %s", out)
	}
	if !contains(out, "&lt;script&gt;") {
		t.Errorf("esperava escape de HTML, obteve: %s", out)
	}
}

func TestHighlight_NeverLosesCharacters(t *testing.T) {
	source := `x = "a" + 'b' + 3 # comentario final`

	out := highlight(source, "python")

	// Todo caractere original deve estar presente em algum ponto do HTML
	// (escapado ou não) — nenhum span pode "engolir" texto.
	for _, want := range []string{"x", "=", "+", "3"} {
		if !contains(out, want) {
			t.Errorf("caractere/token %q ausente na saída: %s", want, out)
		}
	}
}

func contains(haystack, needle string) bool {
	return len(haystack) >= len(needle) && indexOf(haystack, needle) != -1
}

func indexOf(haystack, needle string) int {
	for i := 0; i+len(needle) <= len(haystack); i++ {
		if haystack[i:i+len(needle)] == needle {
			return i
		}
	}
	return -1
}
