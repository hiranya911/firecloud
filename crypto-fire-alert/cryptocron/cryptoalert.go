package cryptocron

import (
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"strings"
	"time"

	"cloud.google.com/go/firestore"
	firebase "firebase.google.com/go"
	"firebase.google.com/go/messaging"
	"google.golang.org/api/iterator"
)

// FirebaseClient is a helper for interacting with Firebase services.
type FirebaseClient struct {
	db  *firestore.Client
	fcm *messaging.Client
}

// Prices is a map of crypto currency prices.
type Prices map[string]float64

// NewFirebaseClient creates a new client using application default credentials.
func NewFirebaseClient(ctx context.Context) (*FirebaseClient, error) {
	app, err := firebase.NewApp(ctx, nil)
	if err != nil {
		return nil, err
	}
	db, err := app.Firestore(ctx)
	if err != nil {
		return nil, err
	}
	fcm, err := app.Messaging(ctx)
	if err != nil {
		return nil, err
	}
	return &FirebaseClient{
		db:  db,
		fcm: fcm,
	}, nil
}

// SavePrices saves the given crypto currency prices to the database.
func (client *FirebaseClient) SavePrices(ctx context.Context, prices Prices) error {
	collection := client.db.Collection("prices")
	batch := client.db.Batch()
	for curr, price := range prices {
		batch.Set(collection.Doc(curr), map[string]interface{}{"value": price}, firestore.MergeAll)
	}
	_, err := batch.Commit(ctx)
	return err
}

// SendNotifications notifies the given list of devices of the specified price change.
func (client *FirebaseClient) SendNotifications(
	ctx context.Context, curr string, price float64, devices []string) error {
	for _, device := range devices {
		msg := &messaging.Message{
			Notification: &messaging.Notification{
				Title: "Crypto Price Alert",
				Body:  fmt.Sprintf("%s price changed to %.2f USD", curr, price),
			},
			Token: device,
		}
		_, err := client.fcm.Send(ctx, msg)
		if err != nil {
			return err
		}
	}
	return nil
}

// FindDevices computes the list of devices that should be notified of the specified price change.
func (client *FirebaseClient) FindDevices(ctx context.Context, curr string, price float64) ([]string, error) {
	var devices []string
	findDevices := func(docs *firestore.DocumentIterator) error {
		for {
			snap, err := docs.Next()
			if err == iterator.Done {
				break
			}
			if err != nil {
				return err
			}
			devices = append(devices, snap.Data()["token"].(string))
		}
		return nil
	}
	docs := client.db.Collection("prefs").Where(curr+"_min", ">", price).Documents(ctx)
	if err := findDevices(docs); err != nil {
		return nil, err
	}
	docs = client.db.Collection("prefs").Where(curr+"_max", "<", price).Documents(ctx)
	if err := findDevices(docs); err != nil {
		return nil, err
	}
	return devices, nil
}

// OnlinePriceFinder finds latest crypto currency prices by consulting a remote web service.
type OnlinePriceFinder struct{}

// Prices returns a map of latest crypto currency prices.
func (pf *OnlinePriceFinder) Prices(ctx context.Context, currencies []string) (Prices, error) {
	var symbols []string
	for _, curr := range currencies {
		symbols = append(symbols, strings.ToUpper(curr))
	}
	const url = "https://min-api.cryptocompare.com/data/pricemulti?fsyms=%s&tsyms=USD&ts=%d"
	res, err := http.Get(fmt.Sprintf(url, strings.Join(symbols, ","), time.Now().Unix()))
	if err != nil {
		return nil, err
	}
	defer res.Body.Close()

	b, err := ioutil.ReadAll(res.Body)
	if err != nil {
		return nil, err
	}
	result := make(map[string]struct {
		USD float64 `json:"USD"`
	})
	if err := json.Unmarshal(b, &result); err != nil {
		return nil, err
	}

	prices := make(Prices)
	for k, v := range result {
		prices[strings.ToLower(k)] = v.USD
	}
	return prices, nil
}
