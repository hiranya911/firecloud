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

func Subscribe(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		sendError(http.StatusMethodNotAllowed, "invalid method", w)
		return
	}

	idToken := r.Header.Get("authorization")
	uid, err := checkAuth(r.Context(), idToken)
	if err != nil {
		sendError(http.StatusUnauthorized, err.Error(), w)
		return
	}

	defer r.Body.Close()
	b, err := ioutil.ReadAll(r.Body)
	if err != nil {
		sendError(http.StatusInternalServerError, err.Error(), w)
		return
	}

	var sr subscribeRequest
	if err := json.Unmarshal(b, &sr); err != nil {
		sendError(http.StatusInternalServerError, err.Error(), w)
		return
	}
	sr.UID = uid

	apiKey, err := generateAPIKey(r.Context(), &sr)
	if err := json.Unmarshal(b, &sr); err != nil {
		sendError(http.StatusInternalServerError, err.Error(), w)
		return
	}

	sendAPIKey(apiKey, w)
}

type subscribeRequest struct {
	API     string `json:"api" firestore:"api"`
	Version string `json:"version" firestore:"version"`
	UID     string `json:"uid" firestore:"uid"`
}

func checkAuth(ctx context.Context, idToken string) (string, error) {
	ft, err := authClient.VerifyIDToken(ctx, idToken)
	if err != nil {
		return "", err
	}
	return ft.UID, nil
}

func sendError(status int, msg string, w http.ResponseWriter) {
	w.WriteHeader(status)
	body := map[string]string{
		"error": msg,
	}
	b, err := json.Marshal(body)
	if err != nil {
		b = []byte(msg)
		w.Header().Set("content-type", "text/plain")
	} else {
		w.Header().Set("content-type", "application/json")
	}
	w.Write(b)
}

func generateAPIKey(ctx context.Context, sr *subscribeRequest) (string, error) {
	doc := dbClient.Collection(collection).NewDoc()
	_, err := doc.Set(ctx, sr)
	if err != nil {
		return "", err
	}
	return doc.ID, nil
}

func sendAPIKey(apiKey string, w http.ResponseWriter) {
	body := map[string]string{
		"apiKey": apiKey,
	}
	b, _ := json.Marshal(body)
	w.Header().Set("content-type", "application/json")
	w.Write(b)
}
