package rtdb

import (
	"context"
	"encoding/json"
	"fmt"
	"strconv"
	"strings"

	firebase "firebase.google.com/go"
	"firebase.google.com/go/db"
	"github.com/abiosoft/ishell"
	"github.com/abiosoft/readline"
)

type Ref interface {
	Path() string
	Get(ctx context.Context, v interface{}) error
	Set(ctx context.Context, v interface{}) error
	Delete(ctx context.Context) error
	Parent() Ref
	Child(path string) Ref
	FromPath(path string) Ref
}

type FirebaseRef struct {
	client *db.Client
	*db.Ref
}

func (r *FirebaseRef) Path() string {
	return r.Ref.Path
}

func (r *FirebaseRef) Child(path string) Ref {
	return &FirebaseRef{
		client: r.client,
		Ref:    r.Ref.Child(path),
	}
}

func (r *FirebaseRef) Parent() Ref {
	return &FirebaseRef{
		client: r.client,
		Ref:    r.Ref.Parent(),
	}
}

func (r *FirebaseRef) FromPath(path string) Ref {
	return &FirebaseRef{
		client: r.client,
		Ref:    r.client.NewRef(path),
	}
}

type rtdbShell struct {
	ref Ref
}

// NewShell creates a new RTDB shell.
func NewShell(ctx context.Context, url string) (*ishell.Shell, error) {
	s, err := newRTDBShell(ctx, url)
	if err != nil {
		return nil, err
	}

	shell := newShellWithConfig(nil)
	registerCommands(shell, s)

	shell.Println("Firebase interactive shell")
	return shell, nil
}

func registerCommands(shell *ishell.Shell, s *rtdbShell) {
	shell.AddCmd(&ishell.Cmd{
		Name: "version",
		Help: "Print version of the CLI",
		Func: func(c *ishell.Context) {
			c.Println("0.0.1")
		},
	})
	shell.AddCmd(&ishell.Cmd{
		Name: "get",
		Help: "Gets the data in the current or specified path",
		Func: s.get,
	})
	shell.AddCmd(&ishell.Cmd{
		Name: "pwd",
		Help: "Prints the path to the current location",
		Func: s.pwd,
	})
	shell.AddCmd(&ishell.Cmd{
		Name: "set",
		Help: "sets the data to the current or specified path",
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

func newRTDBShell(ctx context.Context, url string) (*rtdbShell, error) {
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

	return &rtdbShell{
		ref: &FirebaseRef{client: client, Ref: client.NewRef("/")},
	}, nil
}

func newShellWithConfig(conf *readline.Config) *ishell.Shell {
	var shell *ishell.Shell
	if conf != nil {
		shell = ishell.NewWithConfig(conf)
	} else {
		shell = ishell.New()
	}

	shell.SetPrompt("/ >>> ")
	return shell
}

func (s *rtdbShell) pwd(c *ishell.Context) {
	c.Println(s.ref.Path())
}

func (s *rtdbShell) get(c *ishell.Context) {
	showData := func(child string, heading bool) error {
		data, err := s.getData(child)
		if err != nil {
			return err
		}

		if heading {
			c.Printf("%s:\n", child)
		}

		c.Println(data)
		return nil
	}

	if len(c.Args) > 1 {
		for idx, child := range c.Args {
			if idx > 0 {
				c.Println()
			}

			if err := showData(child, true); err != nil {
				c.Println(err)
				return
			}
		}
	} else {
		child := ""
		if len(c.Args) == 1 {
			child = c.Args[0]
		}
		if err := showData(child, false); err != nil {
			c.Println(err)
			return
		}
	}
}

func (s *rtdbShell) getData(child string) (string, error) {
	target, err := s.getRef(child)
	if err != nil {
		return "", err
	}

	var i interface{}
	if err := target.Get(context.Background(), &i); err != nil {
		return "", err
	}

	b, err := json.MarshalIndent(i, "", "    ")
	if err != nil {
		return "", err
	}

	return string(b), nil
}

func (s *rtdbShell) set(c *ishell.Context) {
	if len(c.Args) != 1 && len(c.Args) != 2 {
		c.Println("usage: set [path] <data>")
		return
	}

	target := s.ref
	data := c.Args[0]
	if len(c.Args) == 2 {
		var err error
		target, err = s.getRef(c.Args[0])
		if err != nil {
			c.Println(err)
			return
		}

		data = c.Args[1]
	}

	if err := target.Set(context.Background(), marshalData(data)); err != nil {
		c.Println(err)
	}
}

func (s *rtdbShell) delete(c *ishell.Context) {
	if len(c.Args) > 1 {
		c.Println("usage: delete [path]")
		return
	}

	target := s.ref
	if len(c.Args) == 1 {
		var err error
		target, err = s.getRef(c.Args[0])
		if err != nil {
			c.Println(err)
			return
		}
	}

	if err := target.Delete(context.Background()); err != nil {
		c.Println(err)
	}
}

func (s *rtdbShell) cd(c *ishell.Context) {
	if len(c.Args) > 1 {
		c.Println("usage: cd [path]")
		return
	}

	if len(c.Args) == 0 {
		if s.ref.Path() != "/" {
			s.ref = s.ref.FromPath("/")
			c.SetPrompt(s.ref.Path() + " >>> ")
		}
		return
	}

	target, err := s.getRef(c.Args[0])
	if err != nil {
		c.Println(err)
		return
	}

	s.ref = target
	c.SetPrompt(target.Path() + " >>> ")
}

// getRef returns a Ref that corresponds to the given path. If the path
// is relative, it is calculated relative to the current node (s.ref). If
// the path is empty, the current node is returned.
func (s *rtdbShell) getRef(path string) (Ref, error) {
	target := s.ref
	if path == "" {
		return target, nil
	}

	segments := parsePath(path)
	if len(segments) == 0 {
		return s.ref.FromPath("/"), nil
	}

	for idx, seg := range segments {
		if seg == "" {
			if idx == 0 {
				target = s.ref.FromPath("/")
			}
		} else if seg == "." {
			continue
		} else if seg == ".." {
			target = target.Parent()
		} else {
			target = target.Child(seg)
		}

		if target == nil {
			return nil, fmt.Errorf("Invalid path: %q", path)
		}
	}

	return target, nil
}

func marshalData(data string) interface{} {
	var dict map[string]interface{}
	if err := json.Unmarshal([]byte(data), &dict); err == nil {
		return dict
	}

	if i, err := strconv.ParseInt(data, 10, 64); err == nil {
		return i
	}

	if f, err := strconv.ParseFloat(data, 64); err == nil {
		return f
	}

	if data == "true" {
		return true
	} else if data == "false" {
		return false
	}
	return data
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
