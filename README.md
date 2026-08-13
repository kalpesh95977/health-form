# Health Insurance Declaration Form — ICICI Lombard

Customer khud form bharta hai → SMS OTP se verify karta hai → declaration accept karta hai →
PDF automatically generate hoke aapke email par chala jata hai.

**Do languages mein available hai — customer ko jo bhi link suit kare wo bhej sakte ho:**
- English: `https://your-deployed-url.com/en`
- Gujarati: `https://your-deployed-url.com/gu`

(Form ke andar bhi top-right corner mein EN / ગુજ switch button hai, customer khud bhi badal sakta hai)

## Files

```
health-consent-form/
├── app/
│   ├── main.py              # FastAPI app + API routes
│   ├── otp_service.py       # SMS OTP (MSG91) — TEST MODE bhi hai
│   ├── pdf_generator.py     # Final declaration PDF banata hai
│   ├── email_service.py     # PDF ko email karta hai
│   ├── templates/form.html  # Customer-facing form (mobile-friendly)
│   └── generated_pdfs/      # Generated PDFs yahan save hote hain
├── requirements.txt
└── .env.example
```

## Step 1 — Local pe test karna (bina MSG91 ke bhi chalega)

```bash
cd health-consent-form
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd app
python main.py
```

Browser mein kholein: `http://localhost:8000`

**TEST MODE:** Agar `.env` mein `MSG91_AUTH_KEY` nahi dala, to OTP terminal/console
mein print hoga (SMS actually nahi jayega) — isse aap poora flow test kar sakte ho
bina MSG91 account ke.

Email bhi agar `.env` mein configure nahi hai, to PDF sirf `app/generated_pdfs/` folder
mein save ho jayega, email skip ho jayega (console mein message dikhega).

## Step 2 — MSG91 setup (real SMS OTP ke liye)

1. [msg91.com](https://msg91.com) pe account banayein
2. **DLT Registration** karein (India mein SMS bhejne ke liye mandatory) — Entity ID
   aur OTP template register karna hoga (MSG91 ki site pe guided process hai, usually
   1-2 din lagte hain approval mein)
3. MSG91 dashboard se **Auth Key** aur **OTP Template ID** copy karein
4. `.env` file mein dalein:
   ```
   MSG91_AUTH_KEY=aapki-auth-key
   MSG91_TEMPLATE_ID=aapki-template-id
   ```

## Step 3 — Email setup (Gmail ke liye)

1. Google Account → Security → 2-Step Verification on karein
2. "App Passwords" section mein jaake ek naya app password generate karein
3. `.env` mein dalein:
   ```
   SMTP_USER=aapka-email@gmail.com
   SMTP_PASSWORD=wahi-16-digit-app-password
   RECEIVER_EMAIL=jaha-PDF-chahiye@gmail.com
   ```

## Step 4 — Deploy karna (customer ko link bhejne ke liye)

Free/cheap options jo aasan hain:
- **Railway.app** ya **Render.com** — GitHub repo connect karke ek-click deploy
- VIDHI app (`vidhi-ai-navy.vercel.app`) jaise hi aap already Vercel use kar rahe ho,
  wahan bhi deploy ho sakta hai (thoda config badalna padega kyunki ye Python
  backend hai, Vercel pe serverless function ki tarah)

Deploy hone ke baad aapko ek link milega jaise `https://health-form.up.railway.app` —
wahi link customer ko WhatsApp/SMS se bhej sakte ho.

## Form mein kya-kya hai

1. **Proposer Details** — Naam, DOB, mobile, email, address, PAN, occupation
2. **Insured Members** — Multiple members add kar sakte hain (self/spouse/kids/parents)
   — har ek ke liye height/weight, pre-existing disease, hospitalization history,
   tobacco/alcohol use, family medical history
3. **Policy Details** — Sum insured, plan type, existing insurance details
4. **Nominee Details**
5. **OTP Verify + Declaration** — Mobile OTP verify + health declaration text +
   "I Agree" checkbox

Submit hone par PDF mein sab kuch aata hai + OTP verification proof (mobile number,
timestamp, submission ID) — legal record ke liye.

## Aage kya customize kar sakte ho

- `pdf_generator.py` mein declaration text ko apne legal/compliance team se
  verify karwa lena (ye ek starting draft hai, insurer-specific wording chahiye ho sakti hai)
- `otp_service.py` mein MSG91 ki jagah Fast2SMS ya kisi aur provider ka switch aasan hai
- Multiple submissions ka record rakhne ke liye (abhi sirf email jata hai) — ek
  simple SQLite/Firebase table add ki ja sakti hai (jaise AutoFlow dashboard mein hai)
- Existing `whatsapp-console` se link karke WhatsApp se bhi form-link auto-bhejne
  ka option add ho sakta hai
