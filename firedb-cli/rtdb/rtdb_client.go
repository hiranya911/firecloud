package rtdb

import (
	"context"

	firebase "firebase.google.com/go"
	"firebase.google.com/go/db"
)

type client interface {
	Path() string
	Get(ctx context.Context, v interface{}) error
	Set(ctx context.Context, v interface{}) error
	Delete(ctx context.Context) error
	Parent() client
	Child(path string) client
	FromPath(path string) client
}

type firebaseClient struct {
	client *db.Client
	*db.Ref
}

func newFirebaseClient(ctx context.Context, url string) (*firebaseClient, error) {
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

	return &firebaseClient{
		client: client,
		Ref:    client.NewRef("/"),
	}, nil
}

func (r *firebaseClient) Path() string {
	return r.Ref.Path
}

func (r *firebaseClient) Child(path string) client {
	return &firebaseClient{
		client: r.client,
		Ref:    r.Ref.Child(path),
	}
}

func (r *firebaseClient) Parent() client {
	return &firebaseClient{
		client: r.client,
		Ref:    r.Ref.Parent(),
	}
}

func (r *firebaseClient) FromPath(path string) client {
	return &firebaseClient{
		client: r.client,
		Ref:    r.client.NewRef(path),
	}
}
