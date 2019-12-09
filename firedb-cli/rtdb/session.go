package rtdb

import (
	"context"
	"fmt"
	"strings"

	firebase "firebase.google.com/go"
	"firebase.google.com/go/db"
)

// Session represents the current status of the CLI session.
type Session interface {
	node(path string) (node, error)
	set(curr node)
}

type rtdbSession struct {
	client *db.Client
	curr   *rtdbNode
}

// NewRTDBSession creates a session backed by Firebase RTDB.
func NewRTDBSession(ctx context.Context, url string) (Session, error) {
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

	return &rtdbSession{
		client: client,
		curr:   &rtdbNode{client.NewRef("/")},
	}, nil
}

func (r *rtdbSession) node(path string) (node, error) {
	target := r.curr
	if path == "" {
		return target, nil
	}

	segments := parsePath(path)
	if len(segments) == 0 || strings.HasPrefix(path, "/") {
		target = &rtdbNode{r.client.NewRef("/")}
	}

	for _, seg := range segments {
		if seg == "." {
			continue
		} else if seg == ".." {
			target = &rtdbNode{target.Parent()}
		} else {
			target = &rtdbNode{target.Child(seg)}
		}

		if target == nil {
			return nil, fmt.Errorf("Invalid path: %q", path)
		}
	}

	return target, nil
}

func (r *rtdbSession) set(curr node) {
	r.curr = curr.(*rtdbNode)
}

func parsePath(path string) []string {
	var segs []string
	for _, s := range strings.Split(path, "/") {
		if s != "" {
			segs = append(segs, s)
		}
	}
	return segs
}
