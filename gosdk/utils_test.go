package gosdk

import "testing"

func TestNewApp(t *testing.T) {
	app := NewApp()
	if app.Info() != "App" {
		t.Fatalf("Info() = %q; want = %q", app.Info(), "App")
	}
}
