package rtdb

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
	"testing"
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
	if session.curr.Path() != "/foo" {
		t.Errorf("cd = %q; want = %q", session.curr.Path(), "/foo")
	}

	shell.Process("cd", "/foo/bar")
	if session.curr.Path() != "/foo/bar" {
		t.Errorf("cd = %q; want = %q", session.curr.Path(), "/foo/bar")
	}

	shell.Process("cd", "./baz")
	if session.curr.Path() != "/foo/bar/baz" {
		t.Errorf("cd = %q; want = %q", session.curr.Path(), "/foo/bar/baz")
	}

	shell.Process("cd")
	if session.curr.Path() != "/" {
		t.Errorf("cd = %q; want = %q", session.curr.Path(), "/")
	}
}

func TestCDParent(t *testing.T) {
	session := newTestSession()
	var buf bytes.Buffer
	shell := NewShell(session, &buf)

	shell.Process("cd", "foo/bar")
	if session.curr.Path() != "/foo/bar" {
		t.Errorf("cd = %q; want = %q", session.curr.Path(), "/foo/bar")
	}

	shell.Process("cd", "..")
	if session.curr.Path() != "/foo" {
		t.Errorf("cd = %q; want = %q", session.curr.Path(), "/foo")
	}

	shell.Process("cd", "..")
	if session.curr.Path() != "/" {
		t.Errorf("cd = %q; want = %q", session.curr.Path(), "/")
	}

	shell.Process("cd", "..")
	if session.curr.Path() != "/" {
		t.Errorf("cd = %q; want = %q", session.curr.Path(), "/")
	}

	want := "Invalid path: \"..\"\n"
	if buf.String() != want {
		t.Errorf("get = %q; want = %q", buf.String(), want)
	}
}

func TestCDExtraArgs(t *testing.T) {
	session := newTestSession()
	var buf bytes.Buffer
	shell := NewShell(session, &buf)
	shell.Process("cd", "foo", "bar")
	want := "usage: cd [path]\n"
	if buf.String() != want {
		t.Errorf("set = %q; want = %q", buf.String(), want)
	}
}

func TestGet(t *testing.T) {
	node := &TestNode{
		path: "/",
		data: []byte(`{"foo": "bar"}`),
	}
	session := newTestSessionWithNode(node)
	var buf bytes.Buffer
	shell := NewShell(session, &buf)
	shell.Process("get")
	want := `{
    "foo": "bar"
}
`
	if buf.String() != want {
		t.Errorf("get = %q; want = %q", buf.String(), want)
	}
}

func TestGetError(t *testing.T) {
	node := &TestNode{
		path: "/",
		err:  errors.New("something failed"),
	}
	session := newTestSessionWithNode(node)
	var buf bytes.Buffer
	shell := NewShell(session, &buf)
	shell.Process("get")
	want := "something failed\n"
	if buf.String() != want {
		t.Errorf("get = %q; want = %q", buf.String(), want)
	}
}

func TestGetInvalidPath(t *testing.T) {
	session := newTestSession()
	var buf bytes.Buffer
	shell := NewShell(session, &buf)
	shell.Process("get", "..")
	want := "Invalid path: \"..\"\n"
	if buf.String() != want {
		t.Errorf("get = %q; want = %q", buf.String(), want)
	}
}

func TestGetInvalidPaths(t *testing.T) {
	session := newTestSession()
	var buf bytes.Buffer
	shell := NewShell(session, &buf)
	shell.Process("get", "..", "..")
	want := "Invalid path: \"..\"\n"
	if buf.String() != want {
		t.Errorf("get = %q; want = %q", buf.String(), want)
	}
}

func TestGetSingle(t *testing.T) {
	node := &TestNode{
		path: "/",
		data: []byte(`{"foo": "bar"}`),
	}
	session := newTestSessionWithNode(node)
	var buf bytes.Buffer
	shell := NewShell(session, &buf)
	shell.Process("get", "path1")
	want := `{
    "foo": "bar"
}
`
	if buf.String() != want {
		t.Errorf("get = %q; want = %q", buf.String(), want)
	}
}

func TestGetMultiple(t *testing.T) {
	node := &TestNode{
		path: "/",
		data: []byte(`{"foo": "bar"}`),
	}
	session := newTestSessionWithNode(node)
	var buf bytes.Buffer
	shell := NewShell(session, &buf)
	shell.Process("get", "path1", "path2")
	want := `path1:
{
    "foo": "bar"
}

path2:
{
    "foo": "bar"
}
`
	if buf.String() != want {
		t.Errorf("get = %q; want = %q", buf.String(), want)
	}
}

func TestSet(t *testing.T) {
	node := &TestNode{
		path: "/",
	}
	session := newTestSessionWithNode(node)
	var buf bytes.Buffer
	shell := NewShell(session, &buf)

	shell.Process("set", "101")
	want := "101"
	if string(node.data) != want {
		t.Errorf("set = %q; want = %q", string(node.data), want)
	}

	shell.Process("set", "/", "102.12")
	want = "102.12"
	if string(node.data) != want {
		t.Errorf("set = %q; want = %q", string(node.data), want)
	}

	shell.Process("set", "/", "true")
	want = "true"
	if string(node.data) != want {
		t.Errorf("set = %q; want = %q", string(node.data), want)
	}

	shell.Process("set", "/", "false")
	want = "false"
	if string(node.data) != want {
		t.Errorf("set = %q; want = %q", string(node.data), want)
	}

	shell.Process("set", "/", `{"key": "value"}`)
	want = `{"key":"value"}`
	if string(node.data) != want {
		t.Errorf("set = %q; want = %q", string(node.data), want)
	}
}

func TestSetError(t *testing.T) {
	node := &TestNode{
		path: "/",
		err:  errors.New("something failed"),
	}
	session := newTestSessionWithNode(node)
	var buf bytes.Buffer
	shell := NewShell(session, &buf)
	shell.Process("set", "foo")
	want := "something failed\n"
	if buf.String() != want {
		t.Errorf("set = %q; want = %q", buf.String(), want)
	}
}

func TestSetExtraArgs(t *testing.T) {
	session := newTestSession()
	var buf bytes.Buffer
	shell := NewShell(session, &buf)
	shell.Process("set", "foo", "bar", "baz")
	want := "usage: set [path] <data>\n"
	if buf.String() != want {
		t.Errorf("set = %q; want = %q", buf.String(), want)
	}
}

func TestSetInvalidPath(t *testing.T) {
	session := newTestSession()
	var buf bytes.Buffer
	shell := NewShell(session, &buf)
	shell.Process("set", "..", "true")
	want := "Invalid path: \"..\"\n"
	if buf.String() != want {
		t.Errorf("set = %q; want = %q", buf.String(), want)
	}
}

func TestDelete(t *testing.T) {
	node := &TestNode{
		path: "/foo",
	}
	session := newTestSessionWithNode(node)
	var buf bytes.Buffer
	shell := NewShell(session, &buf)

	shell.Process("delete")
}

func TestDeletePath(t *testing.T) {
	session := newTestSession()
	var buf bytes.Buffer
	shell := NewShell(session, &buf)

	shell.Process("delete", "path")
}

func TestDeleteExtraArgs(t *testing.T) {
	session := newTestSession()
	var buf bytes.Buffer
	shell := NewShell(session, &buf)
	shell.Process("delete", "foo", "bar")
	want := "usage: delete [path]\n"
	if buf.String() != want {
		t.Errorf("set = %q; want = %q", buf.String(), want)
	}
}

func TestDeleteInvalidPath(t *testing.T) {
	session := newTestSession()
	var buf bytes.Buffer
	shell := NewShell(session, &buf)
	shell.Process("delete", "..")
	want := "Invalid path: \"..\"\n"
	if buf.String() != want {
		t.Errorf("delete = %q; want = %q", buf.String(), want)
	}
}

func TestDeleteError(t *testing.T) {
	node := &TestNode{
		path: "/",
		err:  errors.New("something failed"),
	}
	session := newTestSessionWithNode(node)
	var buf bytes.Buffer
	shell := NewShell(session, &buf)
	shell.Process("delete")
	want := "something failed\n"
	if buf.String() != want {
		t.Errorf("delete = %q; want = %q", buf.String(), want)
	}
}

func TestVersion(t *testing.T) {
	session := newTestSession()
	var buf bytes.Buffer
	shell := NewShell(session, &buf)

	shell.Process("version")
	want := fmt.Sprintf("%s\n", version)
	if buf.String() != want {
		t.Errorf("set = %q; want = %q", buf.String(), want)
	}
}

func newTestSession() *Session {
	n := &TestNode{
		path: "/",
	}
	return newTestSessionWithNode(n)
}

func newTestSessionWithNode(n *TestNode) *Session {
	return &Session{
		curr: n,
	}
}

type TestNode struct {
	path string
	data []byte
	err  error
}

func (n *TestNode) Child(path string) node {
	child := n.path
	if child == "/" {
		child += path
	} else {
		child += "/" + path
	}

	temp := *n
	temp.path = child
	return &temp
}

func (n *TestNode) Parent() node {
	segs := parsePath(n.path)
	if len(segs) == 0 {
		return nil
	}

	temp := *n
	temp.path = "/" + strings.Join(segs[0:len(segs)-1], "/")
	return &temp
}

func (n *TestNode) Path() string {
	return n.path
}

func (n *TestNode) Get(ctx context.Context, v interface{}) error {
	if n.err != nil {
		return n.err
	}

	return json.Unmarshal(n.data, v)
}

func (n *TestNode) GetShallow(ctx context.Context, v interface{}) error {
	return n.Get(ctx, v)
}

func (n *TestNode) Set(ctx context.Context, v interface{}) error {
	if n.err != nil {
		return n.err
	}

	b, err := json.Marshal(v)
	if err != nil {
		return err
	}

	n.data = b
	return nil
}

func (n *TestNode) Push(ctx context.Context, v interface{}) (string, error) {
	err := n.Set(ctx, v)
	if err != nil {
		return "", err
	}

	return "child", nil
}

func (n *TestNode) Delete(ctx context.Context) error {
	if n.err != nil {
		return n.err
	}

	return nil
}
