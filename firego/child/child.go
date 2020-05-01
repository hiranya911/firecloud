package child

import (
	"fmt"

	"github.com/hiranya911/firecloud/firego/v4"
)

// SayHello says hello.
func SayHello(name string) string {
	parent := firego.SayHello(name)
	return fmt.Sprintf("Child: %s", parent)
}
