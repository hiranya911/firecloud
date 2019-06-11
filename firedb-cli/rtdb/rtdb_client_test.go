package rtdb

import (
	"bytes"
	"context"
	"log"
	"os"
	"testing"

	firebase "firebase.google.com/go"
	"github.com/abiosoft/ishell"
	"github.com/abiosoft/readline"
	"google.golang.org/api/option"
)

var s *rtdbShell
var err error

func TestMain(m *testing.M) {
	s, err = newRTDBShell(context.Background(), "https://test.firebaseio.com")
	if err != nil {
		log.Fatal(err)
	}
	os.Exit(m.Run())
}

func TestPwd(t *testing.T) {
	var buf bytes.Buffer
	conf := &readline.Config{
		Stdout: &buf,
	}

	shell := newShellWithConfig(conf)
	s.pwd(&ishell.Context{
		Actions: shell,
	})
	if buf.String() != "/\n" {
		t.Errorf("pwd = %q; want = %q", buf.String(), "/\n")
	}
}

func newRef() (*firebase.App, error) {
	conf := &firebase.Config{
		DatabaseURL: "https://example-db.firebaseio.com",
	}
	return firebase.NewApp(context.Background(), conf, option.WithTokenSource(nil))
}
