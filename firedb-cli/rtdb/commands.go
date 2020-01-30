package rtdb

import (
	"context"
	"encoding/json"
	"strconv"

	"github.com/abiosoft/ishell"
)

type get struct {
	sess Session
}

func (g *get) build() *ishell.Cmd {
	return &ishell.Cmd{
		Name: "get",
		Help: "Gets the data in the current or specified path",
		Func: g.run,
	}
}

func (g *get) run(c *ishell.Context) {
	showData := func(data, path string, heading bool) {
		if heading {
			c.Printf("%s:\n", path)
		}

		c.Println(data)
	}

	paths := c.Args
	if len(paths) == 0 {
		paths = append(paths, "")
	}

	var nodes []getter
	for _, path := range paths {
		node, err := g.sess.node(path)
		if err != nil {
			c.Println(err)
			return
		}

		nodes = append(nodes, node)
	}

	for idx, child := range nodes {
		if idx > 0 {
			c.Println()
		}

		data, err := data(child)
		if err != nil {
			c.Println(err)
			return
		}

		showData(data, paths[idx], len(paths) > 1)
	}
}

func data(target getter) (string, error) {
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

type pwd struct {
	sess Session
}

func (p *pwd) build() *ishell.Cmd {
	return &ishell.Cmd{
		Name: "pwd",
		Help: "Prints the path of the current node",
		Func: p.run,
	}
}

func (p *pwd) run(c *ishell.Context) {
	node, _ := p.sess.node("")
	c.Println(node.Path())
}

type cd struct {
	sess Session
}

func (cd *cd) build() *ishell.Cmd {
	return &ishell.Cmd{
		Name: "cd",
		Help: "changes the current location",
		Func: cd.run,
	}
}

func (cd *cd) run(c *ishell.Context) {
	if len(c.Args) > 1 {
		c.Println("usage: cd [path]")
		return
	}

	path := "/"
	if len(c.Args) > 0 {
		path = c.Args[0]
	}

	new, err := cd.sess.node(path)
	if err != nil {
		c.Println(err)
		return
	}

	cd.sess.set(new)
	c.SetPrompt(new.Path() + " >>> ")
}

type ls struct {
	sess Session
}

func (ls *ls) build() *ishell.Cmd {
	return &ishell.Cmd{
		Name: "ls",
		Help: "Lists the child data in the current or specified path",
		Func: ls.run,
	}
}

func (ls *ls) run(c *ishell.Context) {
	showData := func(children []string, path string, heading bool) {
		if heading {
			c.Printf("%s:\n", path)
		}

		for _, child := range children {
			c.Println(child)
		}
	}

	paths := c.Args
	if len(paths) == 0 {
		paths = append(paths, "")
	}

	var nodes []shallowGetter
	for _, path := range paths {
		node, err := ls.sess.node(path)
		if err != nil {
			c.Println(err)
			return
		}

		nodes = append(nodes, node)
	}

	for idx, child := range nodes {
		if idx > 0 {
			c.Println()
		}

		data, err := listChildren(child)
		if err != nil {
			c.Println(err)
			return
		}

		showData(data, paths[idx], len(paths) > 1)
	}
}

func listChildren(target shallowGetter) ([]string, error) {
	var i interface{}
	if err := target.GetShallow(context.Background(), &i); err != nil {
		return nil, err
	}

	var children []string
	dir, ok := i.(map[string]interface{})
	if ok {
		for k := range dir {
			children = append(children, k)
		}
	}

	return children, nil
}

type set struct {
	sess Session
}

func (s *set) build() *ishell.Cmd {
	return &ishell.Cmd{
		Name: "set",
		Help: "Sets the data to the current or specified path",
		Func: s.run,
	}
}

func (s *set) run(c *ishell.Context) {
	if len(c.Args) != 1 && len(c.Args) != 2 {
		c.Println("usage: set [path] <data>")
		return
	}

	path := ""
	data := c.Args[0]
	if len(c.Args) == 2 {
		path = c.Args[0]
		data = c.Args[1]
	}

	target, err := s.sess.node(path)
	if err != nil {
		c.Println(err)
		return
	}

	if err := target.Set(context.Background(), marshalData(data)); err != nil {
		c.Println(err)
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

type delete struct {
	sess Session
}

func (d *delete) build() *ishell.Cmd {
	return &ishell.Cmd{
		Name: "delete",
		Help: "Deletes the current or specified path and all its child nodes",
		Func: d.run,
	}
}

func (d *delete) run(c *ishell.Context) {
	if len(c.Args) > 1 {
		c.Println("usage: delete [path]")
		return
	}

	path := ""
	if len(c.Args) == 1 {
		path = c.Args[0]
	}

	target, err := d.sess.node(path)
	if err != nil {
		c.Println(err)
		return
	}

	if err := target.Delete(context.Background()); err != nil {
		c.Println(err)
	}
}

type update struct {
	sess Session
}

func (u *update) build() *ishell.Cmd {
	return &ishell.Cmd{
		Name: "update",
		Help: "Updates the specified child keys",
		Func: u.run,
	}
}

func (u *update) run(c *ishell.Context) {
	if len(c.Args) != 1 && len(c.Args) != 2 {
		c.Println("usage: update [path] <data>")
		return
	}

	path := ""
	data := c.Args[0]
	if len(c.Args) == 2 {
		path = c.Args[0]
		data = c.Args[1]
	}

	target, err := u.sess.node(path)
	if err != nil {
		c.Println(err)
		return
	}

	parsed := marshalData(data)
	m, ok := parsed.(map[string]interface{})
	if !ok {
		c.Println("data must be a map")
		return
	}

	if err := target.Update(context.Background(), m); err != nil {
		c.Println(err)
	}
}

type push struct {
	sess Session
}

func (p *push) build() *ishell.Cmd {
	return &ishell.Cmd{
		Name: "push",
		Help: "Pushes a new child to the current path",
		Func: p.run,
	}
}

func (p *push) run(c *ishell.Context) {
	if len(c.Args) > 1 {
		c.Println("usage: push [data]")
		return
	}

	target, err := p.sess.node("")
	if err != nil {
		c.Println(err)
		return
	}

	var data interface{}
	if len(c.Args) == 1 {
		data = marshalData(c.Args[0])
	}

	child, err := target.Push(context.Background(), data)
	if err != nil {
		c.Println(err)
	} else {
		c.Println(child)
	}
}

type vers struct {
	sess Session
}

func (v *vers) build() *ishell.Cmd {
	return &ishell.Cmd{
		Name: "version",
		Help: "Prints the current version of the CLI",
		Func: v.run,
	}
}

func (v *vers) run(c *ishell.Context) {
	c.Println(Version)
}
