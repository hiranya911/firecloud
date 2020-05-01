package child

import (
	"firego/v3"
	"fmt"
)

// SayHello says hello.
func SayHello(name string) string {
	parent := firego.SayHello(name)
	return fmt.Sprintf("Child: %s", parent)
}
