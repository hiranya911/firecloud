import * as functions from 'firebase-functions';
import * as admin from 'firebase-admin';

admin.initializeApp();

const firestore = admin.firestore();
const settings = {timestampsInSnapshots: true};
firestore.settings(settings);

export const sendCryptoAlerts = functions.firestore.document('prices/{currency}')
    .onUpdate(async (change, context) => {
        const currencyId: string = context.params.currency;
        const data = change.after.data();
        const newPrice: number = data.value;
        console.log(`Price of ${currencyId} changed to USD ${newPrice}`);

        const tokens = await findTargetDevices(currencyId, newPrice);
        console.log(`Notifying ${tokens.length} devices`);

        const promises: Array<Promise<string>> = [];
        tokens.forEach((token) => {
            const result = admin.messaging().send({
                token,
                notification: {
                    title: 'Crypto Price Alert',
                    body: `${data.name} price changed to USD ${newPrice}.`,
                },
            });
            promises.push(result);
        });
        return await Promise.all(promises);
    });

async function findTargetDevices(currencyId: string, price: number): Promise<string[]> {
    const prefs = firestore.collection('prefs');
    const minQuery = prefs.where(`${currencyId}_min`, '>', price).get();
    const maxQuery = prefs.where(`${currencyId}_max`, '<', price).get();
    const tokens: string[] = [];
    (await minQuery).forEach((doc) => {
        tokens.push(doc.data().token);
    });
    (await maxQuery).forEach((doc) => {
        tokens.push(doc.data().token);
    });
    return tokens;
}
