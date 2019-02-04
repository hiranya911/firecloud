package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"

	firebase "firebase.google.com/go"
)

const (
	subscribeURL         = "https://us-central1-solarflares-f4bee.cloudfunctions.net/Subscribe"
	verifyCustomTokenURL = "https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyCustomToken?key=%s"
)

func main() {
	ctx := context.Background()
	app, err := firebase.NewApp(ctx, nil)
	if err != nil {
		log.Fatalf("NewApp() = %v", err)
	}

	authClient, err := app.Auth(ctx)
	if err != nil {
		log.Fatalf("Auth() = %v", err)
	}

	customToken, err := authClient.CustomToken(ctx, "testuser")
	if err != nil {
		log.Fatalf("CustomToken() = %v", err)
	}

	idToken, err := signInWithCustomToken(customToken)
	if err != nil {
		log.Fatalf("signInWithCustomToken() = %v", err)
	}
	log.Printf("Received ID token = %s", idToken)

	apiKey, err := subscribe(ctx, idToken)
	if err != nil {
		log.Fatalf("signInWithCustomToken() = %v", err)
	}
	log.Printf("Received API key = %s", apiKey)
}

func subscribe(ctx context.Context, idToken string) (string, error) {
	req, err := json.Marshal(map[string]interface{}{
		"api":     "HelloWorld",
		"version": "1.0.0",
	})
	if err != nil {
		return "", err
	}
	hr, err := http.NewRequest(http.MethodPost, subscribeURL, bytes.NewBuffer(req))
	if err != nil {
		return "", err
	}
	hr.Header.Set("authorization", idToken)
	hr = hr.WithContext(ctx)
	resp, err := http.DefaultClient.Do(hr)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("unexpected http status code: %d", resp.StatusCode)
	}

	b, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}
	var result struct {
		APIKey string `json:"apiKey"`
	}
	if err := json.Unmarshal(b, &result); err != nil {
		return "", err
	}
	return result.APIKey, nil
}

func signInWithCustomToken(token string) (string, error) {
	req, err := json.Marshal(map[string]interface{}{
		"token":             token,
		"returnSecureToken": true,
	})
	if err != nil {
		return "", err
	}

	apiKey := os.Getenv("FIREBASE_APIKEY")
	if apiKey == "" {
		return "", errors.New("firebase api key not specified")
	}
	resp, err := postRequest(fmt.Sprintf(verifyCustomTokenURL, apiKey), req)
	if err != nil {
		return "", err
	}
	var respBody struct {
		IDToken string `json:"idToken"`
	}
	if err := json.Unmarshal(resp, &respBody); err != nil {
		return "", err
	}
	return respBody.IDToken, err
}

func postRequest(url string, req []byte) ([]byte, error) {
	resp, err := http.Post(url, "application/json", bytes.NewBuffer(req))
	if err != nil {
		return nil, err
	}

	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected http status code: %d", resp.StatusCode)
	}
	return ioutil.ReadAll(resp.Body)
}
