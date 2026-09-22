import asyncio
import os
import sys
import json

sys.path.insert(0, r"c:\Users\qiwai")
from dotenv import load_dotenv
load_dotenv(r"c:\Users\qiwai\.env")

from vts_7L_test import PureAsyncFirestoreClient, DEFAULT_CHANNEL_ID

async def test():
    cred_json = os.getenv("FIREBASE_CRED_JSON")
    if not cred_json:
        print("FIREBASE_CRED_JSON not found in env")
        return
    cred = json.loads(cred_json)
    client = PureAsyncFirestoreClient(cred)
    try:
        user_doc = await client.collection('user_memory').document(DEFAULT_CHANNEL_ID).get()
        print(f'✅ user_memory ({DEFAULT_CHANNEL_ID}) exists:', user_doc.exists, 'data:', user_doc.to_dict())
        
        h_doc = await client.collection('channel_history').document(DEFAULT_CHANNEL_ID).get()
        print(f'✅ channel_history ({DEFAULT_CHANNEL_ID}) exists:', h_doc.exists, 'length:', len(h_doc.to_dict().get('history', [])) if h_doc.exists else 0)
        
        meta_doc = await client.collection('channel_meta').document(DEFAULT_CHANNEL_ID).get()
        print(f'✅ channel_meta ({DEFAULT_CHANNEL_ID}) exists:', meta_doc.exists, 'tags:', meta_doc.to_dict() if meta_doc.exists else None)

        tiktok_doc = await client.collection('channel_history').document('tiktok_live_stream').get()
        print('✅ tiktok_live_stream history exists:', tiktok_doc.exists, 'length:', len(tiktok_doc.to_dict().get('history', [])) if tiktok_doc.exists else 0)
    finally:
        session = await client.get_session()
        if not session.closed:
            await session.close()

if __name__ == "__main__":
    asyncio.run(test())
