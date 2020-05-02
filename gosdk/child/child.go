package child

type Client struct {
}

func (c *Client) Info() string {
	return "child.Client@v6"
}

func NewClient() *Client {
	return &Client{}
}
