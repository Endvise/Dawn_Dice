import requests
import json

url = "https://gticuuzplbemivfturuz.supabase.co/rest/v1/users?select=*&limit=1"
headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd0aWN1dXpwbGJlbWl2ZnR1cnV6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDA2MDAxNSwiZXhwIjoyMDg1NjM2MDE1fQ.TKXlxD3jiwt8wFmW6NsTLqzGqG-W1HPGUxipM8AWbFU",
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd0aWN1dXpwbGJlbWl2ZnR1cnV6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDA2MDAxNSwiZXhwIjoyMDg1NjM2MDE1fQ.TKXlxD3jiwt8wFmW6NsTLqzGqG-W1HPGUxipM8AWbFU",
}

try:
    resp = requests.get(url, headers=headers)
    result = f"Status: {resp.status_code}\n"
    result += f"Response: {resp.text[:2000]}"
    with open("D:\\0099_Dawn_Dice\\schema_result.txt", "w", encoding="utf-8") as f:
        f.write(result)
except Exception as e:
    with open("D:\\0099_Dawn_Dice\\schema_result.txt", "w", encoding="utf-8") as f:
        f.write(f"Error: {str(e)}")
