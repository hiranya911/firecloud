package child

import "testing"

func TestSayHello(t *testing.T) {
	result := SayHello("user")
	if result != "Child: Hello, user" {
		t.Fatalf("Invalid result = %q", result)
	}
}
