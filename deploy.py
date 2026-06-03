from pyngrok import ngrok
import subprocess
import os

ngrok.set_auth_token("3ESNGQs27rZN2TSXpur8x2MqZcR_5Du15DsvbnJpr483EDD1B")

public_url = ngrok.connect(8501)
print(f"\n✅ Your BIM Assistant is live at: {public_url}")
print("Share this link with anyone in the world.")
print("Keep this terminal running to keep the app alive.\n")

subprocess.run(["streamlit", "run", "app.py"])