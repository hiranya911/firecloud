package rtdb

import (
	"io"

	"github.com/abiosoft/ishell"
	"github.com/abiosoft/readline"
)

// Version of the CLI.
const Version = "0.0.1"

// NewShell creates a new RTDB shell.
func NewShell(sess Session, stdout io.Writer) *ishell.Shell {
	shell := ishell.NewWithConfig(&readline.Config{
		Prompt: "/ >>> ",
		Stdout: stdout,
	})

	shell.AddCmd((&cd{sess}).build())
	shell.AddCmd((&delete{sess}).build())
	shell.AddCmd((&get{sess}).build())
	shell.AddCmd((&ls{sess}).build())
	shell.AddCmd((&push{sess}).build())
	shell.AddCmd((&pwd{sess}).build())
	shell.AddCmd((&set{sess}).build())
	shell.AddCmd((&update{sess}).build())
	shell.AddCmd((&vers{sess}).build())

	return shell
}
