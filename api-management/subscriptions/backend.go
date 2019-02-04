package subscriptions

import (
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"strings"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
)

// HelloWorld is a sample backend API implementation.
func HelloWorld(w http.ResponseWriter, r *http.Request) {
	ifAPIKeyIsValid(helloWorldHandler).ServeHTTP(w, r)
}

func helloWorldHandler(w http.ResponseWriter, r *http.Request) {
	name := r.FormValue("name")
	body := map[string]string{
		"response": fmt.Sprintf("Hello, %s", name),
	}
	b, _ := json.Marshal(body)
	w.Header().Set("content-type", "application/json")
	w.Write(b)
}

func ifAPIKeyIsValid(handler http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if err := checkAPIKey(r); err != nil {
			sendError(w, newHTTPError(http.StatusUnauthorized, err))
			return
		}
		handler(w, r)
	}
}

func checkAPIKey(r *http.Request) error {
	apiKey, err := getBearerToken(r)
	if err != nil {
		return err
	}

	doc := dbClient.Collection(collection).Doc(apiKey)
	_, err = doc.Get(r.Context())
	if grpc.Code(err) == codes.NotFound {
		return errors.New("invalid API key")
	}
	return err
}

func getBearerToken(r *http.Request) (string, error) {
	authHeader := r.Header.Get("authorization")
	if authHeader == "" {
		return "", errors.New("authorization header not available")
	}

	parts := strings.Split(authHeader, "Bearer ")
	if len(parts) != 2 {
		return "", errors.New("failed to parse authorization header")
	}

	apiKey := parts[1]
	if apiKey == "" {
		return "", errors.New("no API key provided")
	}
	return apiKey, nil
}
