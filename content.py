"""Static content served by the API: safety recommendations and clearly-labelled DEMONSTRATION sample inputs."""

RECOMMENDATIONS = {
    "helpline": {"number": "1930", "portal": "https://cybercrime.gov.in/",
                 "text": "National Cyber Crime Helpline 1930 and cybercrime.gov.in (Indian Cyber Crime Coordination Centre, "
                         "Ministry of Home Affairs). Digital Kavach AI is not an official service."},
    "sections": [
        {"id": "otp", "title": "OTPs, PINs and passwords", "items": [
            "Never share an OTP, UPI PIN, card PIN, CVV or password with anyone. Banks never ask for them.",
            "You never need to enter a PIN to receive money. If a request asks for your PIN, it is taking money out.",
            "Turn on two-step login for email and social accounts, and use a different password for each."]},
        {"id": "links", "title": "Links and messages", "items": [
            "Do not tap links in unexpected SMS, WhatsApp or email messages. Type the organisation's address yourself.",
            "Look closely at the domain: 'sbi-kyc-update.xyz' is not 'sbi.co.in'. Shortened links hide the destination.",
            "Do not install apps (APK files) or screen-sharing tools such as AnyDesk because a caller asks you to."]},
        {"id": "payments", "title": "Payments and prizes", "items": [
            "You cannot win a lottery or contest you never entered. Real prizes do not ask for a fee.",
            "Do not pay 'processing', 'customs' or 'registration' fees to receive money, a job or a parcel.",
            "'Digital arrest' does not exist. Police and courts do not demand money or video-call supervision."]},
        {"id": "profiles", "title": "Fake profiles and impersonation", "items": [
            "Check account age, followers, and whether the organisation's official website links to the profile.",
            "Be careful when a friend 'has a new account' or asks for money - phone them on a number you already have.",
            "Use the platform's Report option and keep screenshots and links as evidence."]},
        {"id": "images", "title": "Images and videos", "items": [
            "Search for the image with a reverse-image-search tool to see where else it appears.",
            "Do not forward an image or video if you are unsure; sharing a fake spreads the harm.",
            "If an image of you was edited or shared without consent, save the link, report it and consider a complaint at cybercrime.gov.in."]},
        {"id": "identity", "title": "Digital identity safety", "items": [
            "Never type your Aadhaar number, selfie or documents into a website or app you cannot verify.",
            "Keep different accounts for different roles (personal, shop, community) and use strong, separate passwords.",
            "Prefer sign-ins that share only what a service needs. Legitimate multiple accounts are normal."]},
        {"id": "defrauded", "title": "If you have been defrauded", "items": [
            "Call 1930 immediately. Quick reporting can help freeze transactions.",
            "File a complaint at cybercrime.gov.in and inform your bank to block cards and UPI.",
            "Change passwords, keep screenshots, and do not delete the chat."]},
    ],
    "quick_check": ["Who is asking, and did I expect this?", "Are they rushing me or asking for money, an OTP or a document?",
                    "Can I confirm through a number or website I already trust?"],
}

SAMPLES = {
    "notice": "Sample inputs are demonstration data written by the team. They are not real people or messages.",
    "scam": [
        {"label": "Bank KYC phishing", "text": "SBI ALERT: Dear customer, your KYC has expired and your account will be blocked today. "
                                               "Share the OTP sent to you and update immediately at http://sbi-kyc-update.xyz"},
        {"label": "Prize and fee", "text": "Congratulations! You have won Rs 25,00,000 in the KBC lucky draw. To claim your prize pay a "
                                           "processing fee of Rs 4999 and send your Aadhaar and bank details to this number."},
        {"label": "Genuine-style alert", "text": "HDFC Bank: Rs 2,500.00 debited from a/c XX4821 on 28-Oct via UPI. "
                                                  "If not you, call the number on the back of your card. Never share your OTP with anyone."},
        {"label": "Digital arrest threat", "text": "This is Mumbai Cyber Cell. A parcel in your name contains narcotics. A case has been registered "
                                                   "against you. Stay on the video call and install AnyDesk to avoid arrest."},
    ],
    "profile": [
        {"label": "Suspicious sample profile", "username": "sbi_official_help88391", "url": "http://instagrarn.com/sbi_support_desk",
         "description": "Official SBI customer care. Guaranteed returns on investment, DM on WhatsApp 9876543210. My old account was hacked, please follow my new account. Urgent offer, act now!",
         "notes": "This account messaged me and asked me for money to release my refund.", "account_age_days": 3, "followers": 12, "following": 4800},
        {"label": "Ordinary sample profile", "username": "meera.kitchen", "url": "https://www.instagram.com/meera.kitchen",
         "description": "Home cook from Guntur. Weekend recipes and food photos.", "notes": "", "account_age_days": 1460, "followers": 820, "following": 310},
        {"label": "Too little information", "username": "rahul_k", "url": "", "description": "", "notes": "", "account_age_days": None, "followers": None, "following": None},
    ],
    "accounts": [
        {"category": "personal", "platform": "Instagram", "handle": "demo.asha.personal"},
        {"category": "business", "platform": "Facebook", "handle": "demo.asha.tailoring"},
        {"category": "community", "platform": "WhatsApp Business", "handle": "demo.village.notice"},
        {"category": "religious", "platform": "YouTube", "handle": "demo.temple.committee"},
        {"category": "organisation", "platform": "LinkedIn", "handle": "demo.ngo.helpdesk"},
    ],
    "report": {"label": "Fill a sample impersonation report", "username": "asha.k_official2", "platform": "Instagram",
               "profile_url": "https://www.instagram.com/asha.k_official2", "report_type": "Fake profile using my identity",
               "description": "A new account uses my photo and name and asks my relatives for urgent money transfers.",
               "evidence_description": "Screenshots of the chats are saved on my phone (not uploaded here)."},
}
