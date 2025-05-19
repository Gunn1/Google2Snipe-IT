# Google ChromeOS to Snipe-IT Sync

This script automates the process of syncing ChromeOS device data from the **Google Admin SDK** into your **Snipe-IT** asset inventory.

It fetches device data using a Google service account with domain-wide delegation and pushes it to Snipe-IT. Duplicate devices are automatically updated. All activity is logged and a progress bar shows sync status.

---

## 🔧 Features

* ✅ Authenticates using a **service account**
* ✅ Fetches **all ChromeOS devices** (paged)
* ✅ Parses and formats relevant fields (MAC, IP, model, enrollment date, etc.)
* ✅ Automatically creates **models and categories**
* ✅ Assigns the proper **fieldset with custom fields**
* ✅ Updates existing devices based on asset tag
* ✅ Handles **API rate limiting (429)** with retry logic
* ✅ Logs errors to `snipeit_errors.log`
* ✅ Displays a live **progress bar** with `tqdm`

---

## 📦 Requirements

* Python 3.8+
* [Snipe-IT](https://snipeitapp.com/) API access
* Google Workspace Admin access with service account + delegation
* `service_account.json` with delegated admin
* Installed Python packages:

  ```bash
  pip install google-api-python-client google-auth tqdm python-dotenv requests
  ```

---

## ⚒️ Setup

### 1. Clone the repo

```bash
git clone https://github.com/your-org/google-snipeit-sync.git
cd google-snipeit-sync
```

### 2. Add Environment Variables

Create a `.env` file:

```
API_TOKEN=your_snipeit_api_key
ENDPOINT_URL=https://your-snipeit-url/api/v1
```

### 3. Place Your Service Account Key

Save your Google service account credentials file as:

```
service_account.json
```

Ensure the account has domain-wide delegation and access to:

```
https://www.googleapis.com/auth/admin.directory.device.chromeos
```

---

## ▶️ Run the Script

```bash
python snipe-IT.py
```

Progress will display in the terminal. Errors are logged in:

```
snipeit_errors.log
```

---

## 🧠 Notes

* You must configure the correct **fieldset ID** for your device custom fields.
* MAC addresses are automatically normalized (`a81d166742f7` → `a8:1d:16:67:42:f7`).
* Asset tags and serial numbers are assumed to be the same.
* Devices not found in Snipe-IT will be created, otherwise updated.

---

## 📄 License

MIT License

---

## 🤝 Contributing

Feel free to open issues or PRs for improvements, new field support, or Snipe-IT enhancements.
