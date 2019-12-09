package rtdb

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"testing"
)

func TestPwd(t *testing.T) {
	sess := &testSession{
		nodes: map[string]*testNode{
			"": &testNode{
				pathFinder: &testGetter{
					path: "/",
				},
			},
		},
	}
	var buf bytes.Buffer
	shell := NewShell(sess, &buf)

	shell.Process("pwd")

	if buf.String() != "/\n" {
		t.Errorf("pwd = %q; want = %q", buf.String(), "/\n")
	}
}

func TestCD(t *testing.T) {
	sess := &testSession{
		nodes: map[string]*testNode{
			"foo": &testNode{
				pathFinder: &testGetter{
					path: "/foo",
				},
			},
			"/foo/bar": &testNode{
				pathFinder: &testGetter{
					path: "/foo/bar",
				},
			},
			"./baz": &testNode{
				pathFinder: &testGetter{
					path: "/foo/bar/baz",
				},
			},
			"/": &testNode{
				pathFinder: &testGetter{
					path: "/",
				},
			},
		},
	}
	var buf bytes.Buffer
	shell := NewShell(sess, &buf)

	shell.Process("cd", "foo")

	if sess.curr.Path() != "/foo" {
		t.Errorf("cd = %q; want = %q", sess.curr.Path(), "/foo")
	}

	shell.Process("cd", "/foo/bar")
	if sess.curr.Path() != "/foo/bar" {
		t.Errorf("cd = %q; want = %q", sess.curr.Path(), "/foo/bar")
	}

	shell.Process("cd", "./baz")
	if sess.curr.Path() != "/foo/bar/baz" {
		t.Errorf("cd = %q; want = %q", sess.curr.Path(), "/foo/bar/baz")
	}

	shell.Process("cd")
	if sess.curr.Path() != "/" {
		t.Errorf("cd = %q; want = %q", sess.curr.Path(), "/")
	}
}

func TestCDParent(t *testing.T) {
	sess := &testSession{
		nodes: map[string]*testNode{
			"foo/bar": &testNode{
				pathFinder: &testGetter{
					path: "/foo/bar",
				},
			},
			"..": &testNode{
				pathFinder: &testGetter{
					path: "/foo",
				},
			},
			"/": &testNode{
				pathFinder: &testGetter{
					path: "/",
				},
			},
		},
	}
	var buf bytes.Buffer
	shell := NewShell(sess, &buf)

	shell.Process("cd", "foo/bar")
	if sess.curr.Path() != "/foo/bar" {
		t.Errorf("cd = %q; want = %q", sess.curr.Path(), "/foo/bar")
	}

	shell.Process("cd", "..")
	if sess.curr.Path() != "/foo" {
		t.Errorf("cd = %q; want = %q", sess.curr.Path(), "/foo")
	}

	shell.Process("cd", "../..")
	if sess.curr.Path() != "/foo" {
		t.Errorf("cd = %q; want = %q", sess.curr.Path(), "/foo")
	}

	want := "Invalid path: \"../..\"\n"
	if buf.String() != want {
		t.Errorf("get = %q; want = %q", buf.String(), want)
	}
}

func TestCDExtraArgs(t *testing.T) {
	sess := &testSession{}
	var buf bytes.Buffer
	shell := NewShell(sess, &buf)

	shell.Process("cd", "foo", "bar")

	want := "usage: cd [path]\n"
	if buf.String() != want {
		t.Errorf("set = %q; want = %q", buf.String(), want)
	}
}

type testGetter struct {
	path string
	data []byte
	err  error
}

func (g *testGetter) Path() string {
	return g.path
}

func (g *testGetter) Get(ctx context.Context, v interface{}) error {
	if g.err != nil {
		return g.err
	}

	return json.Unmarshal(g.data, v)
}

func TestGet(t *testing.T) {
	sess := &testSession{
		nodes: map[string]*testNode{
			"": &testNode{
				getter: &testGetter{
					data: []byte(`{"foo": "bar"}`),
				},
			},
		},
	}
	var buf bytes.Buffer
	shell := NewShell(sess, &buf)

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
	sess := &testSession{
		nodes: map[string]*testNode{
			"": &testNode{
				getter: &testGetter{
					err: errors.New("something failed"),
				},
			},
		},
	}
	var buf bytes.Buffer
	shell := NewShell(sess, &buf)

	shell.Process("get")

	want := "something failed\n"
	if buf.String() != want {
		t.Errorf("get = %q; want = %q", buf.String(), want)
	}
}

func TestGetInvalidPath(t *testing.T) {
	sess := &testSession{}
	var buf bytes.Buffer
	shell := NewShell(sess, &buf)

	shell.Process("get", "..")

	want := "Invalid path: \"..\"\n"
	if buf.String() != want {
		t.Errorf("get = %q; want = %q", buf.String(), want)
	}
}

func TestGetSingle(t *testing.T) {
	sess := &testSession{
		nodes: map[string]*testNode{
			"path1": &testNode{
				getter: &testGetter{
					data: []byte(`{"foo": "bar"}`),
				},
			},
		},
	}
	var buf bytes.Buffer
	shell := NewShell(sess, &buf)

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
	sess := &testSession{
		nodes: map[string]*testNode{
			"path1": &testNode{
				getter: &testGetter{
					data: []byte(`{"foo1": "bar"}`),
				},
			},
			"path2": &testNode{
				getter: &testGetter{
					data: []byte(`{"foo2": "bar"}`),
				},
			},
		},
	}
	var buf bytes.Buffer
	shell := NewShell(sess, &buf)

	shell.Process("get", "path1", "path2")

	want := `path1:
{
    "foo1": "bar"
}

path2:
{
    "foo2": "bar"
}
`
	if buf.String() != want {
		t.Errorf("get = %q; want = %q", buf.String(), want)
	}
}

type testSetter struct {
	data []byte
	err  error
	done bool
}

func (s *testSetter) Set(ctx context.Context, v interface{}) error {
	if s.err != nil {
		return s.err
	}

	b, err := json.Marshal(v)
	if err != nil {
		return err
	}

	s.data = b
	s.done = true
	return nil
}

func (s *testSetter) Delete(ctx context.Context) error {
	if s.err != nil {
		return s.err
	}

	s.done = true
	return nil
}

func TestSet(t *testing.T) {
	currSetter := &testSetter{}
	rootSetter := &testSetter{}
	sess := &testSession{
		nodes: map[string]*testNode{
			"": &testNode{
				setter: currSetter,
			},
			"/": &testNode{
				setter: rootSetter,
			},
		},
	}
	var buf bytes.Buffer
	shell := NewShell(sess, &buf)

	shell.Process("set", "101")
	want := "101"
	if string(currSetter.data) != want {
		t.Errorf("set = %q; want = %q", string(currSetter.data), want)
	}

	shell.Process("set", "/", "102.12")
	want = "102.12"
	if string(rootSetter.data) != want {
		t.Errorf("set = %q; want = %q", string(rootSetter.data), want)
	}

	shell.Process("set", "/", "true")
	want = "true"
	if string(rootSetter.data) != want {
		t.Errorf("set = %q; want = %q", string(rootSetter.data), want)
	}

	shell.Process("set", "/", "false")
	want = "false"
	if string(rootSetter.data) != want {
		t.Errorf("set = %q; want = %q", string(rootSetter.data), want)
	}

	shell.Process("set", "/", `{"key": "value"}`)
	want = `{"key":"value"}`
	if string(rootSetter.data) != want {
		t.Errorf("set = %q; want = %q", string(rootSetter.data), want)
	}
}

func TestSetError(t *testing.T) {
	sess := &testSession{
		nodes: map[string]*testNode{
			"": &testNode{
				setter: &testSetter{
					err: errors.New("something failed"),
				},
			},
		},
	}
	var buf bytes.Buffer
	shell := NewShell(sess, &buf)

	shell.Process("set", "foo")

	want := "something failed\n"
	if buf.String() != want {
		t.Errorf("set = %q; want = %q", buf.String(), want)
	}
}

func TestSetExtraArgs(t *testing.T) {
	sess := &testSession{}
	var buf bytes.Buffer
	shell := NewShell(sess, &buf)

	shell.Process("set", "foo", "bar", "baz")

	want := "usage: set [path] <data>\n"
	if buf.String() != want {
		t.Errorf("set = %q; want = %q", buf.String(), want)
	}
}

func TestSetInvalidPath(t *testing.T) {
	sess := &testSession{}
	var buf bytes.Buffer
	shell := NewShell(sess, &buf)

	shell.Process("set", "..", "true")

	want := "Invalid path: \"..\"\n"
	if buf.String() != want {
		t.Errorf("set = %q; want = %q", buf.String(), want)
	}
}

func TestDelete(t *testing.T) {
	del := &testSetter{}
	sess := &testSession{
		nodes: map[string]*testNode{
			"": &testNode{
				deleter: del,
			},
		},
	}
	var buf bytes.Buffer
	shell := NewShell(sess, &buf)

	shell.Process("delete")

	if !del.done {
		t.Errorf("delete = %v; want = %v", del.done, true)
	}
}

func TestDeletePath(t *testing.T) {
	del := &testSetter{}
	sess := &testSession{
		nodes: map[string]*testNode{
			"path": &testNode{
				deleter: del,
			},
		},
	}
	var buf bytes.Buffer
	shell := NewShell(sess, &buf)

	shell.Process("delete", "path")

	if !del.done {
		t.Errorf("delete = %v; want = %v", del.done, true)
	}
}

func TestDeleteExtraArgs(t *testing.T) {
	session := &testSession{}
	var buf bytes.Buffer
	shell := NewShell(session, &buf)

	shell.Process("delete", "foo", "bar")

	want := "usage: delete [path]\n"
	if buf.String() != want {
		t.Errorf("set = %q; want = %q", buf.String(), want)
	}
}

func TestDeleteInvalidPath(t *testing.T) {
	session := &testSession{}
	var buf bytes.Buffer
	shell := NewShell(session, &buf)

	shell.Process("delete", "..")

	want := "Invalid path: \"..\"\n"
	if buf.String() != want {
		t.Errorf("delete = %q; want = %q", buf.String(), want)
	}
}

func TestDeleteError(t *testing.T) {
	sess := &testSession{
		nodes: map[string]*testNode{
			"": &testNode{
				deleter: &testSetter{
					err: errors.New("something failed"),
				},
			},
		},
	}
	var buf bytes.Buffer
	shell := NewShell(sess, &buf)

	shell.Process("delete")

	want := "something failed\n"
	if buf.String() != want {
		t.Errorf("delete = %q; want = %q", buf.String(), want)
	}
}

func TestVersion(t *testing.T) {
	session := &testSession{}
	var buf bytes.Buffer
	shell := NewShell(session, &buf)

	shell.Process("version")

	want := fmt.Sprintf("%s\n", Version)
	if buf.String() != want {
		t.Errorf("version = %q; want = %q", buf.String(), want)
	}
}

type testNode struct {
	getter
	shallowGetter
	pathFinder
	setter
	deleter
	pusher
}

type testSession struct {
	nodes map[string]*testNode
	curr  node
}

func (s *testSession) node(path string) (node, error) {
	if n, ok := s.nodes[path]; ok {
		return n, nil
	}

	return nil, fmt.Errorf("Invalid path: %q", path)
}

func (s *testSession) set(curr node) {
	s.curr = curr
}
