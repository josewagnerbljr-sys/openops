// Command openops-cli é o ponto de entrada da ferramenta de linha de
// comando do OpenOps.
package main

import (
	"os"

	"github.com/josewagnerbljr-sys/openops/go/openops-cli/cmd"
)

func main() {
	os.Exit(cmd.Execute())
}
