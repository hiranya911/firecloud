package gosdk

import "github.com/hiranya911/firecloud/gosdk/child"

type App struct {
}

func (app *App) Info() string {
	return "App"
}

func (app *App) Child() *child.Client {
	return child.NewClient()
}

func NewApp() *App {
	return &App{}
}
