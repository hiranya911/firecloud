package firego

import "fmt"

// SayHello says hello.
func SayHello(name string) string {
	return fmt.Sprintf("Hello, %s", name)
}
