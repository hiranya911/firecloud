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
	app.Version = rtdb.Version
	app.Action = func(c *cli.Context) error {
		url := c.Args().Get(0)
		session, err := rtdb.NewRTDBSession(context.Background(), url)
		if err != nil {
			return cli.NewExitError(err, 1)
		}

		shell := rtdb.NewShell(session, nil)
		shell.Run()
		return nil
	}
	app.Run(os.Args)
}
