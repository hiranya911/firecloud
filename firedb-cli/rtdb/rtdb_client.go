package rtdb

import (
	"context"

	firebase "firebase.google.com/go"
	"firebase.google.com/go/db"
)

type node interface {
	Get(ctx context.Context, v interface{}) error
	Set(ctx context.Context, v interface{}) error
	Delete(ctx context.Context) error
	Path() string
	Parent() node
	Child(path string) node
}

type rtdbNode struct {
	*db.Ref
}

func (node *rtdbNode) Path() string {
	return node.Ref.Path
}

func (node *rtdbNode) Parent() node {
	return &rtdbNode {
		Ref: node.Ref.Parent(),
	}
}

func (node *rtdbNode) Child(path string) node {
	return &rtdbNode {
		Ref: node.Ref.Child(path),
	}
}

func newRTDBNode(ctx context.Context, url string) (*rtdbNode, error) {
	var conf *firebase.Config
	if url != "" {
		conf = &firebase.Config{
			DatabaseURL: url,
		}
	}

	app, err := firebase.NewApp(ctx, conf)
	if err != nil {
		return nil, err
	}

	client, err := app.Database(ctx)
	if err != nil {
		return nil, err
	}

	return &rtdbNode {
		Ref: client.NewRef("/"),
	}, nil
}
