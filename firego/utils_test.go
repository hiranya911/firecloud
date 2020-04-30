package firego

import "testing"

func TestSayHello(t *testing.T) {
     result := SayHello("user")
     if result != "Hello, user" {
     	t.Fatalf("Invalid result = %q", result)
     }
}
