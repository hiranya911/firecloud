package subscriptions

import (
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"strings"
)

func HelloWorld(w http.ResponseWriter, r *http.Request) {
	if err := checkAPIKey(r); err != nil {
		sendError(http.StatusUnauthorized, err.Error(), w)
		return
	}
	name := r.FormValue("name")
	body := map[string]string{
		"response": fmt.Sprintf("Hello, %s", name),
	}
	b, _ := json.Marshal(body)
	w.Header().Set("content-type", "application/json")
	w.Write(b)
}

func checkAPIKey(r *http.Request) error {
	authHeader := r.Header.Get("authorization")
	if authHeader == "" {
		return errors.New("authorization header not available")
	}
	parts := strings.Split(authHeader, "Bearer ")
	if len(parts) != 2 {
		return errors.New("failed to parse authorization header")
	}
	apiKey := parts[1]
	if apiKey == "" {
		return errors.New("no API key provided")
	}
	doc := dbClient.Collection(collection).Doc(apiKey)
	_, err := doc.Get(r.Context())
	return err
}
