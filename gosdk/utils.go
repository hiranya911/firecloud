package gosdk

import "github.com/hiranya911/firecloud/gosdk/v6/child"

type App struct {
}

func (app *App) Info() string {
	return "App@v6"
}

func (app *App) Child() *child.Client {
	return child.NewClient()
}

func NewApp() *App {
	return &App{}
}
