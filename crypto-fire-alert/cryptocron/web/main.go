package main

import (
	"context"
	"fmt"
	"log"
	"math/big"
	"math/rand"
	"net/http"
	"os"

	"github.com/hiranya911/firecloud/crypto-fire-alert/cryptocron"
)

func main() {
	client, err := cryptocron.NewFirebaseClient(context.Background())
	if err != nil {
		log.Fatal(err)
	}
	http.Handle("/fetch", fetchUpdates(client))

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	log.Printf("Listening on port %s", port)
	log.Fatal(http.ListenAndServe(fmt.Sprintf(":%s", port), nil))
}

func fetchUpdates(client *cryptocron.FirebaseClient) appHandler {
	var pf priceFinder
	if os.Getenv("SIMULATE_MODE") == "1" {
		pf = &mockPriceFinder{
			min: 1000.0,
			max: 15000.0,
		}
	} else {
		pf = &cryptocron.OnlinePriceFinder{}
	}
	allCurrencies := []string{"btc", "eth"}
	sendNotifications := os.Getenv("SEND_NOTIFICATIONS") == "1"
	handler := func(w http.ResponseWriter, r *http.Request) error {
		prices, err := pf.Prices(r.Context(), allCurrencies)
		if err != nil {
			return err
		}
		if err := client.SavePrices(r.Context(), prices); err != nil {
			return nil
		}
		for curr, price := range prices {
			log.Printf("Price of %s = %.2f USD", curr, price)
			if !sendNotifications {
				continue
			}
			devices, err := client.FindDevices(r.Context(), curr, price)
			if err != nil {
				return err
			}
			if len(devices) > 0 {
				log.Printf("Notifying %d device(s) of %s price change", len(devices), curr)
				if err := client.SendNotifications(r.Context(), curr, price, devices); err != nil {
					return err
				}
			}
		}
		w.WriteHeader(200)
		w.Write([]byte("prices updated successfully"))
		return nil
	}
	if os.Getenv("CRON_ONLY") == "1" {
		return validateCronRequest(handler)
	}
	return handler
}

func validateCronRequest(handler appHandler) appHandler {
	return func(w http.ResponseWriter, r *http.Request) error {
		if r.Header.Get("X-Appengine-Cron") != "true" {
			w.WriteHeader(http.StatusNotFound)
			return nil
		}
		return handler(w, r)
	}
}

type priceFinder interface {
	Prices(context.Context, []string) (cryptocron.Prices, error)
}

type mockPriceFinder struct {
	min, max float64
}

func (pf *mockPriceFinder) Prices(ctx context.Context, currencies []string) (cryptocron.Prices, error) {
	coinPrice := make(map[string]float64)
	for _, curr := range currencies {
		price, _ := big.NewFloat(pf.min + rand.Float64()*(pf.max-pf.min)).SetPrec(8).Float64()
		coinPrice[curr] = price
	}
	return coinPrice, nil
}

type appHandler func(w http.ResponseWriter, r *http.Request) error

func (ah appHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if err := ah(w, r); err != nil {
		w.WriteHeader(500)
		w.Write([]byte(err.Error()))
		return
	}
}
