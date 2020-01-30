package main

import (
	"context"
	"fmt"
	"os"

	"gopkg.in/urfave/cli.v1"

	"github.com/hiranya911/firecloud/dbcli/rtdb"
)

func main() {
	app := cli.NewApp()
	app.Name = "dbcli"
	app.Usage = "Start DB CLI shell"
	app.UsageText = "dbcli [global options] [arguments...]"
	app.Version = rtdb.Version
	app.Flags = []cli.Flag{
		cli.BoolFlag{
			Name:  "script",
			Usage: "run the command in non-interactive mode",
		},
		cli.StringFlag{
			Name:   "rtdb",
			Usage:  "realtime database url string",
			EnvVar: "FIREBASE_RTDB_URL",
			Value:  "",
		},
	}
	app.Action = func(c *cli.Context) error {
		url := c.String("rtdb")
		if url == "" {
			return cli.NewExitError("rtdb url not specified", 1)
		}

		session, err := rtdb.NewRTDBSession(context.Background(), url)
		if err != nil {
			return cli.NewExitError(err, 1)
		}

		shell := rtdb.NewShell(session, nil)
		script := c.Bool("script")
		if script {
			return shell.Process(c.Args()...)
		}

		fmt.Println("Firebase Real-time Database CLI")
		fmt.Println(url)
		fmt.Println()
		shell.Run()
		return nil
	}

	app.Run(os.Args)
}
