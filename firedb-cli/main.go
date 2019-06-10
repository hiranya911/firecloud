package main

import (
	"context"
	"os"

	"gopkg.in/urfave/cli.v1"

	"github.com/hiranya911/firecloud/dbcli/rtdb"
)

func main() {
	app := cli.NewApp()
	app.Name = "dbcli"
	app.Usage = "Start DB CLI shell"
	app.Action = func(c *cli.Context) error {
		url := c.Args().Get(0)
		shell, err := rtdb.NewShell(context.Background(), url)
		if err != nil {
			return cli.NewExitError(err, 1)
		}

		shell.Run()
		return nil
	}
	app.Run(os.Args)
}
