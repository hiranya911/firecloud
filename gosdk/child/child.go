package child

type Client struct {
}

func (c *Client) Info() string {
	return "child.Client"
}

func NewClient() *Client {
	return &Client{}
}
