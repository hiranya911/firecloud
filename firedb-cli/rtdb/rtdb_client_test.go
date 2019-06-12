package rtdb

import (
	"bytes"
	"testing"

	"firebase.google.com/go/db"
	"github.com/abiosoft/readline"
)

func TestPwd(t *testing.T) {
	var buf bytes.Buffer
	conf := &readline.Config{
		Stdout: &buf,
	}

	shell := newShellWithConfig(conf)
	s := &rtdbShell{
		ref: newRef(),
	}
	registerCommands(shell, s)
	shell.Process("pwd")
	if buf.String() != "/\n" {
		t.Errorf("pwd = %q; want = %q", buf.String(), "/\n")
	}
}

func TestCD(t *testing.T) {
	var buf bytes.Buffer
	conf := &readline.Config{
		Stdout: &buf,
	}

	shell := newShellWithConfig(conf)
	s := &rtdbShell{
		ref: newRef(),
	}
	registerCommands(shell, s)
	shell.Process("cd", "foo")

	if s.ref.Path() != "/foo" {
		t.Errorf("cd = %q; want = %q", s.ref.Path(), "/foo")
	}
	shell.Process()
}

func newRef() Ref {
	return &TestRef{
		path: "/",
	}
}

type TestRef struct {
	path string
	*db.Ref
}

func (r *TestRef) Path() string {
	return r.path
}

func (r *TestRef) Child(path string) Ref {
	return &TestRef{
		path: r.path + path,
	}
}

func (r *TestRef) Parent() Ref {
	return nil
}

func (r *TestRef) FromPath(path string) Ref {
	return nil
}
