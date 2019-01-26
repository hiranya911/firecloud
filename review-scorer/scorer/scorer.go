package scorer

import (
	"context"
	"log"
	"time"

	firebase "firebase.google.com/go"
	"firebase.google.com/go/db"
)

// FirestoreEvent is the payload of a Firestore event.
type FirestoreEvent struct {
	OldValue   FirestoreValue `json:"oldValue"`
	Value      FirestoreValue `json:"value"`
	UpdateMask struct {
		FieldPaths []string `json:"fieldPaths"`
	} `json:"updateMask"`
}

// FirestoreValue holds Firestore fields.
type FirestoreValue struct {
	CreateTime time.Time `json:"createTime"`
	// Fields is the data for this value. The type depends on the format of your
	// database. Log an interface{} value and inspect the result to see a JSON
	// representation of your database fields.
	Fields     Review    `json:"fields"`
	Name       string    `json:"name"`
	UpdateTime time.Time `json:"updateTime"`
}

// Review represents the Firestore schema of a movie review.
type Review struct {
	Author struct {
		Value string `json:"stringValue"`
	} `json:"author"`
	Text struct {
		Value string `json:"stringValue"`
	} `json:"text"`
}

var client *db.Client

func init() {
	ctx := context.Background()

	conf := &firebase.Config{
		DatabaseURL: "https://solarflares-f4bee.firebaseio.com/",
	}
	app, err := firebase.NewApp(ctx, conf)
	if err != nil {
		log.Fatalf("firebase.NewApp: %v", err)
	}

	client, err = app.Database(ctx)
	if err != nil {
		log.Fatalf("app.Firestore: %v", err)
	}
}

// ScoreReview generates the scores for movie reviews and transactionally writes them to the
// Firebase Realtime Database.
func ScoreReview(ctx context.Context, e FirestoreEvent) error {
	review := e.Value.Fields
	reviweScore := score(review.Text.Value)

	ref := client.NewRef("scores").Child(review.Author.Value)
	updateTxn := func(node db.TransactionNode) (interface{}, error) {
		var currentScore int
		if err := node.Unmarshal(&currentScore); err != nil {
			return nil, err
		}
		return currentScore + reviweScore, nil
	}
	return ref.Transaction(ctx, updateTxn)
}

func score(text string) int {
	return len(text)
}
