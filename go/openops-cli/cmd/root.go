// Package cmd implementa os subcomandos do openops-cli.
//
// O CLI é escrito em Go e compilado como binário único justamente para
// cumprir o item 13 do documento mestre do OpenOps ("Preparação para
// forks" -> "Instalação reproduzível do zero"): qualquer pessoa baixa um
// único executável, sem precisar instalar runtime nenhum, e roda os
// comandos de diagnóstico e operação do OpenOps.
package cmd

import (
	"flag"
	"fmt"
	"os"
)

// Command descreve um subcomando executável do CLI.
type Command struct {
	Name        string
	Description string
	Run         func(args []string) int
}

var registry = map[string]*Command{}

// Register adiciona um comando ao registro global do CLI.
func Register(c *Command) {
	registry[c.Name] = c
}

// Execute despacha para o subcomando indicado em os.Args[1] e retorna o
// exit code apropriado.
func Execute() int {
	if len(os.Args) < 2 {
		printUsage()
		return 1
	}

	name := os.Args[1]
	if name == "-h" || name == "--help" {
		printUsage()
		return 0
	}

	cmd, ok := registry[name]
	if !ok {
		fmt.Fprintf(os.Stderr, "comando desconhecido: %q\n\n", name)
		printUsage()
		return 1
	}

	return cmd.Run(os.Args[2:])
}

func printUsage() {
	fmt.Println("openops-cli — ferramenta de linha de comando do OpenOps")
	fmt.Println()
	fmt.Println("Uso: openops-cli <comando> [flags]")
	fmt.Println()
	fmt.Println("Comandos disponíveis:")
	for name, c := range registry {
		fmt.Printf("  %-10s %s\n", name, c.Description)
	}
}

// newFlagSet é um helper para subcomandos que precisam de flags próprias.
func newFlagSet(name string) *flag.FlagSet {
	return flag.NewFlagSet(name, flag.ExitOnError)
}
