package rtdb

import (
	"io"

	"github.com/abiosoft/ishell"
	"github.com/abiosoft/readline"
)

const version = "0.0.1"

// NewShell creates a new RTDB shell.
func NewShell(s *Session, stdout io.Writer) *ishell.Shell {
	shell := ishell.NewWithConfig(&readline.Config{
		Prompt: "/ >>> ",
		Stdout: stdout,
	})
	registerCommands(shell, s)
	return shell
}

func registerCommands(shell *ishell.Shell, s *Session) {
	shell.AddCmd(&ishell.Cmd{
		Name: "version",
		Help: "Print version of the CLI",
		Func: func(c *ishell.Context) {
			c.Println(version)
		},
	})
	shell.AddCmd(&ishell.Cmd{
		Name: "get",
		Help: "Gets the data in the current or specified path",
		Func: s.get,
	})
	shell.AddCmd(&ishell.Cmd{
		Name: "ls",
		Help: "Lists the child data in the current or specified path",
		Func: s.ls,
	})
	shell.AddCmd(&ishell.Cmd{
		Name: "push",
		Help: "Pushes a new child to the current path",
		Func: s.push,
	})
	shell.AddCmd(&ishell.Cmd{
		Name: "pwd",
		Help: "Prints the path to the current location",
		Func: s.pwd,
	})
	shell.AddCmd(&ishell.Cmd{
		Name: "set",
		Help: "Sets the data to the current or specified path",
		Func: s.set,
	})
	shell.AddCmd(&ishell.Cmd{
		Name: "delete",
		Help: "Deletes the current or specified path and all its child nodes",
		Func: s.delete,
	})
	shell.AddCmd(&ishell.Cmd{
		Name: "cd",
		Help: "changes the current location",
		Func: s.cd,
	})
}
