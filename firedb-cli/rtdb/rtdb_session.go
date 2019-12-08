package rtdb

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"strconv"
	"strings"

	"github.com/abiosoft/ishell"
)

// Session represents the current status of the CLI session.
type Session struct {
	curr node
}

// NewSession creates a new session to interact with the specified RTDB URL.
func NewSession(ctx context.Context, url string) (*Session, error) {
	node, err := newRTDBNode(context.Background(), url)
	if err != nil {
		return nil, err
	}

	return &Session{
		curr: node,
	}, nil
}

func (s *Session) pwd(c *ishell.Context) {
	c.Println(s.curr.Path())
}

func (s *Session) get(c *ishell.Context) {
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

func (s *Session) getData(child string) (string, error) {
	target, err := s.node(child)
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

func (s *Session) set(c *ishell.Context) {
	if len(c.Args) != 1 && len(c.Args) != 2 {
		c.Println("usage: set [path] <data>")
		return
	}

	target := s.curr
	data := c.Args[0]
	if len(c.Args) == 2 {
		var err error
		target, err = s.node(c.Args[0])
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

func (s *Session) delete(c *ishell.Context) {
	if len(c.Args) > 1 {
		c.Println("usage: delete [path]")
		return
	}

	target := s.curr
	if len(c.Args) == 1 {
		var err error
		target, err = s.node(c.Args[0])
		if err != nil {
			c.Println(err)
			return
		}
	}

	if err := target.Delete(context.Background()); err != nil {
		c.Println(err)
	}
}

func (s *Session) cd(c *ishell.Context) {
	if len(c.Args) > 1 {
		c.Println("usage: cd [path]")
		return
	}

	if len(c.Args) == 0 {
		if s.curr.Path() != "/" {
			s.curr = s.root()
			c.SetPrompt(s.curr.Path() + " >>> ")
		}
		return
	}

	target, err := s.node(c.Args[0])
	if err != nil {
		c.Println(err)
		return
	}

	s.curr = target
	c.SetPrompt(s.curr.Path() + " >>> ")
}

func (s *Session) node(path string) (node, error) {
	target := s.curr
	if path == "" {
		return target, nil
	}

	segments := parsePath(path)
	log.Println(path, segments)
	if len(segments) == 0 || strings.HasPrefix(path, "/") {
		target = s.root()
	}

	for _, seg := range segments {
		if seg == "." {
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

func (s *Session) root() node {
	curr := s.curr
	for {
		temp := curr.Parent()
		if temp == nil {
			return curr
		}

		curr = temp
	}
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
