package rtdb

import (
	"bytes"
	"testing"

	"firebase.google.com/go/db"
)

func TestPwd(t *testing.T) {
	session := newTestSession()
	var buf bytes.Buffer
	shell := NewShell(session, &buf)
	shell.Process("pwd")
	if buf.String() != "/\n" {
		t.Errorf("pwd = %q; want = %q", buf.String(), "/\n")
	}
}

func TestCD(t *testing.T) {
	session := newTestSession()
	var buf bytes.Buffer
	shell := NewShell(session, &buf)
	shell.Process("cd", "foo")

	if session.client.Path() != "/foo" {
		t.Errorf("cd = %q; want = %q", session.client.Path(), "/foo")
	}
	shell.Process()
}

func newTestSession() *Session {
	ref := &TestRef{
		path: "/",
	}
	return &Session{
		client: ref,
	}
}

func newRef() client {
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

func (r *TestRef) Child(path string) client {
	return &TestRef{
		path: r.path + path,
	}
}

func (r *TestRef) Parent() client {
	return nil
}

func (r *TestRef) FromPath(path string) client {
	return nil
}
