package child

import "testing"

func TestNewClient(t *testing.T) {
	client := NewClient()
	if client.Info() != "child.Client@v6" {
		t.Fatal()
	}
}
