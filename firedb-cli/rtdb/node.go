package rtdb

import (
	"context"

	"firebase.google.com/go/db"
)

type getter interface {
	Get(ctx context.Context, v interface{}) error
}

type shallowGetter interface {
	GetShallow(ctx context.Context, v interface{}) error
}

type pathFinder interface {
	Path() string
}

type setter interface {
	Set(ctx context.Context, v interface{}) error
}

type deleter interface {
	Delete(ctx context.Context) error
}

type pusher interface {
	Push(ctx context.Context, v interface{}) (string, error)
}

type node interface {
	deleter
	getter
	shallowGetter
	pathFinder
	pusher
	setter
}

type rtdbNode struct {
	*db.Ref
}

func (node *rtdbNode) Path() string {
	return node.Ref.Path
}

func (node *rtdbNode) Push(ctx context.Context, v interface{}) (string, error) {
	ref, err := node.Ref.Push(ctx, v)
	if err != nil {
		return "", err
	}

	return ref.Path, nil
}
