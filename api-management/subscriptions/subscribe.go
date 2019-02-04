package subscriptions

import (
	"context"
	"encoding/json"
	"io/ioutil"
	"log"
	"net/http"

	"cloud.google.com/go/firestore"
	firebase "firebase.google.com/go"
	"firebase.google.com/go/auth"
)

var authClient *auth.Client
var dbClient *firestore.Client

const collection string = "apikeys"

func init() {
	app, err := firebase.NewApp(context.Background(), nil)
	if err != nil {
		log.Fatalf("NewApp() = %v", err)
	}

	authClient, err = app.Auth(context.Background())
	if err != nil {
		log.Fatalf("Auth() = %v", err)
	}

	dbClient, err = app.Firestore(context.Background())
	if err != nil {
		log.Fatalf("Firestore() = %v", err)
	}
}

// Subscribe subscribes the caller to an API. The caller is given an API key in return.
func Subscribe(w http.ResponseWriter, r *http.Request) {
	if err := handleSubscribe(w, r); err != nil {
		sendError(w, err)
	}
}

func handleSubscribe(w http.ResponseWriter, r *http.Request) error {
	if r.Method != http.MethodPost {
		return newHTTPErrorFromString(http.StatusMethodNotAllowed, "unsupported http method")
	}
	defer r.Body.Close()

	uid, err := checkAuth(r)
	if err != nil {
		return newHTTPError(http.StatusUnauthorized, err)
	}

	sr, err := parseRequest(r)
	if err != nil {
		return newHTTPError(http.StatusInternalServerError, err)
	}
	sr.UID = uid

	apiKey, err := generateAPIKey(r.Context(), sr)
	if err != nil {
		return newHTTPError(http.StatusInternalServerError, err)
	}
	if err := sendAPIKey(w, apiKey); err != nil {
		return newHTTPError(http.StatusInternalServerError, err)
	}
	return nil
}

func checkAuth(r *http.Request) (string, error) {
	idToken := r.Header.Get("authorization")
	ft, err := authClient.VerifyIDToken(r.Context(), idToken)
	if err != nil {
		return "", err
	}
	return ft.UID, nil
}

type subscribeRequest struct {
	API     string `json:"api" firestore:"api"`
	Version string `json:"version" firestore:"version"`
	UID     string `json:"-" firestore:"uid"`
}

func parseRequest(r *http.Request) (*subscribeRequest, error) {
	b, err := ioutil.ReadAll(r.Body)
	if err != nil {
		return nil, err
	}

	var sr subscribeRequest
	if err := json.Unmarshal(b, &sr); err != nil {
		return nil, newHTTPError(http.StatusInternalServerError, err)
	}
	return &sr, nil
}

func generateAPIKey(ctx context.Context, sr *subscribeRequest) (string, error) {
	doc := dbClient.Collection(collection).NewDoc()
	_, err := doc.Set(ctx, sr)
	if err != nil {
		return "", err
	}
	return doc.ID, nil
}

func sendAPIKey(w http.ResponseWriter, apiKey string) error {
	body := map[string]string{
		"apiKey": apiKey,
	}
	b, err := json.Marshal(body)
	if err != nil {
		return err
	}
	w.Header().Set("content-type", "application/json")
	w.Write(b)
	return nil
}

type httpError struct {
	status  int
	message string
}

func newHTTPError(status int, err error) *httpError {
	return &httpError{
		status:  status,
		message: err.Error(),
	}
}

func newHTTPErrorFromString(status int, msg string) *httpError {
	return &httpError{
		status:  status,
		message: msg,
	}
}

func (he *httpError) Error() string {
	return he.message
}

func sendError(w http.ResponseWriter, err error) {
	he, ok := err.(*httpError)
	if !ok {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(he.status)
	body := map[string]string{
		"error": he.message,
	}
	b, err := json.Marshal(body)
	if err != nil {
		b = []byte(he.message)
		w.Header().Set("content-type", "text/plain")
	} else {
		w.Header().Set("content-type", "application/json")
	}
	w.Write(b)
}
