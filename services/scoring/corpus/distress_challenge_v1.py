"""
DISTRESS ADVERSARIAL CHALLENGE SET V1
=====================================
Hard cases that a synthetic training set tends to get wrong:
negation, recovery, strong vocabulary with moderate meaning,
high distress with NO emotion words (functional collapse), short inputs.
Used only for evaluation. Never train on this file.
"""
import pandas as pd

OUTPUT_PATH = "training/data/distress_challenge_v1.csv"

CASES = [
    # text, label, category, language
    ("I'm not worried about the hearing at all.", 0, "negation", "english"),
    ("I don't feel stressed these days, honestly.", 0, "negation", "english"),
    ("Mujhe case ko lekar koi tension nahi hai.", 0, "negation", "hinglish"),
    ("I'm not scared of going to court anymore.", 0, "negation", "english"),
    ("Last month I couldn't sleep, but now I'm sleeping fine and back at work.", 0, "recovery", "english"),
    ("Pehle bahut darr lagta tha, ab main theek hoon aur kaam pe jaa raha hoon.", 0, "recovery", "hinglish"),
    ("The panic I had earlier has gone, I feel normal now.", 0, "recovery", "english"),
    ("The next hearing is on Tuesday at 11.", 0, "neutral_factual", "english"),
    ("Kal thane jaana hai kaagaz lene.", 0, "neutral_factual", "hinglish"),
    ("My lawyer said the judgement may take two more months.", 0, "neutral_factual", "english"),
    ("Sab badhiya hai, bas date confirm karni thi.", 0, "low_hinglish", "hinglish"),
    ("Ghar pe sab theek, kaam bhi chal raha hai.", 0, "low_hinglish", "hinglish"),
    ("I'm fine.", 0, "short", "english"),

    ("I'm a bit scared about the hearing but I'll manage.", 1, "moderate_strong_vocab", "english"),
    ("Thoda darr lagta hai par sambhal lunga.", 1, "moderate_strong_vocab", "hinglish"),
    ("The stress is there but I'm still getting through my days.", 1, "moderate_strong_vocab", "english"),
    ("I get anxious before calls, though it passes after a while.", 1, "moderate_strong_vocab", "english"),
    ("I've been sleeping less and I'm distracted at work, but I'm okay overall.", 1, "moderate_functional", "english"),
    ("Neend kam ho gayi hai aur kaam mein dhyan nahi lagta, par theek hoon.", 1, "moderate_functional", "hinglish"),
    ("Some nights are hard, but most days are fine.", 1, "moderate_functional", "english"),
    ("Hearing ke pehle ghabrahat hoti hai par baad mein theek ho jaata hoon.", 1, "moderate_hinglish", "hinglish"),
    ("Case ki wajah se thoda mood off rehta hai aajkal.", 1, "moderate_hinglish", "hinglish"),
    ("Work is fine and my family is supportive, but I keep worrying about the case at night and my sleep has suffered.", 1, "mixed_long", "english"),
    ("Thodi tension hai.", 1, "short", "hinglish"),

    ("I haven't left my room in a week and I stopped going to work.", 2, "high_no_emotion_words", "english"),
    ("Ek hafte se kamre se bahar nahi nikla, kaam pe jaana chhod diya.", 2, "high_no_emotion_words", "hinglish"),
    ("I haven't eaten in two days and I can't get out of bed.", 2, "high_no_emotion_words", "english"),
    ("I've stopped answering the phone and I don't talk to anyone anymore.", 2, "high_no_emotion_words", "english"),
    ("I can't do this anymore, I'm falling apart.", 2, "high_explicit", "english"),
    ("Mujhse ab nahi hoga, main bikhar raha hoon.", 2, "high_explicit", "hinglish"),
    ("The fear is so bad I can't breathe when I think about it.", 2, "high_explicit", "english"),
    ("I feel there is no point in living like this.", 2, "high_explicit", "english"),
    ("Raat ko darr ke maare saans nahi aati, lagta hai mar jaunga.", 2, "high_hinglish", "hinglish"),
    ("Bachon ko school bhejna band kar diya, itna darr hai.", 2, "high_hinglish", "hinglish"),
    ("I go to work every day, but as soon as I get home I break down crying and can't stop.", 2, "mixed_long", "english"),
    ("Bahut darr lag raha hai.", 2, "short", "hinglish"),
    ("Main theek nahi hoon, bilkul toot gaya hoon.", 2, "short", "hinglish"),
]

df = pd.DataFrame(CASES, columns=["text", "label", "category", "language"])
df.to_csv(OUTPUT_PATH, index=False)
print("Challenge cases:", len(df))
print(df["label"].value_counts().sort_index())
print("Saved:", OUTPUT_PATH)
