package cmd

import "fmt"

// Version é preenchida via -ldflags no build de release; em builds locais
// mantém o valor "dev".
var Version = "dev"

func init() {
	Register(&Command{
		Name:        "version",
		Description: "Mostra a versão do openops-cli",
		Run: func(args []string) int {
			fmt.Printf("openops-cli %s\n", Version)
			return 0
		},
	})
}
